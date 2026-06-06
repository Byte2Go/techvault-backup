# Mock #1 — Java Microservices Platform: Web + Mobile + Kafka
**Type:** System Design Mock Interview (SA / Java Architect level)  
**Day in Plan:** Day 7  
**Time allowed:** 60 minutes  
**Scenario ID:** S1 (MUST PREP)

---

## The Question (As an Interviewer Would Ask It)

> "Design a backend platform for a mid-size e-commerce company. The platform must serve a React web app and an Android/iOS mobile app. Core flows: product catalog, user accounts, order placement, payment processing, and order notifications. The system must handle 50,000 orders per day with peak load of 500 orders per minute. You have a team of 20 engineers across 4 squads. Walk me through your architecture."

---

## How to Structure Your 60 Minutes

```
0-5 min   → Clarify requirements (never jump to design immediately)
5-15 min  → Establish NFRs and constraints
15-35 min → Core architecture design (draw as you talk)
35-50 min → Deep dive on 2-3 components (interviewer will probe)
50-60 min → Tradeoffs, what you'd do differently, open issues
```

---

## Step 1: Clarify First (0–5 min)

Always ask these before drawing anything:

**Functional:**
- "Is payment processed in-house or via a gateway like Razorpay/Stripe?"
- "Do we need real-time order tracking or is eventual notification acceptable?"
- "Is the product catalog read-heavy? Any seller-side write flows?"
- "Do mobile and web need different data? (Determines BFF need)"

**Non-Functional:**
- "50K orders/day — what's the read-to-write ratio? Catalog browsing vs ordering?"
- "What's the availability target? Five nines (99.999%) or 99.9%?"
- "Any compliance — PCI-DSS for payments? Data residency?"
- "Is this greenfield or migrating an existing monolith?"

**Assume (state your assumptions clearly):**
- Payment via Razorpay (no PCI card data in our system)
- 99.9% availability target (43 min downtime/month acceptable)
- Read:Write ratio ~ 100:1 (catalog heavy read, orders are writes)
- Greenfield — no legacy migration
- AWS as cloud provider
- Indian market — data in ap-south-1 (Mumbai)

---

## Step 2: NFRs & Scale Estimates (5–15 min)

### Scale Calculations (show your math — interviewers love this)

```
Orders:
  50,000 orders/day = ~35 orders/min average
  Peak: 500 orders/min = 8-9 orders/second
  → Order Service: needs to handle ~10 TPS peak (comfortable with 3 instances)

Catalog:
  100:1 read:write ratio → 500 catalog reads/min at peak (but catalog = popular pages)
  Realistic catalog: 5,000-10,000 concurrent users browsing
  → Cache-heavy; most reads never hit DB

Notifications:
  50K orders/day → 50K notification events/day → ~0.6 events/second
  → Kafka partition can handle this trivially

Data volume:
  Order: ~2KB avg → 50K/day → 100MB/day → ~36GB/year
  → PostgreSQL handles this easily for years
  
  Product catalog: 100K products × 10KB avg = 1GB → fits in ElasticSearch + Redis
```

### NFR Table

| NFR | Target | Architecture Implication |
|---|---|---|
| Availability | 99.9% | Multi-AZ deployment; no single point of failure |
| Order placement latency | p99 < 500ms | Async Kafka for notifications; sync only for critical path |
| Catalog read latency | p99 < 100ms | Redis caching; CloudFront CDN for images |
| RTO | 4 hours | Active-passive DR; automated failover |
| RPO | 1 hour | RDS Multi-AZ + automated backups |
| Security | OAuth2 + JWT | Keycloak auth server; API Gateway validation |

---

## Step 3: Service Decomposition (15–20 min)

### Identify Bounded Contexts (DDD approach — say this out loud)

> "I start with business capabilities, then validate against DDD bounded contexts. The key test: can each service be owned by one team and deployed independently?"

```
Squad 1 — Catalog & Discovery:
  └── ProductCatalogService    (CRUD products, search, categories)

Squad 2 — User & Identity:
  └── UserService              (registration, profiles, addresses)
  └── AuthService              (OAuth2/OIDC via Keycloak)

Squad 3 — Order & Payments:
  └── OrderService             (place order, order lifecycle)
  └── InventoryService         (stock management, reservations)
  └── PaymentService           (Razorpay integration, payment records)

Squad 4 — Fulfillment & Comms:
  └── ShippingService          (shipment creation, tracking)
  └── NotificationService      (email/SMS/push — consumes events from Kafka)
```

**Conway's Law alignment:** 4 squads → 4 domain clusters → independent deployability.

---

## Step 4: Full Architecture (20–35 min)

### Draw This (ASCII version for reference)

```
                            INTERNET
                               │
                    ┌──────────┴──────────┐
                    │   CloudFront (CDN)   │  ← Static assets, cacheable API responses
                    └──────────┬──────────┘
                               │
                    ┌──────────┴──────────┐
                    │   AWS WAF + Shield   │  ← DDoS, OWASP Top 10 rules
                    └──────────┬──────────┘
                               │
               ┌───────────────┴───────────────┐
               │         API Gateway (Kong)     │  ← Auth (JWT validation), Rate limiting,
               │                               │    Routing, SSL termination, Logging
               └──────┬──────────────┬─────────┘
                      │              │
             ┌────────┴───┐    ┌─────┴──────┐
             │  Web BFF   │    │ Mobile BFF │   ← Separate BFF per client type
             │ (Node.js)  │    │  (Node.js) │     Web BFF: rich data, pagination
             └────────┬───┘    └─────┬──────┘     Mobile BFF: lightweight, push-notif
                      │              │
                      └──────┬───────┘
                             │ (internal REST / gRPC)
        ┌──────────┬─────────┼──────────┬──────────┐
        │          │         │          │          │
  ┌─────┴──┐ ┌────┴───┐ ┌───┴────┐ ┌───┴──┐ ┌────┴──────┐
  │Catalog │ │  User  │ │ Order  │ │Inven-│ │ Payment   │
  │Service │ │Service │ │Service │ │tory  │ │ Service   │
  │(Java)  │ │(Java)  │ │(Java)  │ │(Java)│ │ (Java)    │
  └────┬───┘ └────┬───┘ └───┬────┘ └───┬──┘ └────┬──────┘
       │          │         │          │          │
  ┌────┴──┐  ┌────┴──┐ ┌────┴──┐  ┌────┴──┐ ┌────┴──┐
  │Elastic│  │Postgres│ │Postgres│  │Postgres│ │Postgres│
  │Search │  │ (User)│ │(Order)│  │(Invent)│ │(Paymnt)│
  │+Redis │  └───────┘ └───┬───┘  └───────┘ └───────┘
  └───────┘                │
                           │ Publishes domain events
                    ┌──────┴──────────────────────────┐
                    │         Apache Kafka             │
                    │  Topics:                         │
                    │  order-events                    │
                    │  payment-events                  │
                    │  inventory-events                │
                    │  notification-commands           │
                    └──────┬──────────────────────────┘
                           │
               ┌───────────┼───────────┐
               │           │           │
        ┌──────┴───┐  ┌────┴────┐  ┌───┴──────────┐
        │Shipping  │  │Analytics│  │Notification  │
        │Service   │  │Service  │  │Service       │
        │(Java)    │  │(Python) │  │(Java)        │
        └──────────┘  └─────────┘  └──────────────┘
                                          │
                              ┌───────────┼───────────┐
                              │           │           │
                           Email        SMS         Push
                         (SES)      (Twilio)    (FCM/APNS)
```

### Infrastructure Layer

```
AWS ap-south-1 (Mumbai):
├── VPC
│   ├── Public Subnets (AZ-a, AZ-b)  → ALB, NAT Gateway
│   ├── Private Subnets (AZ-a, AZ-b) → EKS nodes, BFFs, Microservices
│   └── DB Subnets (AZ-a, AZ-b)      → RDS (Multi-AZ), ElastiCache
│
├── EKS Cluster (Kubernetes)
│   ├── Services deployed as k8s Deployments
│   ├── HPA on Order/Payment services (scale on CPU + custom Kafka lag metric)
│   └── Istio service mesh (mTLS east-west, circuit breaking)
│
├── Managed services:
│   ├── Amazon RDS PostgreSQL (Multi-AZ) — per service DB
│   ├── Amazon ElastiCache (Redis) — session, catalog cache
│   ├── Amazon MSK (managed Kafka) — or self-hosted on EKS
│   ├── Amazon Elasticsearch Service — product search
│   └── Amazon ECR — container registry
│
└── CI/CD: GitHub Actions → ECR → ArgoCD → EKS
```

---

## Step 5: Order Placement Flow (Deep Dive — 35–45 min)

### Interviewer will ask: "Walk me through what happens when a user places an order"

```
1. Mobile App → POST /orders (via Mobile BFF → API Gateway)

2. API Gateway:
   → Validates JWT (signature, expiry, audience)
   → Rate limits (per user: 10 orders/min)
   → Routes to Order Service

3. Order Service (synchronous critical path):
   a. Load customer (UserService via REST call, or cached)
   b. BEGIN transaction
   c. Validate cart items (InventoryService — gRPC for speed)
      → InventoryService: soft-reserve stock (reduce available, not committed)
   d. Create Order (status: PENDING_PAYMENT) in OrderDB
   e. Call PaymentService → Razorpay charge via REST
      → On success: Order status = PLACED, inventory = COMMITTED
      → On failure: Order status = FAILED, inventory reservation released
   f. COMMIT transaction
   g. Publish OrderPlaced event to Kafka

4. Kafka consumers (async — after response sent to user):
   → ShippingService: creates shipment record
   → NotificationService: sends order confirmation email + push notification
   → AnalyticsService: records order event for reporting

5. Response to user:
   HTTP 201 Created { "orderId": "ord-xxx", "status": "PLACED", "estimatedDelivery": "..." }
   → Returned after step 3f; Kafka publishing is fire-and-forget from user's perspective
```

### Why This Design?

> "I keep the synchronous critical path minimal — only what the user must wait for: auth check, inventory validation, payment, and order creation. Everything downstream (notifications, shipping, analytics) is async via Kafka. This keeps p99 latency low and makes the system resilient — if NotificationService is down, orders still succeed."

### Saga for Payment Failure

```
Payment fails at Razorpay:
→ PaymentService returns failure
→ OrderService: release inventory reservation (InventoryService call)
→ OrderService: mark order FAILED
→ Publish OrderFailed event to Kafka
→ NotificationService: send "payment failed" notification

This is a 2-step saga (inventory + payment) — simple enough for orchestration
within OrderService without a dedicated saga orchestrator.
```

---

## Step 6: Key Architecture Decisions & Justifications

### Decision 1: BFF over single API
> "Mobile needs lightweight payloads and push notification support. Web needs rich filtering, sorting, server-side rendering hints. A shared API either over-fetches on mobile or under-serves web. Each BFF is owned by its frontend team — they evolve independently. Both BFFs call the same underlying microservices."

### Decision 2: Kafka over direct REST for downstream
> "If I wired ShippingService and NotificationService directly into the order placement flow, a NotificationService outage would fail orders. Kafka decouples them — OrderService publishes an event and returns. Consumers process asynchronously. The event is durable — if NotificationService restarts after 2 minutes, it processes all missed events from its last committed offset."

### Decision 3: Database per service
> "Each service owns its schema. ProductCatalogService uses Elasticsearch (search-optimized). OrderService uses PostgreSQL (ACID transactions). NotificationService could use DynamoDB (high-write, simple schema). No cross-service joins — data aggregation via API composition in BFFs or via Kafka projections."

### Decision 4: Razorpay for payments, not in-house
> "Building PCI-compliant card processing in-house requires enormous security investment — penetration testing, audits, HSMs. Razorpay handles card data; we store only payment tokens. Our PCI scope drops to SAQ-A. Speed to market and risk reduction > the flexibility of in-house processing."

### Decision 5: EKS over ECS Fargate
> "20 engineers, 4 squads — the team has the operational maturity for Kubernetes. We need Istio for mTLS between services (compliance requirement). We want Helm for per-environment config management. EKS gives us these; ECS Fargate doesn't without complexity. For a smaller team I'd recommend ECS Fargate."

---

## Step 7: What You'd Do Differently / Open Issues

> These show maturity — interviewers love when you flag what's not solved.

**What I'd validate before committing:**
- "The MSK vs self-hosted Kafka decision needs a cost analysis — MSK is 3-4x more expensive than self-hosted on EKS, but operational burden for Kafka is high. For 50K orders/day, MSK is worth it."
- "I'd do a load test before launch — 500 orders/min is modest, but inventory reservation under peak concurrency needs validation."

**What I'd add at scale:**
- "At 10x this load, I'd add a separate read replica for OrderService (read-heavy order history queries)."
- "Rate limiting is at API Gateway level, but I'd add application-level idempotency keys for order placement — network retries from mobile apps can create duplicate orders."
- "Catalog caching strategy needs definition — Redis TTL, cache invalidation on price/stock changes."

---

## Interviewer Follow-Up Questions (Prepare These)

**Q: "Your OrderService calls InventoryService synchronously. What happens if Inventory is slow?"**
A: Timeout + circuit breaker (Resilience4j). Order Service configures: 200ms timeout for Inventory call. If Inventory exceeds 200ms → timeout exception → circuit breaker opens after 5 consecutive failures → subsequent calls fail fast (don't wait 200ms each). Fall back to: reject the order with "service temporarily unavailable" rather than hanging. Inventory team gets alerted via Kafka consumer lag metrics. I'd also push to make inventory check async in v2 — accept order optimistically, compensate if stock isn't available.

**Q: "How do you handle duplicate order submissions — user clicks twice on mobile?"**
A: Idempotency key. Mobile app generates a UUID per order attempt and sends it as a header (`Idempotency-Key: uuid-abc`). Order Service checks Redis: has this key been processed? If yes, return the cached response (same orderId, no new order created). If no, process and cache the result with a 24-hour TTL. This makes double-click, network retry, and app restart safe.

**Q: "50K orders is current. How does your design scale to 5M orders/day?"**
A: Horizontal scaling is built in — Kubernetes HPA scales OrderService pods on CPU/Kafka consumer lag. The DB becomes the bottleneck first: I'd add read replicas for reporting queries, partition the orders table by date, and consider sharding by customerId at ~500K orders/day. Kafka partitions would increase (currently adequate at 50K; at 5M I'd revisit partition count and consumer group sizing). The BFF layer is stateless — scales linearly. The main architectural change at 5M: separate the read model (CQRS) — heavy order history queries move to an Elasticsearch projection rather than hitting the primary DB.

**Q: "How do you deploy a new version of OrderService with zero downtime?"**
A: Rolling update in Kubernetes — `maxUnavailable: 0`, `maxSurge: 1`. New pod starts, readiness probe passes (/actuator/health/readiness), then old pod terminates. Combine with a `preStop` hook (sleep 5s) to drain in-flight requests before shutdown. For riskier releases, canary deployment via Argo Rollouts — 10% traffic to new version, monitor error rate and p99 latency for 10 minutes, then 100%. Automated rollback triggers if error rate exceeds 0.1%.

**Q: "Walk me through your monitoring strategy."**
A: Three pillars. Metrics: Prometheus scraping all services (JVM heap, GC, request rate, error rate, Kafka consumer lag), Grafana dashboards per service, PagerDuty alert if Order placement error rate > 0.1% or consumer lag > 10K. Logs: structured JSON logging with correlation IDs, shipped to CloudWatch Logs, indexed in OpenSearch for searching. Traces: OpenTelemetry SDK in every service, traces sent to Jaeger — I can trace a single order request across all 5 services it touches. SLO: 99.9% of order placement requests complete in under 500ms, measured via Prometheus.

---

## Scoring Rubric — Self-Assessment After Practice

Score yourself 1-5 on each dimension:

| Dimension | What Good Looks Like | Your Score |
|---|---|---|
| **Requirements** | Asked 3-5 clarifying questions; stated assumptions explicitly | /5 |
| **Scale math** | Did back-of-envelope for TPS, storage, bandwidth | /5 |
| **Service decomposition** | Justified boundaries with DDD/Conway's Law | /5 |
| **Architecture diagram** | Drew complete diagram with all components | /5 |
| **Critical path** | Explained sync vs async split and why | /5 |
| **Data layer** | Different DB per service, justified each | /5 |
| **Resilience** | Mentioned circuit breaker, DLQ, idempotency | /5 |
| **Deployment** | Mentioned CI/CD, zero-downtime, rollback | /5 |
| **Tradeoffs** | Proactively called out what you'd do differently | /5 |
| **Follow-ups** | Answered deep-dives without hesitation | /5 |

**Target score:** 40+/50 before walking into interviews.

---

## What Impresses at 40L Level

✅ Open with clarifying questions — never assume  
✅ State assumptions explicitly ("I'll assume Razorpay for payments")  
✅ Do back-of-envelope math out loud  
✅ Name patterns by name: "BFF pattern", "Strangler Fig", "Circuit Breaker", "Saga"  
✅ Justify every major decision with a tradeoff  
✅ Proactively mention what you haven't solved  
✅ Reference Conway's Law when explaining service boundaries  
✅ Distinguish sync (critical path) from async (Kafka) and explain why  
✅ Mention idempotency for order placement without being asked  
✅ Bring up compliance (PCI tokenization, data residency) if it's a fintech context  

## What Kills Candidates at This Level

❌ Jump to drawing boxes without clarifying  
❌ Single monolith DB for all services  
❌ No mention of caching (every read-heavy system needs it)  
❌ Kafka for everything including 2-entity sync calls  
❌ No mention of failure handling — what if PaymentService is down?  
❌ "I'd use microservices because they're better" — no justification  
❌ Ignoring mobile vs web differences (no BFF)  
❌ No NFRs / no scale estimate  

---

*Tags: #mock-interview #system-design #S1 #microservices #BFF #kafka #order-service #EKS #saga #40L*
