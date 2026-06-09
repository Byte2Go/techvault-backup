### The Problem This Architecture Solves
As a microservice grows, business rules leak into controllers, database code leaks into business logic, and frontend requirements break backend models. When everything is tangled together, changing one thing breaks everything else.

Clean Architecture solves this by enforcing strict boundaries: <mark style="background: #BBFABBA6;">each layer has exactly one job</mark>, knows only what it needs to know, and never reaches across into another layer's territory.

---
## Foundation — The Four Data Shapes (Entities vs. Messages)
Data takes four completely different shapes as it moves through your system. Each shape exists for a different owner, lives in its own layer, and serves a unique master.

**Two categories first:** <mark style="background: #FFB86CA6;">An **Entity** has a unique identity, a lifecycle, and state that changes over time </mark>— a specific `Order`, a specific `Customer`. <mark style="background: #ADCCFFA6;">A **Message** is the opposite: no identity, immutable</mark>, <mark style="background: #FFB8EBA6;">and it vanishes the moment its use case finishes executing.</mark>

|Shape|Category|Speaks|Lives in|
|---|---|---|---|
|**DTO** (UI Entity)|Entity + POJO|JSON — shaped for frontend screens and external callers|`api/`|
|**Command / Query** (Application Message)|Message + POJO|Pure intent — `PlaceOrderCommand`, `GetOrderByIdQuery`. The controller strips all HTTP metadata and copies only the raw fields the use case needs into this immutable `record`|`application/command/` or `application/query/`|
|**Domain Object** (Core Entity)|Entity + POJO|Pure business logic — plain Java `if` statements enforcing company rules. Zero database code, zero framework annotations, zero web code|`domain/`|
|**JPA Entity** (DB Entity)|Entity + Non-POJO|SQL tables and columns — `@Entity`, `@Table` annotations let Hibernate map fields directly to physical storage rows|`infrastructure/`|

No single object can serve all four masters. A database row structure is terrible for rendering a frontend form. An HTTP DTO is terrible for enforcing business state rules. A domain model shouldn't know that network ports or database indexes exist.

---
## App Structure Layer 1: The API Package (The Front Gate)

```
com.company.orderservice/
└── api/
    ├── OrderController.java
    └── dto/
        ├── PlaceOrderRequest.java   ← Inbound DTO
        └── OrderResponse.java       ← Outbound DTO
```

The `api/` package has one job: <mark style="background: #ADCCFFA6;">act as the inbound adapter.</mark> <mark style="background: #D2B3FFA6;">It handles the communication protocol, translates data formats,</mark> and then steps aside. It contains **zero business logic**.

When a request arrives at `OrderController`, four things happen in sequence:
**1. Protocol termination** — it declares what protocol it speaks: `"I listen on POST /api/v1/orders over HTTP/REST."`
**2. Deserialization and syntactic validation** — it converts the raw JSON string from the browser into your Inbound DTO (`PlaceOrderRequest`), automatically triggering `@NotBlank` and `@Email` checks. These checks ask: _Is the input shaped correctly? Is the email a valid format?_ <mark style="background: #FF5582A6;">Not: _Does this customer have enough credit?_ That's a business question — it belongs elsewhere.</mark>
**3. Delegation** — it <mark style="background: #BBFABBA6;">maps the DTO into a Command object </mark>and <mark style="background: #FFB86CA6;">hands it to the Application layer.</mark> The controller never makes a business decision.
**4. Serialization** — it takes whatever the Application layer returns and <mark style="background: #BBFABBA6;">wraps it into an Outbound DTO</mark> (`OrderResponse`), serialized back to JSON for the browser.

```
Browser sends raw JSON string
         │
         ▼
┌─────────────────────────────┐
│  api/ BOUNDARY              │
│  PlaceOrderRequest (DTO)    │  ← maps + validates JSON
│           │                 │
│           ▼ (passes inward) │
│           ▼ (receives back) │
│  OrderResponse (DTO)        │  ← prepares response for UI
└─────────────────────────────┘
         │
         ▼
Browser receives raw JSON string
```

**Why this boundary matters:** If the frontend team redesigns their screens and needs a completely different JSON structure, you only touch the DTOs in `api/`. Your business logic and database code never know it happened.

---
## The Command and Query: Bridge Between API and Application
When an inbound controller or listener finishes processing a network request, it does not pass its **transport DTO** directly into the core engine. Instead, it maps the data into a dedicated, <mark style="background: #FFB86CA6;">transport-agnostic application message</mark>: <mark style="background: #ADCCFFA6;">a **Command** or a **Query**. </mark>Both are strictly immutable Java objects (typically Java `records`), where **Commands are used to alter system state** and **Queries are used to read data**.

This application message acts as the <mark style="background: #FFF3A3A6;">ultimate decoupling buffer between the  outside infrastructure and your stable inner use cases</mark>.

#### Why not just pass the DTO straight through?
Six months from now, an instruction might arrive from three completely different network sources—an HTTP REST Controller, a Kafka Event Listener, or a gRPC Server Handler.

If your use case method signature accepts a `PlaceOrderRequest` (an HTTP Web DTO), your application layer will instantly break the moment a Kafka message broker attempts to trigger that same business feature using a different payload format.

```
[ HTTP REST Controller  ] ── maps JSON  ──┐
                                          ├──► [ PlaceOrderCommand / Query ]
[ Kafka Message Listener] ── maps Avro  ──┤          ──► [ UseCase Service ]
                                          │
[ gRPC Server Handler   ] ── maps Proto ──┘
```

<mark style="background: #BBFABBA6;">The Application use case doesn't know or care where the instruction originated on the network wire. All it expects is a valid, well-formed, immutable data container.</mark> This keeps your core business logic permanently independent of transport protocols and third-party API requirements.

---
## App Structure Layer 2: The Application Package (The Orchestrator)

```
└── application/
    ├── PlaceOrderUseCase.java
    └── command/
        └── PlaceOrderCommand.java
```

The Application layer does not make business rules and does not write database queries. <mark style="background: #FFB86CA6;">It **orchestrates** — it coordinates the sequence of steps needed to fulfill one use case</mark>, like a manager who delegates to experts.

The pattern for every use case method:
1. Receive the Command
2. Load the required domain objects <mark style="background: #FFB8EBA6;">from storage</mark>
3. Hand those objects <mark style="background: #FFB8EBA6;">to the Domain layer to make a business decision</mark>
4. Save the result <mark style="background: #FFB8EBA6;">back to storage</mark>
5. Publish any events

```java
@Service
@Transactional
public class PlaceOrderUseCase {
    private final OrderRepository orderRepository; // a domain interface, not JPA

    public void execute(PlaceOrderCommand command) {
        Order order = Order.createNew(command.customerId(), command.items()); // domain decides
        orderRepository.save(order); // infrastructure handles persistence
    }
}
```

**Three strict rules for this layer:**
- **No infrastructure code** — no raw SQL, no Kafka driver, no HTTP client. <mark style="background: #FFB86CA6;">It speaks to the outside world</mark> <mark style="background: #FFF3A3A6;">only through abstract interfaces defined in the Domain layer</mark>.
- **No business logic** — no `if/else` that calculates business outcomes. Wrong: `if (order.getTotal() > 100) { applyDiscount(); }`. Right: `order.applyApplicableDiscounts(pricingService)`. The domain object makes that decision.
- **Transaction boundary lives here** — `@Transactional` <mark style="background: #BBFABBA6;">belongs on the use case method</mark>. <mark style="background: #ADCCFFA6;">If the domain logic succeeds but the database save fails, this layer triggers the rollback.</mark>

---
## App Structure Layer 3: The Domain Package (The Business Brain)

```
└── domain/
    ├── model/
    │   ├── Order.java
    │   └── Money.java
    └── repository/
        └── OrderRepository.java
```

<mark style="background: #BBFABBA6;">This is the heart of your microservice</mark>. It contains your company's business rules as plain Java `if` statements — <mark style="background: #ADCCFFA6;">no database code, no Spring annotations, no framework of any kind.</mark>
### Order.java — The Rule Enforcer

```java
public class Order {
    private String status; // "DRAFT", "SHIPPED", "CANCELLED"
    private List<String> items = new ArrayList<>();

    public void cancelOrder() {
        if (this.status.equals("SHIPPED")) {
            throw new IllegalStateException("Cannot cancel an order that has already shipped.");
        }
        this.status = "CANCELLED";
    }

    public void addItem(String itemName) {
        if (this.status.equals("CANCELLED")) {
            throw new IllegalStateException("Cannot add items to a cancelled order.");
        }
        this.items.add(itemName);
    }
}
```

When a business analyst says _"you can no longer cancel a shipped order,"_ you know exactly where that rule lives and exactly which line to change. It's just a Java `if` statement in a plain class.

### Money.java — The Smart Value Type
Using a raw `BigDecimal` for money creates a silent, catastrophic bug: your code will happily add 100 USD to 50 JPY and return 150 with no error. The number is mathematically correct; the currency is completely broken.

```java
public record Money(BigDecimal amount, String currency) {
    public Money plus(Money other) {
        if (!this.currency.equals(other.currency)) {
            throw new IllegalArgumentException(
                "Cannot add " + this.currency + " to " + other.currency);
        }
        return new Money(this.amount.add(other.amount), this.currency);
    }
}
```

By making `Money` a dedicated type, you permanently protect the entire codebase from currency mixing. Anywhere money is used, the type enforces the rule automatically.

### OrderRepository.java — The Contract (Not the Implementation)
<mark style="background: #ABF7F7A6;">The Domain needs to load and save orders</mark>, but it is not allowed to know that Postgres exists. <mark style="background: #BBFABBA6;">So it writes a contract — a Java interface — and tells the outer layers</mark>: _"I need someone to provide these two capabilities. I don't care how."_

```java
public interface OrderRepository {
    Order getOrderById(String id);
    void saveOrderToStorage(Order order);
}
```

<mark style="background: #ABF7F7A6;">The Infrastructure layer later looks at this interface and implements it using Spring Data JPA and a real Postgres connection.</mark> The Domain never knows the difference. This is the mechanism that makes your business logic swappable across any database technology.

---
## App Structure Layer 4: The Infrastructure Package (The Physical Wiring)

```
└── infrastructure/
    ├── persistence/
    │   ├── OrderJpaEntity.java
    │   └── SpringDataOrderRepository.java
    └── messaging/
        ├── KafkaOrderEventPublisher.java
        ├── KafkaOrderEventConsumer.java
        ├── RabbitMqNotificationSender.java
        └── RabbitMqNotificationConsumer.java
```

<mark style="background: #FFB86CA6;">This is the only layer allowed to use heavy framework annotations.</mark> <mark style="background: #ADCCFFA6;">It knows everything about the outside world: SQL schemas, Kafka topics, RabbitMQ queues, and connection strings.</mark> Its job is to implement the contracts the Domain defined.

### Persistence: Postgres / Spring Data JPA
`OrderJpaEntity` maps your physical SQL table rows. It is a completely separate object from `Order.java` in the domain — deliberately, because<mark style="background: #D2B3FFA6;"> a database row structure should never contaminate your business model</mark>.

```java
@Entity
@Table(name = "orders")
public class OrderJpaEntity {
    @Id
    private String id;

    @Column(name = "customer_id", nullable = false)
    private String customerId;

    @Column(name = "total_amount", nullable = false)
    private BigDecimal totalAmount;

    @Column(name = "status", nullable = false)
    private String status;
    // getters and setters
}
```

<mark style="background: #FFB86CA6;">`SpringDataOrderRepository` implements the `OrderRepository` interface from the Domain using Spring Data JPA </mark>— giving you `.save()`, `.findById()`, and `.delete()` without writing a single SQL query:

```java
@Repository
public interface SpringDataOrderRepository extends JpaRepository<OrderJpaEntity, String> {
    // Spring generates all SQL at runtime
}
```

### Messaging Outbound: Kafka and RabbitMQ
**Kafka** is used for broadcasting events to the world — high-throughput, log-based streaming. Other microservices subscribe and react asynchronously.

```java
@Component
public class KafkaOrderEventPublisher {
    private final KafkaTemplate<String, Object> kafkaTemplate;

    public void sendOrderCreatedEvent(String orderId, String status) {
        kafkaTemplate.send("order-events-topic", orderId, new OrderEventPayload(orderId, status));
    }
}
```

**RabbitMQ** is used for direct, targeted work queue tasks — reliable point-to-point delivery to a specific worker (e.g., an email notification worker).

```java
@Component
public class RabbitMqNotificationSender {
    private final RabbitTemplate rabbitTemplate;

    public void sendTaskToQueue(String customerId, String message) {
        rabbitTemplate.convertAndSend(NOTIFICATION_QUEUE, buildPayload(customerId, message));
    }
}
```

### Messaging Inbound: Consumers
The infrastructure layer is a two-way street. It also handles messages arriving _into_ your microservice. <mark style="background: #FFB86CA6;">The listener class lives here because it handles the raw broker connection — its job is to unwrap the transport packaging and hand a clean Command down to the Application layer</mark>.

```java
@Component
public class KafkaOrderEventConsumer {
    @KafkaListener(topics = "payment-events-topic", groupId = "order-service-group")
    public void consumePaymentEvent(String rawJsonPayload) {
        // Parse payload → build Command → call use case
        // processOrderPaymentUseCase.execute(parsedCommand);
    }
}

@Component
public class RabbitMqNotificationConsumer {
    @RabbitListener(queues = RabbitMQConfig.NOTIFICATION_QUEUE)
    public void consumeTask(String rawMessage) {
        // Parse payload → call use case
        // sendEmailUseCase.execute(rawMessage);
    }
}
```

---

## The Complete Data Flow
No matter which door a request enters through, the pattern is always identical:
```
[ HTTP request   ]  ──► api/ controller
[ Kafka event    ]  ──► infrastructure/messaging/consumer } All map to a Command
[ RabbitMQ task  ]  ──► infrastructure/messaging/consumer  }
                                   │
                                   ▼
                      application/ use case (orchestrates)
                                   │
                                   ▼
                      domain/ model (applies business rules)
                                   │
                                   ▼
                      infrastructure/ persistence (saves to DB)
                      infrastructure/ messaging (publishes events)
```

---

## Layer Responsibility Summary

| Layer          | Package           | Job                                | What it knows                     |
| -------------- | ----------------- | ---------------------------------- | --------------------------------- |
| API            | `api/`            | Translate HTTP ↔ Commands          | HTTP, JSON, DTOs                  |
| Application    | `application/`    | Orchestrate one use case           | Commands, Domain interfaces       |
| Domain         | `domain/`         | Enforce business rules             | Pure Java only                    |
| Infrastructure | `infrastructure/` | Implement all external connections | Postgres, Kafka, RabbitMQ, Spring |

The architecture has one governing principle: **dependencies only point inward.** <mark style="background: #FFB86CA6;">Infrastructure knows about Domain.</mark> <mark style="background: #FFB8EBA6;">Domain knows nothing about Infrastructure</mark>. If you swap Postgres for MongoDB tomorrow, you rewrite one class in `infrastructure/persistence/` — nothing in `domain/` or `application/` changes.