# P8 · Day 11 — On-Prem→Cloud · Mainframe→Java · B2B API · Third-Party Integration
**Pillar:** P8 — Integration & Migration (continued)  
**Role Priority:** SA 🔵 Core · Java 🟢 Supporting · AI ⚪ Supporting  
**Day in Plan:** Day 11 (Week 2)  
**Scenarios covered:** S4, S5, S7 (HIGH SIGNAL)

---

## Topic 1 · On-Premises → Cloud Migration (6 Rs Framework)

### In One Line
The 6 Rs give you a vocabulary to classify every workload in a migration portfolio — and interviewers expect you to apply them, not just list them.

### The 6 Rs

| Strategy | Also Called | What It Means | When To Use |
|---|---|---|---|
| **Rehost** | Lift & Shift | Move VM as-is to cloud (EC2) | Fast migration, no refactoring budget, early wins |
| **Replatform** | Lift & Reshape | Minor optimisations without changing core (move DB to RDS, app to ECS) | Moderate effort; gain managed services |
| **Repurchase** | Drop & Shop | Replace with SaaS (move CRM to Salesforce, email to SendGrid) | Commodity functions; not core business |
| **Refactor** | Re-architect | Redesign for cloud-native (microservices, serverless, Kafka) | Core differentiating workloads; high value |
| **Retain** | Revisit | Keep on-prem for now | Compliance, recently upgraded, not yet a priority |
| **Retire** | — | Decommission — it's not used | Reduces migration scope |

### Applying the 6 Rs to a Portfolio

```
Workload Assessment:
  ┌────────────────────────────────────────────────────────┐
  │  App           │  Strategy    │  Why                   │
  ├────────────────┼──────────────┼────────────────────────┤
  │  Legacy CRM    │  Repurchase  │  Salesforce does it better │
  │  Oracle DB     │  Replatform  │  Move to RDS Aurora     │
  │  Old reports   │  Retire      │  No one uses them       │
  │  Core banking  │  Retain      │  Regulatory review needed │
  │  Java monolith │  Rehost →    │  Lift first, refactor later│
  │                │  Refactor    │                        │
  │  Batch ETL     │  Replatform  │  Move to AWS Glue       │
  └────────────────┴──────────────┴────────────────────────┘
```

### Migration Waves — How to Phase the Work

```
Wave 1 (Months 1-3) — Quick wins, low risk:
  → Retire unused apps (reduce scope)
  → Repurchase commodity tools
  → Rehost dev/test environments first (low impact, learn the tooling)

Wave 2 (Months 4-9) — Core rehost:
  → Rehost production apps (lift & shift)
  → Replatform DB to RDS (managed backups, Multi-AZ, no patching)
  → Establish connectivity: Direct Connect or VPN to on-prem

Wave 3 (Months 10-18) — Optimise:
  → Refactor monolith (Strangler Fig — from Day 10)
  → Right-size EC2 instances (Compute Optimizer)
  → Adopt managed services (SQS, SNS, Elasticache)
  → Decommission on-prem hardware

Wave 4 (Ongoing) — Cloud native:
  → ECS/EKS, auto-scaling, GitOps, FinOps practices
```

### Hybrid Connectivity — On-Prem to AWS

```
Option 1: AWS Site-to-Site VPN
  On-prem router ←→ AWS VPN Gateway ←→ VPC
  Bandwidth: up to 1.25 Gbps per tunnel
  Latency: internet-based; variable
  Cost: low
  Use: dev/test, lower bandwidth needs, fast to set up

Option 2: AWS Direct Connect
  On-prem DC ←→ AWS Direct Connect location ←→ AWS VPC
  Bandwidth: 1 Gbps, 10 Gbps, 100 Gbps
  Latency: consistent, low (private fibre)
  Cost: higher (port fees + partner fees)
  Use: production, large data transfers, compliance (data never crosses internet)

Architecture during hybrid phase:
  On-prem services → Direct Connect → VPC → AWS services
  Split: new services in AWS; legacy stays on-prem; they communicate via DC
```

### AWS Migration Services

| Service | Purpose |
|---|---|
| **AWS Application Migration Service (MGN)** | Rehost — continuous block-level replication from on-prem to EC2 |
| **AWS Database Migration Service (DMS)** | Migrate DB to RDS; supports heterogeneous (Oracle → PostgreSQL) |
| **AWS Schema Conversion Tool (SCT)** | Convert Oracle/SQL Server schema to PostgreSQL/Aurora schema |
| **AWS DataSync** | Move large datasets (NFS, SMB shares) to S3/EFS |
| **AWS Snow family** | Physical data transfer — Snowball (80TB), Snowmobile (100PB) |

### Interview Q&A

**Q: A company wants to migrate 50 on-prem Java apps to AWS in 18 months. How do you approach it?**
A: Start with a discovery and assessment — inventory all 50 apps, map dependencies, classify each using the 6 Rs. Typically 10-20% get retired (unused), 10-15% get repurchased (commodity), leaving ~30 apps to actually migrate. Phase into waves: Wave 1 rehost dev/test environments (learn tooling, no production risk). Wave 2 rehost production (lift & shift to EC2) while replatforming databases to RDS — gets us off on-prem hardware fast. Wave 3 refactor differentiating apps to cloud-native (ECS/EKS, managed services). Establish Direct Connect early for production hybrid connectivity. The goal: decommission on-prem data centre by month 18 while apps continue running throughout.

---

## Topic 2 · Mainframe → Java Migration

### In One Line
Mainframe-to-Java migration is one of the highest-stakes migrations in enterprise — the patterns are coexistence, data synchronisation, and incremental extraction, never a big bang rewrite.

### Why Mainframes Persist (Understand the Context)

```
Mainframes (IBM z/OS, COBOL-based) are NOT obsolete:
  → Run 95% of ATM transactions, 80% of in-person credit card transactions globally
  → Process billions of transactions/day reliably
  → 30-50 year old business logic baked in — no one fully understands it
  → Rewriting them risks destroying business logic that exists only in code

The real goal: expose mainframe capabilities via modern APIs, 
  gradually extract modules, retain what works
```

### Migration Strategies

**Strategy 1 — API Façade (Expose Without Replacing)**
```
Mainframe COBOL program → MQ (IBM MQ / WebSphere) → Java Adapter Service → REST API
                                                              ↑
                                        modern microservices call this API

This is NOT migration — it's wrapping.
Benefit: modern services can consume mainframe capabilities without touching COBOL
Timeline: fastest; weeks to implement
Risk: lowest — mainframe still runs
Use when: need to expose capabilities quickly; full migration not yet approved
```

**Strategy 2 — Strangler Fig for Mainframe**
```
Phase 1: API Facade in front of mainframe
Phase 2: Extract batch jobs to Java (start with non-critical batch)
Phase 3: Extract reporting (read from mainframe DB replica, generate reports in Java)
Phase 4: Extract one business function at a time (loans, accounts, payments)
         → Java service handles new transactions
         → Mainframe handles existing/in-flight transactions
         → Dual-write synchronises both
Phase 5: Mainframe handles only legacy data; Java handles all new business
Phase 6: Historical data migrated; mainframe decommissioned

Timeline: 3-7 years for full mainframe retirement (not months)
```

**Strategy 3 — COBOL to Java Transpilation**
```
Automated tools (Micro Focus, AWS Blu Age) convert COBOL to Java
Pros: preserves logic; faster than manual rewrite
Cons: generated Java is unreadable; business logic still opaque; hard to maintain
Use when: need to get off COBOL quickly; team will refactor generated code over time
```

### Data Coexistence — The Hard Problem

```
Mainframe DB (VSAM files, DB2 z/OS) ↔ Java Service DB (PostgreSQL)

Problem: same data in two places → how to keep in sync?

Approach 1 — Mainframe as master:
  All writes → Mainframe DB
  Java reads → via MQ/API call to mainframe OR via DB2 z/OS replication to PostgreSQL
  → Mainframe is always source of truth
  → Java can only read, not write

Approach 2 — Dual write (same as Day 10):
  During migration window, both systems write to both DBs
  Reconciliation job validates consistency nightly
  Discrepancies → alert → manual resolution

Approach 3 — Event-based sync:
  Mainframe → IBM MQ → Java Adapter → Kafka → downstream services
  → Mainframe publishes events on each state change
  → Java services consume and update their own DB
  → Eventual consistency; Java DB is read replica of mainframe state
```

### Batch Job Migration

```
Mainframe batch jobs (JCL scripts) run nightly:
  → Account reconciliation
  → Interest calculation
  → Statement generation

Migration approach:
  1. Map JCL job → Java equivalent (Spring Batch)
  2. Run BOTH in parallel for 2-3 months; compare output
  3. If outputs match → switch to Java batch; retire JCL job
  4. Spring Batch runs on AWS Batch or EKS CronJob

Spring Batch structure:
  Job → Step1 (read accounts from DB) → Step2 (calculate interest) → Step3 (write results)
  ItemReader → ItemProcessor → ItemWriter
  Supports restart from checkpoint if job fails mid-run
```

### Interview Q&A

**Q: How would you approach migrating a mainframe banking system to cloud-native Java?**
A: Never a big bang rewrite — mainframes run logic no one fully understands, and rewriting everything simultaneously risks destroying decades of battle-tested business rules. My approach: Phase 1 — API Façade: wrap mainframe with Java adapter services exposing REST APIs, so new digital channels (mobile, web) can consume mainframe capabilities without touching COBOL. Phase 2 — Strangler Fig: extract one domain at a time starting with batch reporting (lowest risk), then new-customer onboarding (clean slate, no historical data), then existing account management (hardest — years of transaction history). Phase 3 — Data coexistence: dual-write with nightly reconciliation jobs comparing mainframe and Java DB. Full retirement in 3-5 years, not 6 months. The goal isn't to kill the mainframe — it's to progressively reduce dependency on it.

---

## Topic 3 · B2B API Integration — Partner Onboarding

### In One Line
B2B API integration requires a partner-facing API tier with OAuth2 client credentials, rate limiting, versioning, and a developer portal — it's a product, not just an endpoint.

### Architecture

```
Partner / Third-Party App
        │
        │ HTTPS + OAuth2 Client Credentials
        ↓
  ┌─────────────────────────────────────────┐
  │         B2B API Gateway (Kong)          │
  │  • OAuth2 token validation              │
  │  • Rate limiting (per partner API key)  │
  │  • Request/response logging (audit)     │
  │  • API versioning routing               │
  │  • Throttling per SLA tier              │
  └────────────────┬────────────────────────┘
                   │
  ┌────────────────┴────────────────────────┐
  │          Partner API Service            │
  │  • Partner-specific data shaping        │
  │  • Translates partner request →         │
  │    internal domain objects              │
  │  • Anti-Corruption Layer (ACL)          │
  │  • Partner context enrichment           │
  └────────────────┬────────────────────────┘
                   │
         Internal microservices
  (OrderService, InventoryService, etc.)
```

### Partner Authentication — Client Credentials Flow

```
1. Partner registers: receives client_id + client_secret (stored securely by partner)

2. Partner requests token:
   POST /oauth/token
   grant_type=client_credentials
   client_id=partner-xyz
   client_secret=<secret>
   scope=orders:read inventory:read

3. Auth Server returns:
   { "access_token": "jwt...", "expires_in": 3600, "token_type": "Bearer" }

4. Partner calls API:
   GET /api/v1/orders?status=PLACED
   Authorization: Bearer <access_token>

5. API Gateway validates JWT (signature, expiry, scope) before forwarding
```

### Rate Limiting — SLA Tiers

```
Partner Tier     | Requests/min | Requests/day | Burst
─────────────────|──────────────|──────────────|──────
Standard         | 60           | 10,000       | 100
Premium          | 300          | 100,000      | 500
Enterprise       | 1,000        | unlimited    | 2,000

Implementation (Kong):
  - Rate limit plugin applied per consumer (partner)
  - Exceeds → HTTP 429 Too Many Requests
  - Response headers:
      X-RateLimit-Limit-Minute: 60
      X-RateLimit-Remaining-Minute: 45
      X-RateLimit-Reset: 1749999999
```

### Developer Portal

```
What a partner developer portal provides:
  ├── API documentation (auto-generated from OpenAPI spec)
  ├── Interactive API explorer (try it now — Swagger UI / Redoc)
  ├── Sandbox environment (test without affecting production)
  ├── API key management (create, rotate, revoke keys)
  ├── Usage analytics (how many calls, error rates, latency)
  ├── Webhook management (register endpoints for event callbacks)
  └── Changelog + deprecation notices

Tools: AWS API Gateway Developer Portal, Kong Dev Portal, Apigee, readme.io
```

### Webhook Design (Push-Based Partner Integration)

```
Instead of partner polling every 5 minutes:
  → Your system pushes events to partner's registered endpoint

Webhook flow:
  Event: OrderShipped → publish to Kafka
  Webhook Service consumes → POST to partner URL:
  {
    "eventType": "ORDER_SHIPPED",
    "eventId": "evt-abc-123",           ← idempotency
    "partnerId": "partner-xyz",
    "occurredAt": "2026-06-05T10:30:00Z",
    "data": { "orderId": "ord-456", "trackingNumber": "TN789" }
  }
  Headers: X-Signature: HMAC-SHA256(payload, partnerSecret)  ← auth

Partner verifies:
  1. Compute HMAC of received payload using known shared secret
  2. Compare with X-Signature header → prevents spoofing
  3. Check eventId in deduplication store → idempotent processing
  4. Return HTTP 200 → webhook service marks delivery successful
  5. If 4xx/5xx → retry with exponential backoff (3 attempts)
  6. After 3 failures → DLQ + alert partner team
```

### Interview Q&A

**Q: Design a B2B API platform for third-party partners.**
A: Three layers. First, authentication — OAuth2 Client Credentials flow; each partner gets a client ID and secret; tokens are short-lived JWTs scoped to specific resources. Second, the API Gateway tier — rate limiting per partner SLA tier (Standard/Premium/Enterprise), request/response audit logging, API version routing, and SSL termination. Third, a Partner API service that acts as an Anti-Corruption Layer — translates partner request schemas to internal domain objects, enriches with partner context, and shields internal services from partner-specific concerns. Complemented by a developer portal for self-service onboarding, documentation, sandbox, and webhook management. Webhooks replace polling for event-driven partners — push on state change, HMAC-signed, idempotent.

---

## Topic 4 · API Exposure to Third Parties — Developer Portal Architecture

### Managing API Versions for External Consumers

```
External APIs must be versioned strictly — you can't break a partner's integration:

URI versioning (recommended for external):
  /api/v1/orders  → v1 consumers (supported for 12-24 months after v2 launch)
  /api/v2/orders  → v2 consumers (adds new fields, changes structure)

Deprecation lifecycle:
  1. Launch v2
  2. Announce v1 deprecation (email, developer portal banner, Sunset header)
  3. Sunset header on v1 responses: Sunset: Sat, 01 Jan 2027 00:00:00 GMT
  4. Monitor: how many partners still use v1? (per-partner API key metrics)
  5. Contact non-migrated partners 60 days before end-of-life
  6. Retire v1 after sunset date

Rule: Never remove a v1 endpoint without:
  → 6-12 month deprecation notice
  → Zero active consumers (or explicit partner sign-off)
```

### API Contract Documentation — OpenAPI

```yaml
# openapi.yaml
openapi: 3.0.3
info:
  title: Company Partner API
  version: 2.0.0
  description: |
    B2B API for order management and inventory access.
    Rate limits: Standard 60/min, Premium 300/min.

paths:
  /orders:
    get:
      summary: List orders
      security:
        - OAuth2: [orders:read]
      parameters:
        - name: status
          in: query
          schema:
            type: string
            enum: [PLACED, SHIPPED, DELIVERED, CANCELLED]
        - name: cursor
          in: query
          description: Pagination cursor from previous response
          schema:
            type: string
      responses:
        '200':
          description: Paginated list of orders
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/OrderListResponse'
        '429':
          description: Rate limit exceeded
          headers:
            Retry-After:
              schema:
                type: integer
              description: Seconds until rate limit resets
```

---

## Topic 5 · Third-Party API Consumption — Adapter Pattern & ACL

### In One Line
When consuming external APIs (payment gateways, logistics, CRM), wrap them in an Anti-Corruption Layer — your domain stays clean regardless of how the third party changes its API.

### The Problem Without ACL

```
Order Service directly calls Razorpay API:
  RazorpayClient.createOrder(razorpayOrderRequest)
  razorpayResponse.getPaymentId()
  razorpayResponse.getRazorpayOrderId()

Razorpay changes their API (v2 → v3):
  → All of this code changes
  → Business logic entangled with external API shape
  → Every Razorpay field name leaks into your domain model
```

### Anti-Corruption Layer (ACL) Pattern

```java
// Domain port — your domain defines what IT needs
public interface PaymentGateway {
    PaymentResult charge(Money amount, PaymentMethod method, String idempotencyKey);
    RefundResult refund(String paymentId, Money amount);
    PaymentStatus getStatus(String paymentId);
}

// Domain model — your language
public record PaymentResult(
    String paymentId,          // your ID, not Razorpay's
    PaymentStatus status,
    Money amount,
    Instant processedAt
) {}

// ACL — Razorpay adapter (infrastructure layer)
@Component
public class RazorpayPaymentGateway implements PaymentGateway {

    private final RazorpayClient razorpayClient;

    @Override
    public PaymentResult charge(Money amount, PaymentMethod method, String idempotencyKey) {
        // Translate domain request → Razorpay request
        JSONObject razorpayOrder = new JSONObject();
        razorpayOrder.put("amount", amount.inPaise());         // Razorpay uses paise
        razorpayOrder.put("currency", amount.currency());
        razorpayOrder.put("receipt", idempotencyKey);

        Order razorpayResponse = razorpayClient.orders.create(razorpayOrder);

        // Translate Razorpay response → domain model
        return new PaymentResult(
            razorpayResponse.get("id"),                        // map to your paymentId
            mapStatus(razorpayResponse.get("status")),
            Money.inPaise(razorpayResponse.get("amount")),
            Instant.now()
        );
    }

    // If Razorpay's API changes, only this adapter changes — domain untouched
    private PaymentStatus mapStatus(String razorpayStatus) {
        return switch (razorpayStatus) {
            case "created"   -> PaymentStatus.PENDING;
            case "attempted" -> PaymentStatus.PROCESSING;
            case "paid"      -> PaymentStatus.SUCCESS;
            default          -> PaymentStatus.UNKNOWN;
        };
    }
}
```

### Resilience for Third-Party Calls

```java
// Every third-party call needs: timeout + retry + circuit breaker + fallback
@CircuitBreaker(name = "razorpay", fallbackMethod = "paymentFallback")
@Retry(name = "razorpay")
@TimeLimiter(name = "razorpay")
public CompletableFuture<PaymentResult> charge(Money amount, ...) {
    return CompletableFuture.supplyAsync(() -> razorpayClient.charge(...));
}

// Fallback: don't just throw; queue for async retry
public CompletableFuture<PaymentResult> paymentFallback(Money amount, ..., Throwable t) {
    log.error("Razorpay unavailable; queuing for retry", t);
    pendingPaymentQueue.enqueue(new PendingPayment(amount, ...));
    return CompletableFuture.completedFuture(PaymentResult.pending());
}
```

### Third-Party API Change Management

```
Versioning strategy for consumed APIs:
  → Always pin to a specific API version (v1, v2) in your client
  → Monitor third-party changelog / release notes
  → When they deprecate a version → create a migration task
  → Maintain ACL — new version = update only the adapter, not domain

Contract testing for third-party (where possible):
  → Record actual responses in a mock (WireMock recording mode)
  → Run tests against WireMock → fast, no real API calls
  → When third-party changes → update WireMock recordings → tests catch breaks
```

---

## Topic 6 · S5 Scenario Playbook — B2B API Platform with OAuth2

### The Question
> "Design a B2B API platform for a logistics company that wants to expose its order tracking, shipment creation, and inventory APIs to 200 partner companies. Partners will integrate via their own backend systems."

### Model Answer (Structure for 60 min)

```
Clarify:
  → Real-time or batch? (REST or webhooks or both?)
  → Partner volume: 200 partners, how many calls/day?
  → Compliance: PII in shipment data → DPDP implications
  → SLA: what uptime guarantee to partners?
  → Monetisation: free / tiered / usage-based?

NFRs:
  → Availability: 99.9% (partners depend on this for their operations)
  → Rate limiting: tiered (standard/premium/enterprise)
  → Audit: every API call logged (who called what, when — compliance)
  → Versioning: API versioned; minimum 12-month deprecation notice

Architecture:
  Partners → [Developer Portal (docs, keys, sandbox)]
           → [API Gateway — OAuth2, rate limiting, logging, routing]
           → [Partner API Service (ACL, data shaping, partner context)]
           → Internal services (TrackingService, ShipmentService, InventoryService)
           ← [Webhook Service (event push to partner endpoints)]

Auth: OAuth2 Client Credentials per partner
Rate limits: Standard 60/min, Premium 300/min, Enterprise custom
Webhooks: shipment status changes push to partner endpoints (HMAC-signed)
Sandbox: isolated environment with mock data for partner testing
```

---

## Day 11 Quick Reference

| Topic | Key Interview Answer |
|---|---|
| 6 Rs | Rehost/Replatform/Repurchase/Refactor/Retain/Retire — classify every workload; start with Retire + Repurchase to reduce scope |
| Migration waves | Wave 1: dev/test rehost; Wave 2: prod rehost + DB to RDS; Wave 3: refactor; Wave 4: cloud-native |
| Direct Connect vs VPN | VPN = fast + cheap + internet latency; Direct Connect = private fibre + consistent latency + compliance |
| Mainframe strategy | API Façade first (wrap, don't rewrite); Strangler Fig over 3-7 years; never big bang |
| Mainframe data sync | IBM MQ → Java Adapter → Kafka → services; dual-write with nightly reconciliation |
| B2B auth | OAuth2 Client Credentials; per-partner client_id/secret; scoped JWT tokens |
| Rate limiting | Tiered SLA (Standard/Premium/Enterprise); 429 with Retry-After; per-partner metrics |
| Webhooks | Push on event; HMAC-signed payload; retry 3x; DLQ on failure; idempotency key |
| ACL for third-party | Domain port (interface) + adapter (implements); domain never imports third-party SDK |
| API deprecation | Sunset header; 6-12 month notice; monitor per-partner usage; zero consumers before retire |

---

*Tags: #6Rs #migration #on-prem #cloud #mainframe #COBOL #strangler-fig #B2B #API-gateway #OAuth2 #webhooks #ACL #adapter-pattern #developer-portal #rate-limiting #S4 #S5 #S7*
