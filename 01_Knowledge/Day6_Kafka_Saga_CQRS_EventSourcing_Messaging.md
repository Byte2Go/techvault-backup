# P5 · Day 6 — Kafka · Saga · CQRS+Event Sourcing · Schema Registry · Messaging Selection
**Pillar:** P5 — Messaging & Event-Driven Architecture  
**Role Priority:** SA 🔵 Core · Java 🟢 Core · AI ⚪ Supporting  
**Day in Plan:** Day 6 (Week 1)  
**Time:** ~3 hours study + 1 hour Q&A practice

---

## Topic 1 · Kafka Architecture — Deep Dive

### In One Line
Kafka is a distributed, durable, ordered, replayable **event log** —<mark style="background: #FFB8EBA6;"> not just a message queue.</mark>

**The Critical Difference:** <mark style="background: #FFF3A3A6;">Traditional message queues (like RabbitMQ) delete messages immediately after consumer acknowledgment</mark>. <mark style="background: #ABF7F7A6;">Kafka retains messages as an immutable sequence of byte arrays</mark>, <mark style="background: #D2B3FFA6;">shifting the burden of tracking state entirely onto the consumers </mark><mark style="background: #ADCCFFA6;">via their read offsets.</mark>

[[Kafka-Introduction]]
[[Kafka Part 1 — Physical Layer- Brokers and Cluster]]
[[Kafka- Part 2 — Storage Layer- Topics and Partitions]]
[[Kafka -Part 2 — Storage Layer- The Offset Log]]
[[Kafka -  Part 3 — Coordination Layer- Leaders and Followers]]
[[Kafka- Part 4 — Failure Recovery Layer- Leader Election]]
[[Kafka- Part 5 — Failure Recovery Layer- KRaft & The Controller]]
[[Kafka- Part 6 — Communication Layer- Client Automatic Recovery]]
[[Kafka - Reliability & Acknowledgements (`acks`)]]
[[Kafka - Part 8 — Idempotence and Exactly-Once Protection]]
[[Kafka- Part 9 — Consumer Layer- Consumer Groups & Parallel Processing]]
[[Kafka - Interview Questions & Architecture Discussions]]
[[Kafka -Part 12 — Enterprise Layer- Kafka in Solution Architecture]]
### Core Concepts

**Key properties:**
- Records are **immutable** — never modified or deleted <mark style="background: #FFB86CA6;">(retention-based cleanup)</mark>
- <mark style="background: #ABF7F7A6;">Consumers track their own</mark> **offset** — can replay from any point
- **Ordering is guaranteed within a partition** — not across partitions

### Partitioning Strategy

```
Producer sends with a key → Kafka hashes key → same key always goes to same partition → ordering guaranteed for that key

Order events keyed by orderId:
  orderId=123 → always Partition 0 → all events for order 123 are ordered
  orderId=456 → always Partition 1 → all events for order 456 are ordered
```

**Partition count rules:**
- <mark style="background: #FFB86CA6;">More partitions = more parallelism (consumers)</mark>
- <mark style="background: #BBFABBA6;">Max consumers in a group = number of partitions</mark>
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

### **Rebalancing:** 
<mark style="background: #FFB86CA6;">When a consumer joins/leaves a group, Kafka reassigns partitions.</mark> During rebalance, consumption pauses. **Example how it rebalancing works:** Let say we have 10 Partition and 5 Consumer in Group, then if i increase the consumer to 20, How reassignment will work?
When you increase the consumer count from 5 to 20 on a topic with 10 partitions, Kafka triggers an automatic coordination process called a **Rebalance**.

Here is exactly how that reassignment works in 3 quick steps:
- **Step 1 (The Trigger):** The 15 new consumer instances boot up and send a `JoinGroup` request to the cluster coordinator broker.
- **Step 2 (The Revocation):** The coordinator stops the entire group, revoking all 10 partition assignments from the original 5 consumers so they stop reading data.
- **Step 3 (The Re-Allocation):** An assignment algorithm runs, mapping 1 partition to each of the first 10 consumers. The remaining 10 consumers receive no assignment and are put into an **Idle** standby state.
### The Final Reassignment Map

|**Component**|**Before Rebalance**|**After Rebalance**|
|---|---|---|
|**Topic Partitions**|10 Partitions|10 Partitions|
|**Total Consumers**|5 Instances|20 Instances|
|**Active Consumers**|**5** (Each handling 2 partitions)|**10** (Each handling 1 partition)|
|**Idle Consumers**|**0**|**10** (Standby, waiting for a crash)|

Your horizontal processing scale hits its absolute limit at **10 active consumers** because of the Golden Rule:==_One partition can only belong to one consumer at a time._== The extra 10 consumers sit completely silent.

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
Consumer reads message → processes it → commits the offset
  → If consumer crashes before commit → re-reads the message (at-least-once delivery)
  → Consumer must be idempotent OR use exactly-once semantics

Auto-commit (risky):
  enable.auto.commit=true → commits every 5 seconds regardless of processing success
  → Can lose messages if crash between auto-commit and processing

Manual commit (correct):
  enable.auto.commit=false
  consumer.commitSync()  → after successful processing
```


### Interview Q&A

**Q: How does Kafka guarantee message ordering?**
A: Ordering is guaranteed within a partition, not across partitions. You guarantee ordering for a specific entity (e.g., all events for Order #123) by using a stable key — the orderId. <mark style="background: #FFB86CA6;">Kafka hashes the key to determine the partition, so all messages with the same key land on the same partition</mark> and are consumed in order. If you need global ordering across all events, use a single partition — but that limits throughput to one consumer.

**Q: How many partitions should a Kafka topic have?**
A: It depends on your throughput target. <mark style="background: #ADCCFFA6;">A single partition typically handles 10-50MB/s. </mark>Divide your target throughput by per-partition throughput to get the minimum. Then factor in consumer parallelism — <mark style="background: #FFB86CA6;">max consumers in a group equals partition count</mark>. <mark style="background: #FF5582A6;">More partitions also means more file handles and more replication overhead.</mark> I start with a reasonably high count (24 or 48 for high-volume topics) because you can increase but not easily decrease partitions, and rebalance using consumer groups to match actual load.

---

## Topic 2 · Producer Patterns — Idempotent & Transactional

### In One Line
Kafka producers can lose, duplicate, or reorder messages under failure — <mark style="background: #FFB86CA6;">idempotent producers eliminate duplicates;</mark> transactional producers give exactly-once write across topics and offsets.

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

**How it works:** Each producer gets a PID (Producer ID). Each message gets a sequence number. <mark style="background: #FFB8EBA6;">Broker rejects duplicate sequence numbers from the same PID</mark>. Producer retries safely — duplicates are deduplicated at broker level.

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
**Mitigation:** Make your consumer **idempotent** — <mark style="background: #FFB8EBA6;">processing the same message twice produces the same result.</mark>

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

## Topic 4 · [[Saga Pattern (Orchestration vs Choreography)]]

### In One Line
Saga coordinates a distributed transaction across multiple services <mark style="background: #FFB86CA6;">through a sequence of local transactions </mark>with compensating actions on failure — no 2PC needed.

### Saga State Machine (Critical for SA Interview)
*Universal Rule of Saga Rollbacks:* If a Saga fails at **Step $N$**, you must execute exactly **$N - 1$ compensating actions** in the reverse order ($Step_{N-1} \rightarrow Step_{N-2} \rightarrow \dots \rightarrow Step_1$).

#### **How the Kafka Event Topology Executes This Cascading Rollback**
Suppose When **Step 7** fails, it publishes a single global error event: `STEP_7_FAILED`. Because Kafka allows multiple independent microservices to subscribe to the same event, the rollback cascades sequentially based on two core mechanics:
##### 1. Choreography Pattern (The Domino Effect)
Each service only listens for the failure of the step directly after it:
- **Service 6** hears `STEP_7_FAILED` $\rightarrow$ Executes `Undo 6` $\rightarrow$ Publishes `UNDO_6_COMPLETED`.
- **Service 5** hears `UNDO_6_COMPLETED` $\rightarrow$ Executes `Undo 5` $\rightarrow$ Publishes `UNDO_5_COMPLETED`
- This chain reaction continues backward until **Service 1** executes `Undo 1` and marks the system as cleanly `FAILED`.

##### 2. Orchestrator Pattern (The Central Commander)
If you prefer centralized control, a dedicated **Saga Coordinator service** listens to the main channel.
- The Coordinator catches the `STEP_7_FAILED` broadcast.
- It looks up its routing table and sends individual, sequential commands to the topics for **Service 6 down to Service 1** to cleanly trigger their undo actions one by one.

<mark style="background: #FFB86CA6;">Persist saga state in DB — if orchestrator crashes, resume from last known state on restart.</mark>

### Interview Q&A
**Q: Design a Saga for an order placement flow with payment and inventory.**
A: I'd use orchestration for this —<mark style="background: #FFB8EBA6;"> three steps with compensation makes choreography hard to trace.</mark> The Order Saga Orchestrator persists state in a DB (each step transition is durable). 
	**Step 1:** reserve inventory — if it fails, mark order failed, done. 
	**Step 2:** charge payment — if it fails, release inventory (compensating), mark failed. **Step 3:** create shipment — if it fails, refund payment and release inventory. Each step calls the downstream service synchronously (for orchestration) or the orchestrator publishes a command event and listens for a result event (fully async orchestration). Saga state is persisted so the orchestrator can resume after a crash.

**Q: How do you handle compensating transactions in Saga?**
A: <mark style="background: #FFB86CA6;">Compensating transactions must be idempotent </mark>— <mark style="background: #FFB8EBA6;">the orchestrator may retry them on failure.</mark>  <mark style="background: #ADCCFFA6;">I design compensations to be safe to call multiple times (same result). </mark>If a compensation itself fails, the saga moves to a FAILED state requiring human intervention — automated compensation can only go so far; some failures need a human.

---

## Topic 5 · [[CQRS & Event Sourcing]]

### In One Line
<mark style="background: #FFB86CA6;">Event Sourcing stores every state change as an immutable event</mark>; <mark style="background: #ADCCFFA6;">CQRS projects those events into optimized read models</mark> — together they give you a full audit log plus fast queries.

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

### Schema Evolution & Compatibility Rules

| Compatibility Mode | Allowed Changes | Use When |
|---|---|---|
| **BACKWARD** | New schema can read old data (add optional fields with defaults) | Consumers upgrade first |
| **FORWARD** | Old schema can read new data (remove optional fields) | Producers upgrade first |
| **FULL** | Both backward + forward | Maximum safety |
| **NONE** | Any change | Dev only |


**Breaking change (REJECTED):**
```
Rename "total" → "amount"   ← consumer reading v1 schema gets null for "amount"
Change "total" type: double → string  ← type mismatch
Remove "orderId" (required) ← existing consumers break
```

---

## Topic 7 · RabbitMQ vs Kafka vs SQS/SNS — Selection Framework

### In One Line
Don't default to Kafka — match the messaging system to the problem; <mark style="background: #ADCCFFA6;">Kafka wins for event streaming, RabbitMQ for task queues</mark>, SQS/SNS for AWS-native serverless.

### Comparison

| Dimension          | Kafka                                              | RabbitMQ                              | AWS SQS/SNS                            |
| ------------------ | -------------------------------------------------- | ------------------------------------- | -------------------------------------- |
| **Model**          | Distributed log (event streaming)                  | Message broker (task queue)           | Managed queue/pub-sub                  |
| **Retention**      | Configurable (days/weeks) — replayable             | Until consumed (or TTL)               | Up to 14 days                          |
| **Ordering**       | ==Per-partition (guaranteed)==                     | ==Per-queue (FIFO queue)==            | SQS FIFO only                          |
| **Throughput**     | Very high (millions/sec)                           | Medium (tens of thousands/sec)        | High (managed)                         |
| **Consumer model** | ==Pull== — consumer controls pace                  | ==Push== — broker pushes to consumers | ==Pull (SQS)== / Push (SNS)            |
| **Replayability**  | Yes — reset offset, replay all                     | No — consumed = gone                  | No                                     |
| **Ops burden**     | High (self-hosted)                                 | Medium                                | Zero (fully managed)                   |
| **Best for**       | Event sourcing, CQRS, audit log, stream processing | Task queues, RPC, routing by content  | AWS-native, serverless, simple pub-sub |

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

### Interview Q&A

**Q: When would you choose Kafka over RabbitMQ?**
A: **Kafka when you need:** 
- <mark style="background: #FFB86CA6;">event replay (you want to rebuild a read model or audit what happened)</mark>, 
- very high throughput (millions of events/sec), 
- multiple independent consumer groups reading the same events, or event sourcing as your persistence model. 
**RabbitMQ when you need:** 
- complex routing logic (topic exchanges, header-based routing), 
- <mark style="background: #ABF7F7A6;">push-based delivery</mark>, simpler ops, or a traditional task queue where consumed = gone is fine. 
**A common pattern:** 
- RabbitMQ for internal job queues (image resizing, email sending) 
- <mark style="background: #FFF3A3A6;">Kafka for domain events that multiple services need to consume and that need to be replayable.</mark>

**Q: How do you handle poison pills in Kafka (messages that always fail processing)?**
A: Dead letter queue pattern. Configure a retry policy with exponential backoff (3 retries: 1s, 2s, 4s). After max retries, the message is published to a DLQ topic (`<original-topic>-dlq`) with the original message plus error metadata (exception, stack trace, attempt count). <mark style="background: #FFB86CA6;">Commit the original offset — don't block the partition for other messages.</mark> A separate DLQ consumer group alerts on-call and enables manual review.
- **The Fetch:** The consumer automatically sends an internal API request to the **Kafka Group Coordinator** asking: _"What was the last committed offset for this group on Partition 1?"_
- **The Resume:** The Coordinator looks up the `__consumer_offsets` ledger, sees the number **13**, and hands it back. The consumer instantly starts pulling data from Offset 13 onward.

---

## Day 6 Quick Reference

| Topic                  | Key Interview Answer                                                              |
| ---------------------- | --------------------------------------------------------------------------------- |
| Kafka ordering         | ==Guaranteed within partition==; use stable key (orderId) for entity ordering     |
| Partitions             | ==Max consumers = partition count==; increase for throughput; can't decrease      |
| acks=all               | No data loss; waits for all ISR; pair with min.insync.replicas=2                  |
| Idempotent producer    | PID + sequence number; broker deduplicates retries                                |
| Transactional producer | Atomic write across topics + offset commit; exactly-once                          |
| At-least-once          | Manual commit after processing; ==consumer must be idempotent==                   |
| Exactly-once           | Kafka Streams EXACTLY_ONCE_V2; 20-30% throughput cost                             |
| DLQ                    | Retry 3x with backoff → publish to -dlq topic → alert + manual fix                |
| Saga — choreography    | ==Services react to events==; simple flows; hard to debug complex ones            |
| Saga — orchestration   | Central orchestrator; flow visible; ==use for complex multi-step + compensation== |
| Schema Registry        | Register Avro schema; enforce BACKWARD compatibility; catch breaks at publish     |
| Kafka vs RabbitMQ      | Kafka = streaming/replay/high throughput; RabbitMQ = routing/task queue           |
| SQS                    | AWS-native, zero ops; FIFO for ordering; pair with SNS for fan-out                |

---

*Tags: #kafka #partitions #consumer-groups #saga #choreography #orchestration #CQRS #event-sourcing #schema-registry #avro #RabbitMQ #SQS #SNS #DLQ #idempotent*
