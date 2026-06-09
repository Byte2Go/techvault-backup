### Layer 1 — The API Package
```
com.company.orderservice/
└── api/
    ├── OrderController.java        ← Network protocol termination
    └── dto/
        ├── PlaceOrderRequest.java  ← Inbound DTO
        └── OrderResponse.java      ← Outbound DTO
```

The `api/` package is an **Inbound Adapter**. Its <mark style="background: #ABF7F7A6;">only job is to speak network protocol (HTTP/REST, gRPC, GraphQL), translate the incoming format into a clean application message</mark>, and enforce syntax validation. It has zero tolerance for business rules or database access.

---
#### The DTO (`api/dto/`)
**What to avoid:**
```java
import jakarta.persistence.Entity; // VIOLATION

@Entity  // A DTO should NEVER be a database entity
public class PlaceOrderRequest {
    private String customerId;
    private List<String> items;
}
```
When a DTO doubles as a database row mapper, any database schema migration instantly breaks your external API contract — crashing every frontend and mobile app consuming your service.

**The correct approach:**
```java
package com.company.orderservice.api.dto;

import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import java.util.List;

public record PlaceOrderRequest(
    @NotNull(message = "Customer ID is required")
    String customerId,

    @NotEmpty(message = "Order must contain at least one item")
    List<String> items,

    String promoCode
) {}
```

A pure POJO `record`. The `jakarta.validation` annotations (`@NotNull`, `@NotEmpty`) are standard Java specification metadata — not framework code — so they don't couple this object to any external infrastructure. They handle **syntactic validation** right at the network perimeter: _"Is the data present and correctly shaped?"_ — before any expensive application logic is touched.

---
#### The Controller (`api/OrderController.java`)

**What to avoid:**
```java
@RestController
public class OrderController {
    private final JpaOrderRepository repo; // VIOLATION: infrastructure leak

    @PostMapping
    @Transactional  // VIOLATION: wrong layer
    public ResponseEntity<?> create(@RequestBody PlaceOrderRequest request) {
        if (request.items().isEmpty()) { // VIOLATION: business logic in controller
            return ResponseEntity.badRequest().body("No items");
        }
        repo.save(...); // VIOLATION: direct DB write
    }
}
```

<mark style="background: #FF5582A6;">**Two specific problems here:**</mark>
`@Transactional` on a controller keeps a physical database connection open while the controller is still doing slow work — serializing a response, waiting on network I/O. Under any meaningful traffic, this exhausts your database connection pool and crashes the system.

<mark style="background: #FFB8EBA6;">Direct infrastructure access and business logic in the controller means that when orders start arriving from Kafka instead of HTTP</mark>, <mark style="background: #FF5582A6;">you have to duplicate all of this code inside the consumer.</mark> The logic is stuck to the transport layer and can never be reused.

**The correct approach:**
```java
package com.company.orderservice.api;

import com.company.orderservice.api.dto.PlaceOrderRequest;
import com.company.orderservice.api.dto.OrderResponse;
import com.company.orderservice.application.command.PlaceOrderCommand;
import com.company.orderservice.application.service.PlaceOrderUseCase;
import jakarta.validation.Valid;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/orders")
public class OrderController {

    private final PlaceOrderUseCase placeOrderUseCase; // depends on application layer only

    public OrderController(PlaceOrderUseCase placeOrderUseCase) {
        this.placeOrderUseCase = placeOrderUseCase;
    }

    @PostMapping
    public ResponseEntity<OrderResponse> placeOrder(@Valid @RequestBody PlaceOrderRequest request) {

        // 1. Strip HTTP metadata — map to a protocol-agnostic Command
        PlaceOrderCommand command = new PlaceOrderCommand(
            request.customerId(),
            request.items(),
            request.promoCode()
        );

        // 2. Delegate inward — the controller makes zero business decisions
        String orderId = placeOrderUseCase.execute(command);

        // 3. Serialize the result back into a presentation DTO
        return ResponseEntity.ok(new OrderResponse(orderId));
    }
}
```

The controller is completely thin. If the frontend redesigns its JSON format tomorrow, you change the DTO and this controller. The business logic behind it remains untouched.

---
#### Annotation Reference
- **`@RestController`** — tells <mark style="background: #ABF7F7A6;">Spring to route HTTP requests into this class and automatically serialize return values to JSON</mark>. Never use this outside the `api/` package.
- **`@Valid`** — placed on the inbound parameter. Tells Spring's validation engine to run the syntactic constraints (`@NotNull`, `@NotEmpty`) declared on the DTO **before** any method logic executes. If validation fails, the request is rejected at the gate with a `400 Bad Request` — no use case is invoked, no database is touched.

---
### Layer 2 — The Application Package

```
com.company.orderservice/
└── application/
    ├── command/
    │   └── PlaceOrderCommand.java   ← Immutable inbound message
    ├── query/
    │   └── GetOrderByIdQuery.java   ← Immutable read request
    └── service/
        └── PlaceOrderUseCase.java   ← Orchestration only
```

<mark style="background: #ADCCFFA6;">The `application/` package is the **Orchestrator**.</mark> <mark style="background: #D2B3FFA6;">It receives a Command or Query, coordinates the sequence of steps to fulfill it, and delegates every real decision to the domain.</mark> <mark style="background: #FFB8EBA6;">It contains zero business rules and zero infrastructure code</mark> — <mark style="background: #BBFABBA6;">it only tells other layers what to do and in what order.</mark>

---
#### The Command (`application/command/`
**What to avoid:**

```java
public class PlaceOrderCommand {
    public String customerId;   // VIOLATION: mutable public fields
    public List<String> items;

    public void setCustomerId(String id) { // VIOLATION: mutable after creation
        this.customerId = id;
    }
}
```

<mark style="background: #FFB8EBA6;">A Command that can be mutated after creation is dangerous.</mark> As it passes through multiple layers, <mark style="background: #FF5582A6;">any layer could quietly alter its values</mark> — making the system's behaviour unpredictable and untraceable.

**The correct approach:**
```java
package com.company.orderservice.application.command;

import java.util.List;

public record PlaceOrderCommand(
    String customerId,
    List<String> items,
    String promoCode
) {}
```

<mark style="background: #ABF7F7A6;">A Java `record` is immutable by construction. </mark> <mark style="background: #BBFABBA6;">Once the controller creates it, no layer can modify its values.</mark> It carries only the raw fields the use case needs — no HTTP headers, no request metadata, <mark style="background: #FFF3A3A6;">no session details. Pure intent.</mark>

---
#### The Use Case (`application/service/`)
**What to avoid:**
```java
@Service
public class PlaceOrderUseCase {
    private final JpaOrderRepository repo; // VIOLATION: infrastructure leak

    @Transactional
    public String execute(PlaceOrderCommand command) {

        // VIOLATION: business rule leaking into orchestration layer
        if (command.items().size() > 50) {
            throw new IllegalArgumentException("Too many items");
        }

        // VIOLATION: raw SQL / JPA logic in the application layer
        OrderJpaEntity entity = new OrderJpaEntity();
        entity.setCustomerId(command.customerId());
        repo.save(entity);

        return entity.getId();
    }
}
```

**Three distinct violations here.**

- Depending directly on `JpaOrderRepository` <mark style="background: #FFB8EBA6;">couples the orchestration layer to Hibernate.</mark> If you switch from Postgres to MongoDB, you are forced to rewrite your use case.
- Business rules in the application layer — like the 50-item limit — are invisible to the domain. When that rule changes, developers will search for it in the wrong place, miss it, and introduce bugs.
- <mark style="background: #FFB8EBA6;">Building JPA entities directly inside the use case means the application layer now knows about your database schema.</mark> A column rename in your SQL table forces changes in two separate layers simultaneously.

**The correct approach:**
```java
package com.company.orderservice.application.service;

import com.company.orderservice.application.command.PlaceOrderCommand;
import com.company.orderservice.domain.model.Order;
import com.company.orderservice.domain.repository.OrderRepository; // domain interface, not JPA
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@Transactional
public class PlaceOrderUseCase {

    private final OrderRepository orderRepository; // depends on domain contract, not implementation

    public PlaceOrderUseCase(OrderRepository orderRepository) {
        this.orderRepository = orderRepository;
    }

    public String execute(PlaceOrderCommand command) {

        // 1. DELEGATE to domain — domain object makes every business decision
        Order order = Order.createNew(command.customerId(), command.items());

        // 2. PERSIST via the domain interface — use case never touches JPA directly
        orderRepository.save(order);

        // 3. RETURN a primitive result — not a domain object, not a JPA entity
        return order.getOrderId();
    }
}
```

The use case reads as a plain English description of steps. It makes no decisions. It simply coordinates: create the object, save it, return the result.

---
#### Annotation Reference
**`@Service`** — marks this class as <mark style="background: #FFB86CA6;">**an application-layer component** for Spring's dependency injection.</mark> Functionally equivalent to `@Component` but signals architectural intent: this class orchestrates, it doesn't serve HTTP and it doesn't touch databases directly.

**`@Transactional`** — <mark style="background: #D2B3FFA6;">this is the correct layer for transaction boundaries. It wraps the entire use case method in a single atomic database operation</mark>. If the domain logic succeeds but the `orderRepository.save()` fails, the transaction rolls back completely — no partial state is ever written to the database. Placing it here, rather than on a controller or a repository, guarantees that the rollback boundary matches exactly one complete business action.

---
#### The Three Strict Rules for This Layer
**No infrastructure code** — never import `JpaRepository`, Kafka drivers, HTTP clients, or AWS SDKs. The use case speaks to the outside world <mark style="background: #FFB86CA6;">only through abstract interfaces defined in the domain layer.</mark>

**No business rules** — never write `if/else` logic that calculates a business outcome. If a condition relates to company policy, it belongs in the domain object. The use case only sequences steps.

**One use case per class** — `PlaceOrderUseCase` handles placing orders. `CancelOrderUseCase` handles cancellations. Merging multiple use cases into a single `OrderService` god-class is how orchestration layers rot.

---
### Layer 3 — The Domain Package

```
com.company.orderservice/
└── domain/
    ├── model/
    │   ├── Order.java              ← Aggregate root (rule enforcer)
    │   └── Money.java              ← Value object (smart data type)
    ├── repository/
    │   └── OrderRepository.java  ← Outbound port (contract, not implementation)
    └── exception/
        └── OrderDomainException.java
```

The `domain/` package is the **Business Brain**. <mark style="background: #FFB86CA6;">It contains your company's rules as plain Java — nothing else. </mark> <mark style="background: #ABF7F7A6;">No Spring annotations, no database drivers, no HTTP code</mark>. If you deleted every framework from the project, this layer should compile and run perfectly on its own. <mark style="background: #D2B3FFA6;">This is the layer that never changes when you switch databases, swap messaging brokers, or redesign your API.</mark>

---
#### The Aggregate Root (`domain/model/Order.java`)
**What to avoid:**
```java
import jakarta.persistence.Entity;         // VIOLATION: database annotation
import org.springframework.stereotype.Component; // VIOLATION: framework coupling

@Entity  // VIOLATION: domain model doubling as a DB row mapper
public class Order {
    public String status; // VIOLATION: public mutable field, no rule enforcement

    public void setStatus(String status) { // VIOLATION: bypasses all business rules
        this.status = status;
    }
}
```

When your domain object is also a JPA entity, a database column rename forces a business logic change. Public setters mean any layer in the system can silently mutate state without triggering any rule — the entire point of the domain layer is destroyed.

**The correct approach:**
```java
package com.company.orderservice.domain.model;

import com.company.orderservice.domain.exception.OrderDomainException;
import java.util.ArrayList;
import java.util.Collections;
import java.util.List;
import java.util.UUID;

public class Order {

    private final String orderId;
    private final String customerId;
    private String status; // "PENDING", "SHIPPED", "CANCELLED"
    private final List<String> items;

    // Static factory — the only way to create a valid Order
    public static Order createNew(String customerId, List<String> items) {
        if (items == null || items.isEmpty()) {
            throw new OrderDomainException("An order must contain at least one item.");
        }
        return new Order(UUID.randomUUID().toString(), customerId, "PENDING", items);
    }

    private Order(String orderId, String customerId, String status, List<String> items) {
        this.orderId  = orderId;
        this.customerId = customerId;
        this.status   = status;
        this.items    = new ArrayList<>(items);
    }

    // BUSINESS RULE: cancellation is only legal before shipment
    public void cancel() {
        if ("SHIPPED".equals(this.status)) {
            throw new OrderDomainException("Cannot cancel an order that has already shipped.");
        }
        this.status = "CANCELLED";
    }

    // BUSINESS RULE: items cannot be added to a dead order
    public void addItem(String item) {
        if ("CANCELLED".equals(this.status)) {
            throw new OrderDomainException("Cannot add items to a cancelled order.");
        }
        this.items.add(item);
    }

    // Read-only accessors — no public setters anywhere
    public String getOrderId()     { return orderId; }
    public String getCustomerId()  { return customerId; }
    public String getStatus()      { return status; }
    public List<String> getItems() { return Collections.unmodifiableList(items); }
}
```

Every state transition goes through a named method that enforces the rule before allowing the change. There is no way to put an `Order` into an illegal state from outside this class — the object protects itself.

---

#### The Value Object (`domain/model/Money.java`)
**What to avoid:**
```java
// Tracking price as a raw number
private BigDecimal price;

// Six months later, somewhere in the codebase:
BigDecimal total = usdAmount.add(jpyAmount); // No error. Silent, catastrophic bug.
```

A raw `BigDecimal` carries no currency context. The compiler cannot catch currency mixing. The bug surfaces in production, in a finance calculation, at the worst possible time.

**The correct approach:**
```java
package com.company.orderservice.domain.model;

import java.math.BigDecimal;

public record Money(BigDecimal amount, String currency) {

    // Compact constructor — validates on creation
    public Money {
        if (amount == null || amount.compareTo(BigDecimal.ZERO) < 0) {
            throw new OrderDomainException("Money amount cannot be null or negative.");
        }
    }

    // BUSINESS RULE: currencies must match before arithmetic is allowed
    public Money add(Money other) {
        if (!this.currency.equals(other.currency)) {
            throw new OrderDomainException(
                "Cannot add " + this.currency + " to " + other.currency + ".");
        }
        return new Money(this.amount.add(other.amount), this.currency);
    }
}
```

`Money` bundles the number and its currency unit together permanently. They can never be separated. Anywhere in the system money is handled, the type enforces the rule automatically — the compiler becomes your financial safety net.

---
#### The Repository Interface (`domain/repository/OrderRepository.java`)

**What to avoid:**
```java
import org.springframework.data.jpa.repository.JpaRepository; // VIOLATION

// VIOLATION: domain layer now depends on Hibernate
public interface OrderRepository extends JpaRepository<OrderJpaEntity, String> {
}
```

The moment the domain interface extends `JpaRepository`, your business logic has a compile-time dependency on Hibernate. Switching databases means rewriting domain code — the exact problem this architecture exists to prevent.

**The correct approach:**
```java
package com.company.orderservice.domain.repository;

import com.company.orderservice.domain.model.Order;
import java.util.Optional;

public interface OrderRepository {
    void save(Order order);
    Optional<Order> findById(String orderId);
}
```

This interface is a **contract written by the domain, fulfilled by infrastructure**. The domain declares what it needs. It has no idea whether the implementation behind it uses Postgres, MongoDB, or an in-memory map. The infrastructure layer implements this interface using Spring Data JPA — but the domain never imports a single infrastructure class.

This is the mechanism that makes the entire architecture swappable.

---

#### Annotation Reference
<mark style="background: #FFB86CA6;">This layer intentionally has **no Spring or framework annotations** on its core model classes.</mark> That is not an oversight — it is the point. <mark style="background: #ABF7F7A6;">The absence of annotations is what makes this layer portable, independently testable, and framework-agnostic.</mark>

The only annotations permitted are:
- **`java.util` and standard Java** — `@Override`, `record` compact constructors, standard Java language features.
- **`jakarta.validation` constraints** — passive metadata labels only, if needed on value objects. Never execution-engine annotations.
- Anything that requires a framework runtime to function — `@Entity`, `@Component`, `@Service`, `@KafkaListener` — belongs in the layers outside the domain.

---
#### The Three Strict Rules for This Layer
**No framework imports** — if the import starts with `org.springframework`, `jakarta.persistence`, or any external library name, it does not belong here.
**No public setters** — every state change must go through a named method that enforces the relevant business rule before mutating the field.
**No knowledge of callers** — the domain never knows whether it was invoked by an HTTP controller, a Kafka consumer, or a test. <mark style="background: #FFF3A3A6;">It responds only to method calls with valid Java arguments.</mark>

---
### Layer 4 — The Infrastructure Package
```
com.company.orderservice/
└── infrastructure/
    ├── persistence/
    │   ├── OrderJpaEntity.java              ← DB row mapper
    │   ├── SpringDataOrderRepository.java   ← Spring Data interface
    │   └── OrderPersistenceAdapter.java     ← Implements domain contract
    └── messaging/
        ├── KafkaOrderEventPublisher.java    ← Outbound event broadcast
        ├── KafkaOrderEventConsumer.java     ← Inbound event listener
        ├── RabbitMqNotificationSender.java  ← Outbound work queue
        └── RabbitMqNotificationConsumer.java← Inbound task listener
```

The `infrastructure/` package is the **Physical Wiring**. <mark style="background: #FFF3A3A6;">This is the only layer permitted to use heavy framework annotations, database drivers, and messaging broker clients.</mark> It has one job: <mark style="background: #ADCCFFA6;">implement the contracts the domain defined</mark>, and <mark style="background: #D2B3FFA6;">handle all communication with the outside world — databases, Kafka, RabbitMQ, and any external service.</mark>

---
#### Persistence — The JPA Entity (`persistence/OrderJpaEntity.java`)
```java
package com.company.orderservice.infrastructure.persistence;

import jakarta.persistence.*;
import java.util.List;

@Entity
@Table(name = "orders")
public class OrderJpaEntity {

    @Id
    @Column(name = "order_id", nullable = false)
    private String orderId;

    @Column(name = "customer_id", nullable = false)
    private String customerId;

    @Column(name = "status", nullable = false)
    private String status;

    @ElementCollection
    @CollectionTable(name = "order_items", joinColumns = @JoinColumn(name = "order_id"))
    @Column(name = "item")
    private List<String> items;

    // Standard getters and setters — JPA requires them
    public String getOrderId()              { return orderId; }
    public void setOrderId(String orderId)  { this.orderId = orderId; }
    public String getCustomerId()           { return customerId; }
    public void setCustomerId(String id)    { this.customerId = id; }
    public String getStatus()               { return status; }
    public void setStatus(String status)    { this.status = status; }
    public List<String> getItems()          { return items; }
    public void setItems(List<String> items){ this.items = items; }
}
```

<mark style="background: #FFF3A3A6;">A completely separate object from `Order.java`</mark>. Changes to your SQL schema never touch your domain model, and changes to your business rules never touch your database mapping.

---
#### Persistence — The Spring Data Interface (`persistence/SpringDataOrderRepository.java`)
```java
package com.company.orderservice.infrastructure.persistence;

import org.springframework.data.jpa.repository.JpaRepository;

public interface SpringDataOrderRepository extends JpaRepository<OrderJpaEntity, String> {
    // Spring generates all SQL CRUD operations at runtime — no queries to write
}
```

<mark style="background: #FFB86CA6;">This interface speaks directly to Hibernate.</mark> It knows about `OrderJpaEntity` and SQL. It lives here in infrastructure and never crosses into the domain.

---

#### Persistence — The Adapter (`persistence/OrderPersistenceAdapter.java`)

```java
package com.company.orderservice.infrastructure.persistence;

import com.company.orderservice.domain.model.Order;
import com.company.orderservice.domain.repository.OrderRepository;
import org.springframework.stereotype.Component;
import java.util.Optional;

@Component
public class OrderPersistenceAdapter implements OrderRepository { // fulfils the domain contract

    private final SpringDataOrderRepository springRepo;

    public OrderPersistenceAdapter(SpringDataOrderRepository springRepo) {
        this.springRepo = springRepo;
    }

    @Override
    public void save(Order order) {
        OrderJpaEntity entity = toJpaEntity(order);   // domain → JPA
        springRepo.save(entity);
    }

    @Override
    public Optional<Order> findById(String orderId) {
        return springRepo.findById(orderId)
                         .map(this::toDomainModel);   // JPA → domain
    }

    // Mapping methods stay strictly inside this adapter
    private OrderJpaEntity toJpaEntity(Order order) {
        OrderJpaEntity e = new OrderJpaEntity();
        e.setOrderId(order.getOrderId());
        e.setCustomerId(order.getCustomerId());
        e.setStatus(order.getStatus());
        e.setItems(order.getItems());
        return e;
    }

    private Order toDomainModel(OrderJpaEntity e) {
        return Order.reconstitute(e.getOrderId(), e.getCustomerId(), e.getStatus(), e.getItems());
    }
}
```

<mark style="background: #FFB86CA6;">This adapter is the **only place** in the entire codebase that knows both the domain model and the JPA entity simultaneously</mark>. It translates between them and keeps both sides completely isolated from each other.

---

#### Messaging Outbound — Kafka (`messaging/KafkaOrderEventPublisher.java`)
```java
package com.company.orderservice.infrastructure.messaging;

import org.springframework.kafka.core.KafkaTemplate;
import org.springframework.stereotype.Component;

@Component
public class KafkaOrderEventPublisher {

    private final KafkaTemplate<String, Object> kafkaTemplate;
    private static final String TOPIC = "order-events-topic";

    public KafkaOrderEventPublisher(KafkaTemplate<String, Object> kafkaTemplate) {
        this.kafkaTemplate = kafkaTemplate;
    }

    public void publishOrderCreated(String orderId, String status) {
        OrderEventPayload payload = new OrderEventPayload(orderId, status);
        kafkaTemplate.send(TOPIC, orderId, payload);
    }
}

record OrderEventPayload(String orderId, String status) {}
```

The use case calls an interface method. This adapter fulfils it. Kafka is completely invisible to every layer above.

---

#### Messaging Outbound — RabbitMQ (`messaging/RabbitMqNotificationSender.java`)

```java
package com.company.orderservice.infrastructure.messaging;

import com.company.orderservice.config.RabbitMQConfig;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.stereotype.Component;

@Component
public class RabbitMqNotificationSender {

    private final RabbitTemplate rabbitTemplate;

    public RabbitMqNotificationSender(RabbitTemplate rabbitTemplate) {
        this.rabbitTemplate = rabbitTemplate;
    }

    public void sendNotificationTask(String customerId, String message) {
        String payload = String.format(
            "{\"customerId\":\"%s\", \"message\":\"%s\"}", customerId, message);
        rabbitTemplate.convertAndSend(RabbitMQConfig.NOTIFICATION_QUEUE, payload);
    }
}
```

<mark style="background: #FFB86CA6;">Kafka and RabbitMQ serve different purposes and live as separate classes.</mark> <mark style="background: #ADCCFFA6;">Kafka broadcasts events to many subscribers.</mark> <mark style="background: #D2B3FFA6;">RabbitMQ routes a specific task to one targeted worker queue.</mark> Mixing them into a single messaging class creates an unmanageable god-object.

---
#### Messaging Inbound — Consumers
Consumers are also infrastructure. <mark style="background: #FFB86CA6;">A message arriving from Kafka or RabbitMQ is just another entry point into your application</mark> — the same as an HTTP request. <mark style="background: #BBFABBA6;">The consumer's only job is to unwrap the broker-specific packaging and hand a clean Command to the application layer.</mark>

```java
package com.company.orderservice.infrastructure.messaging;

import com.company.orderservice.application.command.ProcessPaymentCommand;
import com.company.orderservice.application.service.ProcessPaymentUseCase;
import org.springframework.kafka.annotation.KafkaListener;
import org.springframework.stereotype.Component;

@Component
public class KafkaOrderEventConsumer {

    private final ProcessPaymentUseCase processPaymentUseCase;

    public KafkaOrderEventConsumer(ProcessPaymentUseCase processPaymentUseCase) {
        this.processPaymentUseCase = processPaymentUseCase;
    }

    @KafkaListener(topics = "payment-events-topic", groupId = "order-service-group")
    public void onPaymentEvent(String rawJsonPayload) {
        // 1. Parse raw broker payload
        ProcessPaymentCommand command = parseToCommand(rawJsonPayload);

        // 2. Delegate inward — identical pattern to the HTTP controller
        processPaymentUseCase.execute(command);
    }

    private ProcessPaymentCommand parseToCommand(String json) {
        // JSON deserialization logic here
        return new ProcessPaymentCommand(/* parsed fields */);
    }
}
```


```java
@Component
public class RabbitMqNotificationConsumer {

    @RabbitListener(queues = RabbitMQConfig.NOTIFICATION_QUEUE)
    public void onNotificationTask(String rawPayload) {
        // Parse → build Command → delegate to use case
    }
}
```

Notice the pattern is identical to `OrderController`. Every entry point — HTTP, Kafka, RabbitMQ — does exactly three things: <mark style="background: #ADCCFFA6;">parse the raw format, build a Command, delegate to the use case.</mark>

---
#### Annotation Reference
**`@Entity` / `@Table` / `@Column`** — Hibernate annotations. Strictly confined to `OrderJpaEntity`. Never appear on domain models or DTOs.

**`@Component`** — marks infrastructure adapters for Spring dependency injection. Used on adapters and publishers rather than <mark style="background: #FFB86CA6;">`@Service`, which signals orchestration intent.</mark>

**`@KafkaListener`** — <mark style="background: #FFF3A3A6;">binds a method to a Kafka topic</mark>. Contains the broker group ID and topic name. Confined to infrastructure consumers; never appears in application or domain layers.

**`@RabbitListener`** — <mark style="background: #FFF3A3A6;">binds a method to a RabbitMQ queue</mark>. Same confinement rule as `@KafkaListener`.

---
#### The Three Strict Rules for This Layer
**Implement, never dictate** — <mark style="background: #FFB86CA6;">infrastructure fulfils contracts written by the domain</mark>. It never defines its own interfaces for the domain to depend on.

**Translate at the boundary** — <mark style="background: #ABF7F7A6;">the persistence adapter is the only class permitted to know both `Order` (domain) and `OrderJpaEntity` (infrastructure).</mark> Mapping methods live inside the adapter and nowhere else.

**Consumers mirror controllers** — <mark style="background: #FFB8EBA6;">every inbound adapter, regardless of protocol, follows the identical three-step pattern</mark>: **parse raw format → build Command → delegate to use case.** No business logic, no direct database access, no exceptions.