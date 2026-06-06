# P5 · Day 6 — Kafka · Saga · CQRS+Event Sourcing · Schema Registry · Messaging Selection
**Pillar:** P5 — Messaging & Event-Driven Architecture  
**Role Priority:** SA 🔵 Core · Java 🟢 Core · AI ⚪ Supporting  
**Day in Plan:** Day 6 (Week 1)  
**Time:** ~3 hours study + 1 hour Q&A practice

---

## Topic 1 · Kafka Architecture — Deep Dive

### In One Line
Kafka is a distributed, durable, ordered, replayable event log — not just a message queue — and understanding its internals is what separates a 40L SA from a developer who "knows Kafka."

### Core Concepts

```
Kafka Cluster
├── Broker 1  (handles partitions)
├── Broker 2
└── Broker 3

Topic: "order-events"
├── Partition 0  → Leader: Broker 1, Followers: Broker 2, 3
├── Partition 1  → Leader: Broker 2, Followers: Broker 1, 3
└── Partition 2  → Leader: Broker 3, Followers: Broker 1, 2

Each Partition: immutable, ordered log of records
  Offset 0: OrderPlaced {orderId: 1}
  Offset 1: OrderPlaced {orderId: 2}
  Offset 2: OrderCancelled {orderId: 1}
  ...
```

**Key properties:**
- Records are **immutable** — never modified or deleted (retention-based cleanup)
- Consumers track their own **offset** — can replay from any point
- **Ordering is guaranteed within a partition** — not across partitions

### Partitioning Strategy

```
Producer sends with a key → Kafka hashes key → same key always goes to same partition
                                                → ordering guaranteed for that key

Order events keyed by orderId:
  orderId=123 → always Partition 0 → all events for order 123 are ordered
  orderId=456 → always Partition 1 → all events for order 456 are ordered
```

**Partition count rules:**
- More partitions = more parallelism (consumers)
- Max consumers in a group = number of partitions
- Choose partition count based on target throughput; you can increase (hard to decrease)
- Rule of thumb: target_throughput / throughput_per_partition (typically 10MB/s per partition)

### Consumer Groups

```
Topic "order-events" — 3 partitions
Consumer Group "inventory-service":
  Consumer A → reads Partition 0
  Consumer B → reads Partition 1
  Consumer C → reads Partition 2
  → Parallel consumption; each partition consumed by exactly ONE consumer in the group

Consumer Group "notification-service":
  Consumer X → reads all 3 partitions (only 1 consumer in this group)

Consumer Group "analytics-service":
  Consumer P → reads Partition 0
  Consumer Q → reads Partition 1, 2

Key insight: Each consumer group gets ALL messages independently.
  → Fan-out to multiple services without duplicate logic in producer.
```

**Rebalancing:** When a consumer joins/leaves a group, Kafka reassigns partitions. During rebalance, consumption pauses. Use `CooperativeStickyAssignor` (Kafka 2.4+) to minimize rebalance disruption.

### Replication & Durability

```
Replication Factor = 3 (1 leader + 2 followers)
Producer acks=all → waits for leader + all in-sync replicas (ISR) to acknowledge
  → No data loss even if 2 out of 3 brokers fail simultaneously
  → Higher latency than acks=1 but safe for financial data

min.insync.replicas=2 → at least 2 replicas must be in sync for writes to succeed
  → If only 1 replica is up → producer gets error (safer than silent data loss)
```

### Offset Management

```
Consumer reads message → processes it → commits offset
  → If consumer crashes before commit → re-reads the message (at-least-once delivery)
  → Consumer must be idempotent OR use exactly-once semantics

Auto-commit (risky):
  enable.auto.commit=true → commits every 5 seconds regardless of processing success
  → Can lose messages if crash between auto-commit and processing

Manual commit (correct):
  enable.auto.commit=false
  consumer.commitSync()  → after successful processing
```

### Interview Q&A (40L SA Level)

**Q: How does Kafka guarantee message ordering?**
A: Ordering is guaranteed within a partition, not across partitions. You guarantee ordering for a specific entity (e.g., all events for Order #123) by using a stable key — the orderId. Kafka hashes the key to determine the partition, so all messages with the same key land on the same partition and are consumed in order. If you need global ordering across all events, use a single partition — but that limits throughput to one consumer.

**Q: How many partitions should a Kafka topic have?**
A: It depends on your throughput target. A single partition typically handles 10-50MB/s. Divide your target throughput by per-partition throughput to get the minimum. Then factor in consumer parallelism — max consumers in a group equals partition count. More partitions also means more file handles and more replication overhead. I start with a reasonably high count (24 or 48 for high-volume topics) because you can increase but not easily decrease partitions, and rebalance using consumer groups to match actual load.

---

## Topic 2 · Producer Patterns — Idempotent & Transactional

### In One Line
Kafka producers can lose, duplicate, or reorder messages under failure — idempotent producers eliminate duplicates; transactional producers give exactly-once write across topics and offsets.

### Producer Delivery Semantics

| Setting | Behaviour | Risk |
|---|---|---|
| `acks=0` | Fire and forget | Message loss if broker down |
| `acks=1` | Leader acknowledges | Loss if leader fails before replication |
| `acks=all` + `min.insync.replicas=2` | All ISR acknowledge | No loss; higher latency |

### Idempotent Producer (Kafka 0.11+)

```java
Properties props = new Properties();
props.put(ProducerConfig.ENABLE_IDEMPOTENCE_CONFIG, true);
props.put(ProducerConfig.ACKS_CONFIG, "all");
props.put(ProducerConfig.RETRIES_CONFIG, Integer.MAX_VALUE);
props.put(ProducerConfig.MAX_IN_FLIGHT_REQUESTS_PER_CONNECTION, 5);

KafkaProducer<String, String> producer = new KafkaProducer<>(props);
```

**How it works:** Each producer gets a PID (Producer ID). Each message gets a sequence number. Broker rejects duplicate sequence numbers from the same PID. Producer retries safely — duplicates are deduplicated at broker level.

### Transactional Producer — Exactly-Once Across Topics

```java
props.put(ProducerConfig.TRANSACTIONAL_ID_CONFIG, "order-service-tx-1");
producer.initTransactions();

try {
    producer.beginTransaction();
    
    // Write to multiple topics atomically
    producer.send(new ProducerRecord<>("order-events", orderId, orderPlacedEvent));
    producer.send(new ProducerRecord<>("audit-events", orderId, auditEvent));
    
    // Commit consumer offset + produce atomically (read-process-write)
    producer.sendOffsetsToTransaction(currentOffsets, consumerGroupId);
    
    producer.commitTransaction();
} catch (Exception e) {
    producer.abortTransaction();  // All writes rolled back
}
```

**Use case:** Consume from topic A, process, produce to topic B — all as one atomic operation. If the service crashes mid-way, none of it is visible to consumers.

---

## Topic 3 · Consumer Patterns — Delivery Guarantees

### At-Least-Once (Default — Most Common)

```java
// Manual commit after processing
while (true) {
    ConsumerRecords<String, String> records = consumer.poll(Duration.ofMillis(100));
    for (ConsumerRecord<String, String> record : records) {
        processOrder(record.value());    // Process first
        consumer.commitSync();           // Then commit offset
    }
}
```

**Risk:** If service crashes between processing and committing → message is reprocessed.  
**Mitigation:** Make your consumer **idempotent** — processing the same message twice produces the same result.

**Idempotent consumer pattern:**
```java
void processOrder(OrderPlaced event) {
    if (processedEventRepo.exists(event.eventId())) {
        return;  // Already processed — skip
    }
    // Process...
    processedEventRepo.markProcessed(event.eventId());  // Deduplication store (Redis/DB)
}
```

### Exactly-Once (Kafka Streams / Transactions)

```java
// In Kafka Streams
StreamsConfig config = new StreamsConfig();
config.put(StreamsConfig.PROCESSING_GUARANTEE_CONFIG, StreamsConfig.EXACTLY_ONCE_V2);

// Kafka manages offset commits + output writes as a single atomic transaction
// No duplicate processing, no loss
```

**Cost:** Throughput reduced (~20-30%), more coordination overhead.  
**Use when:** Financial transactions, inventory deductions — anywhere double-processing is catastrophic.

### Dead Letter Queue (DLQ) Pattern

```
Consumer polls message → tries to process
  → Processing fails (bad data, downstream unavailable)
  → Retry 3 times with exponential backoff
  → Still fails → publish to DLQ topic: "order-events-dlq"
  → Commit offset (don't block the main topic)

DLQ processor (separate service):
  → Alerts + manual review
  → Fix bad data → republish to original topic
  → Or discard with audit log
```

```java
// Spring Kafka DLQ configuration
@Bean
public DefaultErrorHandler errorHandler(KafkaTemplate<String, String> template) {
    DeadLetterPublishingRecoverer recoverer = new DeadLetterPublishingRecoverer(template,
        (record, ex) -> new TopicPartition(record.topic() + "-dlq", record.partition()));
    
    ExponentialBackOffWithMaxRetries backoff = new ExponentialBackOffWithMaxRetries(3);
    backoff.setInitialInterval(1000L);   // 1s, 2s, 4s
    backoff.setMultiplier(2.0);
    
    return new DefaultErrorHandler(recoverer, backoff);
}
```

---

## Topic 4 · Saga Pattern — End-to-End Design

### In One Line
Saga coordinates a distributed transaction across multiple services through a sequence of local transactions with compensating actions on failure — no 2PC needed.

### Choreography Saga — Design

```
Order Service publishes: OrderPlaced
                              ↓
Payment Service listens → charges card → publishes: PaymentCharged
                                                         ↓
Inventory Service listens → reserves stock → publishes: StockReserved
                                                               ↓
Shipping Service listens → creates shipment → publishes: ShipmentCreated
                                                                ↓
Notification Service listens → sends confirmation

Failure at Inventory (insufficient stock):
Inventory publishes: StockReservationFailed
                              ↓
Payment Service listens → refunds card → publishes: PaymentRefunded  ← compensating tx
                              ↓
Order Service listens → marks order FAILED
```

**Kafka topics per event type:**
```
order-placed
payment-charged
payment-refund-requested    ← compensating
stock-reserved
stock-reservation-failed    ← failure signal
shipment-created
order-failed
```

### Orchestration Saga — Design

```java
@Service
public class OrderSagaOrchestrator {
    
    public void execute(OrderPlacedEvent event) {
        SagaState state = sagaStateRepo.create(event.orderId(), STARTED);
        
        try {
            // Step 1: Reserve inventory
            InventoryResponse inv = inventoryService.reserve(event);
            if (!inv.success()) {
                compensate(state, STEP_INVENTORY);
                return;
            }
            state.advanceTo(INVENTORY_RESERVED);
            
            // Step 2: Charge payment
            PaymentResponse pay = paymentService.charge(event);
            if (!pay.success()) {
                compensate(state, STEP_PAYMENT);
                return;
            }
            state.advanceTo(PAYMENT_CHARGED);
            
            // Step 3: Create shipment
            shippingService.createShipment(event);
            state.complete();
            
        } catch (Exception e) {
            compensate(state, state.currentStep());
        }
    }
    
    private void compensate(SagaState state, SagaStep failedAt) {
        // Roll back completed steps in reverse order
        if (failedAt.isAfter(STEP_PAYMENT)) paymentService.refund(state.orderId());
        if (failedAt.isAfter(STEP_INVENTORY)) inventoryService.release(state.orderId());
        state.fail();
        eventPublisher.publish(new OrderFailed(state.orderId()));
    }
}
```

### Saga State Machine (Critical for SA Interview)

```
STARTED → INVENTORY_RESERVED → PAYMENT_CHARGED → SHIPMENT_CREATED → COMPLETED
                ↓                      ↓
         COMPENSATING_PAYMENT   COMPENSATING_INVENTORY
                ↓                      ↓
           FAILED ←──────────────── FAILED
```

Persist saga state in DB — if orchestrator crashes, resume from last known state on restart.

### Choreography vs Orchestration — Decision

| Dimension | Choreography | Orchestration |
|---|---|---|
| Complexity | Grows fast with more services | Centralized — visible flow |
| Coupling | Services coupled to events (implicit) | Services coupled to orchestrator (explicit) |
| Debugging | Hard — trace events across topics | Easy — orchestrator logs each step |
| SPOF | No SPOF | Orchestrator is a potential SPOF (make HA) |
| **Use when** | Simple 2-3 step flows | Complex multi-step, compensations needed |

### Interview Q&A (40L SA Level)

**Q: Design a Saga for an order placement flow with payment and inventory.**
A: I'd use orchestration for this — three steps with compensation makes choreography hard to trace. The Order Saga Orchestrator persists state in a DB (each step transition is durable). Step 1: reserve inventory — if it fails, mark order failed, done. Step 2: charge payment — if it fails, release inventory (compensating), mark failed. Step 3: create shipment — if it fails, refund payment and release inventory. Each step calls the downstream service synchronously (for orchestration) or the orchestrator publishes a command event and listens for a result event (fully async orchestration). Saga state is persisted so the orchestrator can resume after a crash.

**Q: How do you handle compensating transactions in Saga?**
A: Compensating transactions must be idempotent — the orchestrator may retry them on failure. Each compensation is a domain operation in its own right: PaymentService.refund() doesn't just undo a charge, it creates a new Refund aggregate with its own audit trail. I design compensations to be safe to call multiple times (same result). If a compensation itself fails, the saga moves to a FAILED state requiring human intervention — automated compensation can only go so far; some failures need a human.

---

## Topic 5 · CQRS + Event Sourcing — End to End

### In One Line
Event Sourcing stores every state change as an immutable event; CQRS projects those events into optimized read models — together they give you a full audit log plus fast queries.

### Full Architecture

```
WRITE SIDE:
REST API → Command Handler → Aggregate (validates, generates events)
                                    ↓ saves to Event Store
                            [Event Store: PostgreSQL / EventStoreDB / Kafka]
                                    ↓ publishes events
                            Event Bus (Kafka)

READ SIDE (Projectors — listen to Kafka):
  ├── OrderSummaryProjector → updates PostgreSQL "order_summary" table
  ├── CustomerOrderHistoryProjector → updates Elasticsearch index
  └── RealtimeDashboardProjector → pushes to Redis / WebSocket

QUERY:
  GET /orders/{id}/summary → reads from PostgreSQL projection
  GET /orders/search?q=... → reads from Elasticsearch projection
  Dashboard → reads from Redis
```

### Event Store Schema (PostgreSQL)

```sql
CREATE TABLE event_store (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    aggregate_id    VARCHAR(100) NOT NULL,
    aggregate_type  VARCHAR(100) NOT NULL,
    event_type      VARCHAR(100) NOT NULL,
    payload         JSONB NOT NULL,
    metadata        JSONB,
    version         INTEGER NOT NULL,       -- optimistic concurrency
    occurred_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE (aggregate_id, version)          -- prevents concurrent version conflicts
);

CREATE INDEX idx_event_store_aggregate ON event_store (aggregate_id, version);
```

### Aggregate Reconstitution

```java
public class Order {
    private OrderId id;
    private OrderStatus status;
    private List<OrderLine> lines = new ArrayList<>();
    private int version = 0;
    private List<DomainEvent> uncommittedEvents = new ArrayList<>();

    // Reconstitute from event history
    public static Order reconstitute(List<DomainEvent> events) {
        Order order = new Order();
        events.forEach(order::apply);
        return order;
    }

    // Business method — generates event
    public void addItem(Product product, int qty) {
        if (status != OPEN) throw new InvalidOrderStateException();
        apply(new ItemAdded(id, product.id(), qty, product.price()));
    }

    // Apply — mutates state, records event
    private void apply(DomainEvent event) {
        switch (event) {
            case OrderPlaced e -> { this.id = e.orderId(); this.status = OPEN; }
            case ItemAdded e   -> lines.add(new OrderLine(e.productId(), e.qty(), e.price()));
            case OrderShipped e -> this.status = SHIPPED;
        }
        this.version++;
        this.uncommittedEvents.add(event);
    }
}
```

### Snapshot Pattern (Performance)

```
Problem: Order with 500 events → must replay 500 events to get current state → slow

Solution:
  Every 50 events → save a Snapshot of current aggregate state
  On reconstitution → load latest snapshot + only events after snapshot version

SELECT * FROM snapshots WHERE aggregate_id = ? ORDER BY version DESC LIMIT 1;
SELECT * FROM event_store WHERE aggregate_id = ? AND version > ? ORDER BY version;
```

### Projection Rebuilding

```
Need to rebuild a read model (e.g., added new field to Elasticsearch index):
  1. Stop the projector consumer group
  2. Reset consumer group offset to beginning: kafka-consumer-groups.sh --reset-offsets --to-earliest
  3. Truncate the read model store
  4. Restart projector → replays all events from beginning → rebuilds read model
  → This is a superpower of Event Sourcing — any read model can be rebuilt anytime
```

---

## Topic 6 · Schema Registry & Avro

### In One Line
Schema Registry centralizes event schema definitions and enforces compatibility rules — so producers and consumers can evolve independently without breaking each other.

### Why Schema Registry

```
Without registry:
  Java producer sends JSON: { "orderId": "123", "total": 99.99 }
  Python consumer expects: { "orderId": "123", "amount": 99.99 }
  → Field renamed → Python consumer silently gets null → data corruption, no error

With Confluent Schema Registry:
  Producer registers schema before publishing
  Consumer validates incoming messages against registered schema
  Incompatible schema change → REJECTED at publish time → caught before reaching consumers
```

### Avro Schema

```json
{
  "type": "record",
  "name": "OrderPlaced",
  "namespace": "com.company.events",
  "fields": [
    {"name": "orderId",    "type": "string"},
    {"name": "customerId", "type": "string"},
    {"name": "total",      "type": {"type": "bytes", "logicalType": "decimal", "precision": 10, "scale": 2}},
    {"name": "currency",   "type": "string", "default": "INR"},
    {"name": "occurredAt", "type": {"type": "long", "logicalType": "timestamp-millis"}}
  ]
}
```

### Schema Evolution & Compatibility Rules

| Compatibility Mode | Allowed Changes | Use When |
|---|---|---|
| **BACKWARD** | New schema can read old data (add optional fields with defaults) | Consumers upgrade first |
| **FORWARD** | Old schema can read new data (remove optional fields) | Producers upgrade first |
| **FULL** | Both backward + forward | Maximum safety |
| **NONE** | Any change | Dev only |

**Safe evolution (BACKWARD compatible):**
```json
// v1:  {"name": "total", "type": "double"}
// v2:  {"name": "total", "type": "double"},
//       {"name": "currency", "type": "string", "default": "INR"}  ← new optional field
//   → Consumers on v1 ignore "currency"; consumers on v2 read it
```

**Breaking change (REJECTED):**
```
Rename "total" → "amount"   ← consumer reading v1 schema gets null for "amount"
Change "total" type: double → string  ← type mismatch
Remove "orderId" (required) ← existing consumers break
```

### Spring Kafka + Avro

```java
// Producer
@Bean
public KafkaTemplate<String, OrderPlaced> kafkaTemplate(ProducerFactory<String, OrderPlaced> factory) {
    return new KafkaTemplate<>(factory);
}

// application.yml
spring:
  kafka:
    producer:
      key-serializer: org.apache.kafka.common.serialization.StringSerializer
      value-serializer: io.confluent.kafka.serializers.KafkaAvroSerializer
    properties:
      schema.registry.url: https://schema-registry.company.com
      auto.register.schemas: false   # Don't auto-register in prod; use CI/CD
```

---

## Topic 7 · RabbitMQ vs Kafka vs SQS/SNS — Selection Framework

### In One Line
Don't default to Kafka — match the messaging system to the problem; Kafka wins for event streaming, RabbitMQ for task queues, SQS/SNS for AWS-native serverless.

### Comparison

| Dimension | Kafka | RabbitMQ | AWS SQS/SNS |
|---|---|---|---|
| **Model** | Distributed log (event streaming) | Message broker (task queue) | Managed queue/pub-sub |
| **Retention** | Configurable (days/weeks) — replayable | Until consumed (or TTL) | Up to 14 days |
| **Ordering** | Per-partition (guaranteed) | Per-queue (FIFO queue) | SQS FIFO only |
| **Throughput** | Very high (millions/sec) | Medium (tens of thousands/sec) | High (managed) |
| **Consumer model** | Pull — consumer controls pace | Push — broker pushes to consumers | Pull (SQS) / Push (SNS) |
| **Replayability** | Yes — reset offset, replay all | No — consumed = gone | No |
| **Ops burden** | High (self-hosted) | Medium | Zero (fully managed) |
| **Best for** | Event sourcing, CQRS, audit log, stream processing | Task queues, RPC, routing by content | AWS-native, serverless, simple pub-sub |

### Decision Framework

```
Q1: Do you need to replay events (audit, rebuild read models, debug)?
  YES → Kafka (event log semantics)

Q2: Do you need complex routing (route by header, content, exchange types)?
  YES → RabbitMQ (flexible routing: direct, topic, fanout, headers exchanges)

Q3: Are you all-in on AWS and want zero ops?
  YES → SQS (queues) + SNS (pub-sub fan-out)

Q4: Do you need very high throughput stream processing?
  YES → Kafka

Q5: Simple task queue — workers processing jobs?
  → RabbitMQ or SQS (simpler than Kafka for this)
```

### RabbitMQ Exchange Types

```
Direct Exchange:   Route by exact routing key (order.placed → order-queue)
Topic Exchange:    Route by pattern (order.* → all order events; *.failed → all failures)
Fanout Exchange:   Broadcast to ALL bound queues (no routing key)
Headers Exchange:  Route by message header values
```

### SQS Key Patterns

```
Standard Queue:    At-least-once, best-effort ordering, unlimited throughput
FIFO Queue:        Exactly-once, strict ordering, 3000 msg/sec (or 300 without batching)
SQS + SNS:         SNS topic fans out to multiple SQS queues (fan-out pattern)

Dead Letter Queue: After maxReceiveCount failures → move to DLQ → alert + manual review
Visibility Timeout: Message invisible to other consumers while being processed
                    Set > max processing time to prevent double-processing
```

### Interview Q&A (40L SA Level)

**Q: When would you choose Kafka over RabbitMQ?**
A: Kafka when you need: event replay (you want to rebuild a read model or audit what happened), very high throughput (millions of events/sec), multiple independent consumer groups reading the same events, or event sourcing as your persistence model. RabbitMQ when you need: complex routing logic (topic exchanges, header-based routing), push-based delivery, simpler ops, or a traditional task queue where consumed = gone is fine. A common pattern: RabbitMQ for internal job queues (image resizing, email sending) and Kafka for domain events that multiple services need to consume and that need to be replayable.

**Q: How do you handle poison pills in Kafka (messages that always fail processing)?**
A: Dead letter queue pattern. Configure a retry policy with exponential backoff (3 retries: 1s, 2s, 4s). After max retries, the message is published to a DLQ topic (`<original-topic>-dlq`) with the original message plus error metadata (exception, stack trace, attempt count). Commit the original offset — don't block the partition for other messages. A separate DLQ consumer group alerts on-call and enables manual review. Fixed messages are republished to the original topic. In Spring Kafka this is handled by `DefaultErrorHandler` with `DeadLetterPublishingRecoverer`.

---

## Day 6 Quick Reference

| Topic | Key Interview Answer |
|---|---|
| Kafka ordering | Guaranteed within partition; use stable key (orderId) for entity ordering |
| Partitions | Max consumers = partition count; increase for throughput; can't decrease |
| acks=all | No data loss; waits for all ISR; pair with min.insync.replicas=2 |
| Idempotent producer | PID + sequence number; broker deduplicates retries |
| Transactional producer | Atomic write across topics + offset commit; exactly-once |
| At-least-once | Manual commit after processing; consumer must be idempotent |
| Exactly-once | Kafka Streams EXACTLY_ONCE_V2; 20-30% throughput cost |
| DLQ | Retry 3x with backoff → publish to -dlq topic → alert + manual fix |
| Saga — choreography | Services react to events; simple flows; hard to debug complex ones |
| Saga — orchestration | Central orchestrator; flow visible; use for complex multi-step + compensation |
| Schema Registry | Register Avro schema; enforce BACKWARD compatibility; catch breaks at publish |
| Kafka vs RabbitMQ | Kafka = streaming/replay/high throughput; RabbitMQ = routing/task queue |
| SQS | AWS-native, zero ops; FIFO for ordering; pair with SNS for fan-out |

---

*Tags: #kafka #partitions #consumer-groups #saga #choreography #orchestration #CQRS #event-sourcing #schema-registry #avro #RabbitMQ #SQS #SNS #DLQ #idempotent*
