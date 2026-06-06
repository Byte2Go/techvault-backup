# P7 · Day 9 — Circuit Breaker · SLO · Distributed Tracing · HA/DR · CAP · Scalability
**Pillar:** P7 — Resilience & Observability  
**Role Priority:** SA 🔵 Core · Java 🟢 Supporting · AI 🟣 Supporting  
**Day in Plan:** Day 9 (Week 2)  
**Time:** ~3 hours study + 1 hour Q&A practice

---

## Topic 1 · Circuit Breaker — Resilience4j

### In One Line
A circuit breaker stops calling a failing dependency and fails fast — preventing cascading failures from taking down your entire system.

### The Problem Without Circuit Breaker

```
OrderService → PaymentService (going slow — 10s response)

Without CB:
  All OrderService threads blocked waiting for PaymentService
  Thread pool exhausted → OrderService also stops responding
  → Cascading failure: one slow service kills the whole system

With CB:
  After N failures → circuit opens → calls fail immediately (no wait)
  → OrderService stays responsive; can serve from cache or return error quickly
  → PaymentService gets time to recover
```

### Circuit Breaker States

```
         failures > threshold
CLOSED ─────────────────────→ OPEN
  ↑                              │
  │ success > threshold          │ after waitDuration
  │                              ↓
HALF-OPEN ←─────────────────── OPEN
  │ trial calls allowed
  │ if success → CLOSED
  │ if failure → OPEN again
```

- **CLOSED** — normal operation; calls pass through; failures counted
- **OPEN** — fast fail; no calls to dependency; returns fallback immediately
- **HALF-OPEN** — probe state; allows N trial calls to test if service recovered

### Resilience4j Configuration (Spring Boot)

```yaml
# application.yml
resilience4j:
  circuitbreaker:
    instances:
      payment-service:
        registerHealthIndicator: true
        slidingWindowType: COUNT_BASED       # or TIME_BASED
        slidingWindowSize: 10                # evaluate last 10 calls
        minimumNumberOfCalls: 5             # min calls before CB evaluates
        failureRateThreshold: 50            # open if 50%+ calls fail
        waitDurationInOpenState: 30s        # stay open for 30 seconds
        permittedNumberOfCallsInHalfOpenState: 3  # 3 trial calls
        slowCallDurationThreshold: 2s       # calls > 2s count as slow
        slowCallRateThreshold: 80           # open if 80%+ calls are slow

  retry:
    instances:
      payment-service:
        maxAttempts: 3
        waitDuration: 500ms
        exponentialBackoffMultiplier: 2     # 500ms, 1s, 2s
        retryExceptions:
          - java.net.ConnectException
          - java.util.concurrent.TimeoutException
        ignoreExceptions:
          - com.company.PaymentDeclinedException  # don't retry business errors

  bulkhead:
    instances:
      payment-service:
        maxConcurrentCalls: 20             # max 20 concurrent calls
        maxWaitDuration: 100ms             # wait 100ms if at limit, then reject
```

### Applying in Spring Boot

```java
@Service
public class PaymentServiceClient {

    @CircuitBreaker(name = "payment-service", fallbackMethod = "paymentFallback")
    @Retry(name = "payment-service")
    @Bulkhead(name = "payment-service")
    @TimeLimiter(name = "payment-service")   // timeout
    public CompletableFuture<PaymentResult> processPayment(PaymentRequest request) {
        return CompletableFuture.supplyAsync(() -> 
            paymentServiceRestClient.post(request));
    }

    // Fallback — called when CB is open or all retries exhausted
    public CompletableFuture<PaymentResult> paymentFallback(
            PaymentRequest request, Exception ex) {
        log.error("Payment service unavailable, returning pending status", ex);
        // Queue for async processing; return "PENDING" status to user
        pendingPaymentQueue.enqueue(request);
        return CompletableFuture.completedFuture(
            PaymentResult.pending("Will be processed shortly"));
    }
}
```

### Retry Patterns

```java
// Exponential backoff with jitter (prevents synchronized retry storms)
RetryConfig config = RetryConfig.custom()
    .maxAttempts(3)
    .intervalFunction(IntervalFunction.ofExponentialRandomBackoff(
        Duration.ofMillis(500),   // initial interval
        2.0,                      // multiplier
        Duration.ofSeconds(10)    // max interval
    ))
    .retryOnException(ex -> ex instanceof ConnectException)
    .build();

// Jitter: adds randomness so retrying services don't all hit dependency at same time
// Retry 1: ~500ms, Retry 2: ~1000ms ± rand, Retry 3: ~2000ms ± rand
```

### Bulkhead — Thread Pool Isolation

```yaml
# Separate thread pool per downstream service
resilience4j:
  thread-pool-bulkhead:
    instances:
      payment-service:
        maxThreadPoolSize: 10
        coreThreadPoolSize: 5
        queueCapacity: 20
      inventory-service:
        maxThreadPoolSize: 10
        coreThreadPoolSize: 5
        queueCapacity: 20
```

**Why:** If PaymentService is slow and consumes all 10 threads in its pool, InventoryService still has its own 10 threads — they don't starve each other. Without bulkhead, one slow downstream service eats all shared threads.

### Interview Q&A

**Q: Explain circuit breaker states and when each applies.**
A: Three states. Closed — normal operation; requests flow through; failures counted in a sliding window. When failure rate crosses the threshold (e.g., 50% of last 10 calls), circuit opens. Open — fast fail; no requests sent to the dependency; fallback invoked immediately; the system stops waiting and returns an error or cached response. After a wait duration (e.g., 30s), moves to half-open. Half-open — probe state; allows a limited number of trial calls. If they succeed, circuit closes (service recovered). If they fail, circuit reopens. This pattern prevents cascading failures — a struggling downstream service doesn't drag down the caller.

**Q: What is the difference between circuit breaker and retry? How do they work together?**
A: Retry handles transient failures — network blip, temporary timeout — by attempting the call again with backoff. Circuit breaker handles sustained failures — dependency is actually down or overloaded — by stopping all calls and failing fast. They compose: retry is inner (tries 3 times), circuit breaker is outer (if 50% of recent calls fail, open the circuit and skip retries entirely). Without circuit breaker, retries on a dead service multiply load on something that can't handle it. The order matters — apply in this sequence: TimeLimiter → Bulkhead → CircuitBreaker → Retry → operation.

---

## Topic 2 · SLI / SLO / SLA / Error Budgets

### In One Line
SLIs measure system health, SLOs set the target, SLAs are the contract with customers, and error budgets decide how much risk you can take — this is the language of reliability at senior level.

### Definitions

```
SLI (Service Level Indicator) — What you measure
  → "99.2% of order placement requests completed in under 500ms this week"

SLO (Service Level Objective) — The internal target
  → "99.5% of requests must complete in under 500ms"
  → Internal goal; breach triggers engineering action, not customer penalty

SLA (Service Level Agreement) — The external contract
  → "We guarantee 99.9% uptime; if breached, you get 10% credit"
  → Legal/commercial; SLO is tighter than SLA (buffer)

Error Budget — How much you can fail and still meet SLO
  → SLO = 99.9% → 0.1% error budget
  → Month = 43,200 minutes → error budget = 43.2 minutes downtime/month
  → If you've used 40 minutes: 3.2 minutes left → freeze risky deployments
```

### Choosing Good SLIs

```
Availability SLI:
  success_requests / total_requests × 100
  → "What % of requests returned 2xx or 3xx?"

Latency SLI:
  requests_under_threshold / total_requests × 100
  → "What % of requests completed in under 500ms?"
  → Use percentiles (p99, p99.9) — don't use average (hides tail latency)

Error rate SLI:
  error_requests / total_requests × 100
  → "What % of requests returned 5xx?"

Saturation SLI:
  current_utilization / max_capacity × 100
  → "What % of DB connection pool is in use?"
```

### SLO Design Example

```
System: Order placement API
SLIs chosen:
  1. Availability: % of requests that return non-5xx
  2. Latency: % of requests completing in < 500ms (p99 window)
  3. Error rate: % of payment failures (business metric)

SLOs:
  Availability SLO: 99.9% over 30 days
  Latency SLO: 99% of requests < 500ms over 24 hours
  Error rate SLO: < 0.1% payment failures over 1 hour

Error budget (availability):
  Monthly: 43,200 min × 0.1% = 43.2 min budget
  Week 1 used: 12 min (planned maintenance)
  Week 2 remaining: 31.2 min
  → Safe to deploy; 31 minutes buffer

Error budget policy:
  > 50% budget consumed: no non-critical deployments
  > 90% budget consumed: freeze all deployments; focus on reliability
  Budget reset: monthly
```

### Prometheus — SLO Metrics

```yaml
# Prometheus recording rules for SLIs
groups:
  - name: order-service-slis
    rules:
      # Availability SLI — 5-minute window
      - record: job:order_availability:ratio_rate5m
        expr: |
          sum(rate(http_requests_total{job="order-service",code!~"5.."}[5m]))
          /
          sum(rate(http_requests_total{job="order-service"}[5m]))

      # Latency SLI — % of requests under 500ms
      - record: job:order_latency_slo:ratio_rate5m
        expr: |
          sum(rate(http_request_duration_seconds_bucket{
            job="order-service", le="0.5"}[5m]))
          /
          sum(rate(http_request_duration_seconds_count{
            job="order-service"}[5m]))

# Alert when error budget burn rate is too high
- alert: OrderServiceErrorBudgetBurn
  expr: job:order_availability:ratio_rate5m < 0.995
  for: 5m
  labels:
    severity: warning
  annotations:
    summary: "Order service availability below SLO — burning error budget"
```

### Interview Q&A

**Q: How would you design an SLO for a payment API?**
A: Start with what matters to users — can they pay successfully, and how fast? SLI 1: availability — percentage of payment requests returning non-5xx. SLI 2: latency — percentage of requests completing under 3 seconds (payment users tolerate more latency than a search query). SLI 3: business success rate — percentage of payments that actually succeed (not just HTTP 200; the downstream Razorpay call must also succeed). SLO: 99.95% availability, 99% of requests under 3s, error budget of 21.6 minutes/month. Error budget policy: if we burn more than 50% in two weeks, freeze feature deployments until reliability work catches up.

---

## Topic 3 · Distributed Tracing

### In One Line
Distributed tracing follows a single request across all microservices, showing exactly where time was spent and where failures occurred — impossible to debug complex systems without it.

### The Problem

```
User reports: "My order placement takes 8 seconds sometimes"

Without tracing:
  Order Service logs: "placeOrder completed in 8023ms" ← useless
  No visibility into which downstream call was slow

With tracing:
  Trace ID: abc-123
  OrderService.placeOrder         [0ms → 8023ms]  total
    ├── InventoryService.reserve  [10ms → 95ms]   fast ✓
    ├── PaymentService.charge     [100ms → 7850ms] SLOW ← root cause
    │     └── Razorpay API call   [150ms → 7800ms] VERY SLOW
    └── KafkaPublisher.publish    [7900ms → 8010ms] fast ✓
```

### OpenTelemetry — The Standard

```java
// Spring Boot auto-instruments HTTP calls, JDBC, Kafka, gRPC
// Add dependency: micrometer-tracing-bridge-otel + opentelemetry-exporter-otlp

// Manual span for important business operations
@Service
public class OrderService {

    private final Tracer tracer;

    public OrderId placeOrder(PlaceOrderCommand cmd) {
        Span span = tracer.spanBuilder("placeOrder")
            .setAttribute("order.customerId", cmd.customerId())
            .setAttribute("order.itemCount", cmd.items().size())
            .startSpan();

        try (Scope scope = span.makeCurrent()) {
            // business logic — child spans created automatically for HTTP/DB calls
            Order order = processOrder(cmd);
            span.setAttribute("order.id", order.id().toString());
            return order.id();
        } catch (Exception e) {
            span.recordException(e);
            span.setStatus(StatusCode.ERROR, e.getMessage());
            throw e;
        } finally {
            span.end();
        }
    }
}
```

```yaml
# application.yml — export traces to Jaeger/Tempo
management:
  tracing:
    sampling:
      probability: 0.1    # Sample 10% in production (100% is too much data)
  otlp:
    tracing:
      endpoint: http://jaeger-collector:4317
```

### Trace Context Propagation

```
HTTP Header: traceparent: 00-abc123-def456-01
             ├── version: 00
             ├── trace-id: abc123  (same across all services)
             ├── parent-span-id: def456
             └── flags: 01 (sampled)

Kafka Header: also carries trace context → async calls traceable end-to-end
```

### Correlation IDs in Logs

```java
// MDC (Mapped Diagnostic Context) — adds fields to every log line
@Component
public class TraceIdFilter implements Filter {
    public void doFilter(ServletRequest req, ServletResponse res, FilterChain chain) {
        String traceId = MDC.get("traceId");  // Set by OpenTelemetry auto-instrumentation
        if (traceId == null) {
            traceId = UUID.randomUUID().toString();
            MDC.put("traceId", traceId);
        }
        ((HttpServletResponse) res).setHeader("X-Trace-Id", traceId);
        try {
            chain.doFilter(req, res);
        } finally {
            MDC.clear();
        }
    }
}

// Log output (structured JSON):
{
  "timestamp": "2026-06-05T10:30:00Z",
  "level": "ERROR",
  "traceId": "abc-123",         ← same across all services for one request
  "spanId":  "def-456",
  "service": "order-service",
  "message": "Payment service timeout"
}
```

### Jaeger vs Zipkin vs AWS X-Ray

| Tool | Best For | Notes |
|---|---|---|
| **Jaeger** | Self-hosted, Kubernetes | Open source; rich UI; Uber-born |
| **Zipkin** | Simple self-hosted | Older; simpler; good for small teams |
| **AWS X-Ray** | AWS-native | No infra ops; integrates with CloudWatch |
| **Grafana Tempo** | Grafana ecosystem | Works with Prometheus + Loki stack |

---

## Topic 4 · Metrics — Prometheus + Grafana

### In One Line
Prometheus scrapes metrics from services; Grafana visualizes them — together they give you RED metrics, JVM health, and the data to back up SLO compliance.

### RED Method (for every service)

```
R — Rate:     requests per second
E — Errors:   error rate (5xx / total)
D — Duration: latency distribution (p50, p95, p99)
```

### Spring Boot Metrics (Micrometer)

```yaml
# application.yml
management:
  endpoints:
    web:
      exposure:
        include: health, info, prometheus, metrics
  metrics:
    tags:
      application: order-service
      environment: production
```

```java
// Custom business metrics
@Service
public class OrderService {

    private final Counter ordersPlaced;
    private final Counter ordersFailed;
    private final Timer orderPlacementLatency;

    public OrderService(MeterRegistry registry) {
        this.ordersPlaced = Counter.builder("orders.placed")
            .description("Total orders placed successfully")
            .register(registry);
        this.ordersFailed = Counter.builder("orders.failed")
            .tag("reason", "payment_declined")
            .register(registry);
        this.orderPlacementLatency = Timer.builder("orders.placement.duration")
            .description("Order placement end-to-end latency")
            .publishPercentiles(0.5, 0.95, 0.99)
            .register(registry);
    }

    public OrderId placeOrder(PlaceOrderCommand cmd) {
        return orderPlacementLatency.record(() -> {
            try {
                OrderId id = doPlaceOrder(cmd);
                ordersPlaced.increment();
                return id;
            } catch (PaymentDeclinedException e) {
                ordersFailed.increment();
                throw e;
            }
        });
    }
}
```

### Key Dashboards to Describe in Interviews

```
Service Dashboard (per microservice):
  ├── Request rate (RPS)
  ├── Error rate (%)
  ├── Latency: p50 / p95 / p99
  ├── JVM: heap used, GC pause time, threads
  ├── DB: connection pool utilization, query time
  └── Kafka: consumer lag per partition

Business Dashboard:
  ├── Orders placed per minute
  ├── Payment success rate
  ├── Revenue per hour
  └── Active users

SLO Dashboard:
  ├── Availability vs SLO (99.9% line)
  ├── Error budget remaining this month
  └── Latency SLO compliance
```

---

## Topic 5 · HA/DR — RTO/RPO Design

### In One Line
HA keeps you running during partial failures; DR gets you back after a catastrophic failure — RTO and RPO define how good your DR must be.

### Definitions

```
RTO (Recovery Time Objective):
  Maximum acceptable downtime after a disaster
  → "We must be back online within 4 hours"

RPO (Recovery Point Objective):
  Maximum acceptable data loss measured in time
  → "We can lose at most 1 hour of data"
  → If RPO = 1hr, backup/replication must happen at least every 1 hour

RTO ↓ = more expensive (hot standby vs cold backup)
RPO ↓ = more expensive (sync replication vs daily backup)
```

### HA Architecture — Multi-AZ

```
AWS ap-south-1 (Mumbai):
  VPC
  ├── AZ ap-south-1a:
  │   ├── EKS nodes (3 pods)
  │   ├── RDS Primary
  │   └── ElastiCache Primary
  └── AZ ap-south-1b:
      ├── EKS nodes (3 pods)       ← k8s scheduler spreads pods across AZs
      ├── RDS Standby (sync)       ← automatic failover in <60s on primary failure
      └── ElastiCache Replica

ALB routes traffic across both AZs.
If AZ-a goes down:
  → ALB stops routing to AZ-a pods (health check fails)
  → RDS auto-promotes standby in AZ-b → new primary
  → ElastiCache replica promoted
  → Total downtime: <2 minutes (RTO = 2 min for AZ failure)
```

### DR Tiers

| Tier | Strategy | RTO | RPO | Cost |
|---|---|---|---|---|
| **Backup & Restore** | Restore from S3 backup | Hours–days | Hours | Low |
| **Pilot Light** | Core infra running; app off | 1-4 hours | Minutes | Medium |
| **Warm Standby** | Scaled-down prod in DR region | 15-60 min | Seconds | High |
| **Hot Standby (Active-Active)** | Full capacity in both regions | Near-zero | Near-zero | Very High |

### Typical Design for "RTO 4hr / RPO 1hr" (Common Interview Scenario)

```
Primary Region: ap-south-1 (Mumbai)
DR Region:      ap-southeast-1 (Singapore)

Components:
  RDS: async replication to DR region (lag < 5 min usually; RPO ~ 5 min)
        → Meets RPO = 1hr comfortably
  Kafka: MirrorMaker 2 replicates topics to DR Kafka cluster
  S3: cross-region replication enabled
  EKS: Terraform + Helm charts stored in Git → spin up in DR in <2 hr
  DNS: Route53 failover policy; health check on primary ALB
       → If primary health check fails → Route53 points to DR ALB

Failover procedure:
  1. Alert fires: primary region unreachable
  2. Promote RDS read replica in DR to primary (5 min)
  3. Apply Terraform to spin up EKS nodes in DR (30 min)
  4. Deploy services via ArgoCD from Git (20 min)
  5. Update Route53 to DR ALB (manual or auto via Lambda)
  6. Smoke test
  Total: ~60 min → RTO = 1hr (well within 4hr target)

Data loss:
  RDS async lag: typically < 5 min → well within RPO = 1hr
```

### DR Testing — Must Mention in Interviews

```
Quarterly DR test:
  1. Simulate primary region failure (don't actually break prod)
  2. Execute failover runbook
  3. Measure actual RTO and RPO achieved
  4. Document gaps and fix

Chaos Engineering (Game Days):
  - Kill random pods → k8s reschedules; no user impact
  - Terminate AZ → traffic shifts; RDS failover; measure recovery
  - Slow Kafka → CB opens; fallback invoked
  - Tools: Chaos Monkey (Netflix), AWS Fault Injection Simulator
```

### Interview Q&A

**Q: Design HA/DR for a banking system with RTO 4hr and RPO 1hr.**
A: Multi-AZ for HA — RDS Multi-AZ with synchronous standby gives automatic failover in under 60 seconds for AZ failure; EKS pods spread across AZs behind ALB. For DR, active-passive across two AWS regions (Mumbai primary, Singapore DR). RDS async cross-region replica — lag typically under 5 minutes, well within 1-hour RPO. Kafka MirrorMaker 2 replicates topics. Infrastructure as code (Terraform + ArgoCD) so the DR environment can be stood up in under 2 hours following a runbook. Route53 failover routing with health checks triggers DNS cutover. Tested quarterly — we execute the runbook and measure actual RTO/RPO.

---

## Topic 6 · CAP Theorem / PACELC

### In One Line
CAP says distributed systems can only guarantee two of three properties during a network partition — every DB choice is implicitly a CAP tradeoff.

### CAP Theorem

```
C — Consistency:   Every read gets the most recent write (or an error)
A — Availability:  Every request gets a response (may not be latest data)
P — Partition Tolerance: System works despite network partitions

Rule: Network partitions WILL happen. You must choose C or A when they do.

CP systems (choose Consistency over Availability during partition):
  → Returns error rather than stale data
  → Examples: PostgreSQL (strong consistency), Zookeeper, HBase, MongoDB (default)

AP systems (choose Availability over Consistency during partition):
  → Returns stale data rather than error
  → Examples: Cassandra, DynamoDB (eventually consistent), CouchDB
```

### PACELC — Extended Model

```
CAP only describes behavior during Partition. PACELC adds normal operation:

If Partition: choose A or C (same as CAP)
Else (normal): choose Latency or Consistency

PA/EL: Cassandra — During partition: Available; Normally: Low latency (eventual consistency)
PC/EC: Google Spanner — During partition: Consistent; Normally: Consistent (higher latency)
PA/EC: MongoDB (default WC:majority) — During partition: Available; Normally: Consistent
```

### Consistency Models (Spectrum)

```
Strong Consistency ←──────────────────────────────────────→ Eventual Consistency

Linearizability    Sequential    Causal    Monotonic Read    Eventual
(strongest)        Consistency   Consistency                 (weakest)

Linearizability: reads always see latest write (PostgreSQL with sync replication)
Sequential: all nodes see same order of operations (not necessarily latest)
Causal: causally related operations seen in order (user sees their own writes)
Monotonic Read: once you see a value, you never see an older value
Eventual: eventually all nodes converge (Cassandra default)
```

### BASE vs ACID

| Property | ACID | BASE |
|---|---|---|
| Consistency | Strong — transaction leaves DB in valid state | Eventual — data converges eventually |
| Isolation | Transactions don't see each other's partial work | Soft state — data may be in flux |
| Durability | Committed = persisted | Best effort |
| Availability | May sacrifice availability for consistency | Prioritizes availability |
| Systems | PostgreSQL, MySQL, Oracle | Cassandra, DynamoDB, CouchDB |

### Practical Guidance for SA Interviews

```
Financial transactions (payments, ledger):  → ACID, strong consistency (PostgreSQL)
User profiles, preferences:                 → Eventual consistency OK (MongoDB, DynamoDB)
Shopping cart (per-user, isolated):         → Eventual OK; use versioning for conflicts
Inventory deduction (critical, must not oversell): → Strong consistency (PostgreSQL, optimistic lock)
Analytics, metrics aggregation:             → Eventual fine; small error acceptable
Session data:                              → Eventual OK; stale session = minor UX issue
```

### Interview Q&A

**Q: Explain CAP theorem. How does it influence your database choices?**
A: CAP says distributed systems can guarantee at most two of: Consistency (every read gets latest write), Availability (every request gets a response), and Partition Tolerance (system works through network failures). Since network partitions will happen in any distributed system, the real choice is between Consistency and Availability during a partition. For financial data — payments, balances, inventory — I choose CP: I'd rather return an error than stale or wrong data. For user preferences, session data, recommendations — AP is fine: returning slightly stale data is better than an error. This directly influences my DB choice: PostgreSQL for transactional data, Cassandra/DynamoDB for high-availability read-heavy data.

---

## Topic 7 · Performance Architecture

### In One Line
Performance is designed in, not tuned in at the end — the SA's job is to identify bottlenecks before they happen and build measurement in from day one.

### Performance Design Checklist

```
Query layer:
  ✅ Every query has an index on filter + sort columns
  ✅ N+1 queries eliminated (JOIN FETCH or @BatchSize)
  ✅ Pagination on all list endpoints (cursor-based for > 1M rows)
  ✅ Connection pool sized to DB max_connections ÷ number of service instances
  ✅ Read replicas for heavy read queries

Caching layer:
  ✅ Cache-aside for read-heavy, write-infrequent data
  ✅ Cache TTL defined (not "forever" — causes stale data)
  ✅ CDN for static assets and public API responses
  ✅ HTTP cache headers set (Cache-Control, ETag)

Application layer:
  ✅ Async for non-critical path (notifications, analytics via Kafka)
  ✅ Connection pool for HTTP clients (not new connection per request)
  ✅ CompletableFuture/reactive for parallel calls
  ✅ Response compression (gzip for JSON > 1KB)

JVM layer:
  ✅ Heap sized correctly (not default 256MB for a service under load)
  ✅ GC algorithm chosen (G1GC default; ZGC for latency-sensitive)
  ✅ Warm-up before load (JIT compilation)
```

### Load Testing Strategy

```
Tools: k6 (modern, JavaScript), Gatling (JVM, Scala DSL), Apache JMeter (GUI, legacy)

Test types:
  Smoke test:    1 user, 1 min → verify basic functionality
  Load test:     Expected load (e.g., 100 RPS) × 30 min → verify normal behaviour
  Stress test:   Ramp up until failure → find breaking point
  Soak test:     Expected load × 8 hours → find memory leaks, resource exhaustion
  Spike test:    Sudden 10x load → verify auto-scaling response

k6 example:
  import http from 'k6/http';
  import { check } from 'k6';

  export let options = {
    stages: [
      { duration: '2m', target: 50 },   // ramp up to 50 users
      { duration: '5m', target: 50 },   // stay at 50
      { duration: '2m', target: 100 },  // ramp to 100
      { duration: '5m', target: 100 },  // stay at 100
      { duration: '2m', target: 0 },    // ramp down
    ],
    thresholds: {
      http_req_duration: ['p99<500'],    // SLO: 99% < 500ms
      http_req_failed: ['rate<0.01'],    // < 1% errors
    },
  };

  export default function () {
    const res = http.post('https://api.company.com/orders', JSON.stringify({...}),
      { headers: { 'Content-Type': 'application/json' } });
    check(res, { 'status is 201': (r) => r.status === 201 });
  }
```

---

## Topic 8 · Scalability Architecture

### In One Line
Horizontal scaling (more instances) beats vertical (bigger instance) for microservices — but stateless design, sharding, and partitioning are prerequisites.

### Horizontal vs Vertical

| Dimension | Vertical (Scale Up) | Horizontal (Scale Out) |
|---|---|---|
| Method | Bigger CPU/RAM on same machine | More instances behind load balancer |
| Limit | Physical machine limits | Near-unlimited |
| Cost | Exponential at high end | Linear |
| Downtime | Usually requires restart | Rolling updates — no downtime |
| State | Easier (single machine) | Requires stateless services |
| **Use when** | DB servers (easier), quick fix | Microservices, stateless workloads |

### Stateless Design — Prerequisite for Horizontal Scale

```
STATEFUL (bad for scaling):
  Request 1 → Server A (stores session in memory)
  Request 2 → Load Balancer routes to Server B
  → Server B has no session → user logged out / error

STATELESS (scalable):
  Session stored in Redis (shared, external)
  Request 1 → Server A (reads session from Redis)
  Request 2 → Server B (reads same session from Redis)
  → Any server can handle any request
  → Add/remove servers freely

Rule: Never store request state in application memory.
  ✅ Redis for sessions
  ✅ JWT for auth (stateless token)
  ✅ Kafka for in-flight work state
  ✅ S3 for file uploads
```

### Sharding — Horizontal DB Scaling

```
Problem: Single PostgreSQL instance → ~10K writes/sec max → bottleneck at scale

Sharding: split data across multiple DB instances by a shard key

Example — shard orders by customerId % 4:
  Shard 0 (customer IDs where id % 4 = 0): Postgres instance 0
  Shard 1 (customer IDs where id % 4 = 1): Postgres instance 1
  Shard 2 (customer IDs where id % 4 = 2): Postgres instance 2
  Shard 3 (customer IDs where id % 4 = 3): Postgres instance 3

Order query for customerId=123:
  123 % 4 = 3 → route to Shard 3

Cross-shard query (all orders in status=PLACED):
  → Must query all 4 shards and merge → expensive
  → Design shard key to avoid cross-shard queries for hot paths
```

**Shard key selection:**
- High cardinality (many unique values)
- Even distribution (avoid hotspots)
- Matches your most frequent query pattern

**Consistent hashing:** Used when number of shards can change — minimizes data movement when adding/removing shards.

### Auto-Scaling

```
Kubernetes HPA (pod scaling):
  Scale when: avg CPU > 70% OR Kafka consumer lag > 10K messages
  Min replicas: 2 (HA baseline)
  Max replicas: 20 (cost cap)

Cluster Autoscaler (node scaling):
  Adds EC2 nodes when pods can't be scheduled (insufficient resources)
  Removes nodes when utilization is low (cost saving)

KEDA (Kubernetes Event-Driven Autoscaling):
  Scale based on Kafka consumer lag — more precise for event-driven services
  Scale to 0 for batch jobs when no messages in queue
```

---

## Day 9 Quick Reference

| Topic | Key Interview Answer |
|---|---|
| Circuit Breaker states | Closed → Open (failure threshold) → Half-Open (trial) → Closed/Open |
| Retry + CB order | TimeLimiter → Bulkhead → CircuitBreaker → Retry → call |
| Bulkhead | Separate thread pools per downstream; slow PaymentService can't starve InventoryService |
| SLI/SLO/SLA | SLI = measure; SLO = internal target; SLA = customer contract; SLO stricter than SLA |
| Error budget | 99.9% SLO = 43.2 min/month budget; burn fast → freeze risky deployments |
| Distributed tracing | OpenTelemetry → Jaeger/Tempo; trace ID propagated in HTTP headers and Kafka headers |
| Correlation IDs | MDC in Java; every log line has traceId; allows filtering single request across services |
| RTO vs RPO | RTO = how fast back; RPO = how much data loss; both drive architecture cost |
| DR tiers | Backup/Restore < Pilot Light < Warm Standby < Hot Standby; cost ∝ speed |
| CAP | Partition always happens; choose C (error on partition) or A (stale on partition) |
| ACID vs BASE | ACID = strong, transactional; BASE = eventual, available |
| Stateless design | Store session in Redis not in-process; prerequisite for horizontal scaling |
| Sharding | Split by shard key; choose key for even distribution + matches query pattern |

---

*Tags: #circuit-breaker #resilience4j #bulkhead #retry #SLO #SLI #error-budget #prometheus #grafana #distributed-tracing #opentelemetry #jaeger #HADR #RTO #RPO #CAP #PACELC #BASE #ACID #sharding #stateless #scalability*
