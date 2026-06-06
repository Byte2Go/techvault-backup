# P8 · Day 10 — Monolith → Microservices: Strangler Fig · Dual-Write · Data Migration
**Pillar:** P8 — Integration & Migration  
**Role Priority:** SA 🔵 Core · Java 🟢 Core · AI ⚪ Supporting  
**Day in Plan:** Day 10 (Week 2)  
**Scenario covered:** S2 (MUST PREP)

---

## Why This Matters

Every SA interview for a company with > 5 years of engineering history involves migration. The ability to decompose a monolith safely — without a big bang rewrite, without downtime, with clear rollback — is the #1 differentiator for 40L SA roles. Most candidates can design greenfield. Very few can migrate safely.

---

## Topic 1 · When to Migrate — and When NOT To

### When migration is justified

```
Pain signals that make the case:
  ✅ Different services need different scaling (catalog = read-heavy, checkout = write-heavy)
  ✅ Long deployment cycles — every change requires full monolith deploy + regression test
  ✅ Team coordination overhead — 8 squads in one repo, merge conflicts daily
  ✅ One module failing brings down entire app (payment bug = catalog down)
  ✅ Technology constraints — one part needs Python/ML, rest is Java
  ✅ Compliance isolation — PCI-DSS scope must be separated from rest
```

### When to NOT migrate (say this in interviews — it signals maturity)

```
❌ "Microservices are modern" — not a reason
❌ Team < 10 engineers — distributed ops overhead too high
❌ Domain not well understood — wrong boundaries = distributed monolith
❌ Monolith is performing fine — if there's no pain, don't create it
❌ No DevOps maturity — microservices without CI/CD + observability = chaos

Better alternative: Modular Monolith
  → Single deployable, strict module boundaries, no circular dependencies
  → Gets you most of the maintainability benefit without the operational cost
  → Migrate to microservices later when you have concrete scaling pain
```

---

## Topic 2 · Strangler Fig Pattern — The Safe Migration Strategy

### In One Line
Wrap the monolith behind a facade, route new traffic to extracted microservices, and gradually strangle the monolith — never rewrite all at once.

### Origin
Named after the strangler fig tree — a vine that wraps around a host tree, grows alongside it, and eventually replaces it as the host dies. The host (monolith) continues functioning throughout.

### The Pattern

```
Phase 0 — Before (Monolith only):
  All traffic → Monolith

Phase 1 — Add Facade (API Gateway / Reverse Proxy):
  All traffic → [Nginx / API Gateway] → Monolith
  → No behaviour change; facade is transparent
  → This is your routing control plane

Phase 2 — Extract first service (e.g., Notifications):
  New notification traffic → [Facade] → NotificationService (NEW)
  Old notification traffic → [Facade] → Monolith (still running)
  → Facade routes by feature flag or URL path

Phase 3 — Strangle more services:
  Payments → PaymentService
  Catalog  → CatalogService
  [Facade] routes each domain to the appropriate service

Phase 4 — Monolith is gone:
  All traffic → [Facade] → Microservices
  Monolith decommissioned
```

### Routing Strategy in Facade

```nginx
# Nginx routing — redirect by path
location /api/notifications/ {
    proxy_pass http://notification-service:8080;
}

location /api/catalog/ {
    proxy_pass http://catalog-service:8080;
}

location / {
    proxy_pass http://monolith:8080;  # everything else still goes to monolith
}
```

```yaml
# API Gateway (Kong) — route by path prefix
services:
  - name: notification-service
    url: http://notification-service:8080
    routes:
      - paths: ["/api/notifications"]

  - name: monolith
    url: http://monolith:8080
    routes:
      - paths: ["/"]    # catch-all — monolith handles everything not yet extracted
```

### Extraction Order — Which Service First?

```
Criteria for first extraction:
  ✅ Low coupling to other monolith modules (few shared tables, few internal calls)
  ✅ Clear, stable domain boundary (unlikely to change during migration)
  ✅ High business value OR high pain (the reason you're doing this)
  ✅ Small team can own it completely

Good first candidates:
  Notifications     — typically loosely coupled; async; no shared write tables
  User preferences  — isolated data; simple CRUD
  Reporting/analytics — read-only; can be extracted without touching write path

Bad first candidates:
  Order management  — tightly coupled to inventory, payment, shipping
  Authentication   — everything depends on it; risky to touch early
  Payments          — high risk; leave for after you've proven the pattern
```

---

## Topic 3 · Dual-Write Pattern — Zero-Downtime Data Migration

### In One Line
Write to both the old DB and the new service's DB simultaneously during migration — validate consistency, then cut over reads, then eliminate the old write path.

### The Problem
You can't just copy data and switch — the monolith is still writing to its DB while you're migrating. A one-time copy creates a gap.

### Dual-Write Phases

```
Phase 1 — SINGLE WRITE (before):
  App → writes to Monolith DB only
  New service DB: empty

Phase 2 — DUAL WRITE (migration):
  App → writes to Monolith DB (primary)
       → writes to New Service DB (secondary, async or sync)
  Reads still go to Monolith DB
  → Compare: are both DBs in sync?

Phase 3 — VERIFY (validation):
  Run shadow reads: read from both DBs, compare results
  Log discrepancies
  Fix sync issues until discrepancy rate = 0%

Phase 4 — FLIP READS (switch):
  Writes still go to BOTH DBs
  Reads now go to New Service DB
  → Monitor for errors; can revert reads instantly

Phase 5 — SINGLE WRITE (cutover):
  Stop writing to Monolith DB
  New Service DB is now sole source of truth
  Remove dual-write code

Phase 6 — DECOMMISSION:
  Remove old tables from Monolith DB (or entire monolith)
```

### Implementation — Dual-Write in Java

```java
@Service
public class OrderRepository {

    private final MonolithJdbcTemplate monolithDb;
    private final OrderServiceJdbcTemplate newServiceDb;
    private final FeatureFlags flags;

    @Transactional
    public void save(Order order) {
        // Always write to monolith DB (primary)
        monolithDb.save(order);

        // Dual-write to new service DB when flag is enabled
        if (flags.isEnabled("dual-write-orders")) {
            try {
                newServiceDb.save(order);
            } catch (Exception e) {
                // Log failure but don't fail the primary write
                log.error("Dual-write to new DB failed for order {}. Will sync async.", 
                    order.id(), e);
                asyncReconciliationQueue.enqueue(order.id());
            }
        }
    }

    public Order findById(OrderId id) {
        if (flags.isEnabled("read-from-new-service-db")) {
            return newServiceDb.findById(id);  // Phase 4+
        }
        return monolithDb.findById(id);        // Phase 1-3
    }
}
```

### Shadow Read Validation

```java
@Component
@Scheduled(fixedDelay = 60_000)  // run every minute
public class DataConsistencyValidator {

    public void validateOrders() {
        List<OrderId> sample = monolithDb.getSampleOrderIds(1000);  // random sample
        int mismatches = 0;

        for (OrderId id : sample) {
            Order monolithOrder = monolithDb.findById(id);
            Order newOrder = newServiceDb.findById(id);

            if (!monolithOrder.equals(newOrder)) {
                mismatches++;
                log.warn("MISMATCH orderId={} monolith={} new={}", id, monolithOrder, newOrder);
                metrics.counter("data.migration.mismatch").increment();
            }
        }

        double mismatchRate = (double) mismatches / sample.size() * 100;
        log.info("Data consistency check: {}% mismatches in {} orders", mismatchRate, sample.size());

        // Only proceed to Phase 4 when mismatchRate == 0
    }
}
```

---

## Topic 4 · Data Migration Strategies

### Strategy 1 — Big Bang (Avoid Unless Forced)

```
Stop monolith → migrate all data → start microservices
Downtime: hours to days
Risk: high — no rollback once monolith is stopped
Use only when: system can afford maintenance window AND dataset is small
```

### Strategy 2 — Trickle Migration (Online Migration)

```
Step 1: Copy historical data in background (bulk load)
        → pg_dump / AWS DMS / Debezium CDC
        → New service DB seeded with all existing data

Step 2: Replay recent events / WAL changes to catch up
        → Debezium reads PostgreSQL WAL → publishes to Kafka → new service consumes

Step 3: Once lag < 1 second → switch to dual-write (Phase 2 above)
        → Dual-write closes the final gap
        → No downtime; monolith runs throughout
```

### Strategy 3 — Debezium CDC (Change Data Capture)

```
Debezium connector → reads PostgreSQL Write-Ahead Log (WAL)
                  → publishes every INSERT/UPDATE/DELETE to Kafka topic
                  → New service consumes → applies to its own DB

Config:
{
  "connector.class": "io.debezium.connector.postgresql.PostgresConnector",
  "database.hostname": "monolith-db.company.com",
  "database.dbname": "monolith",
  "table.include.list": "public.orders,public.order_lines",
  "topic.prefix": "migration"
}

Result:
  Kafka topic "migration.public.orders":
    { "op": "c", "after": { "id": 123, "status": "PLACED", ... }}  ← INSERT
    { "op": "u", "before": {...}, "after": { "id": 123, "status": "SHIPPED" }}  ← UPDATE
    { "op": "d", "before": { "id": 123, ... }}  ← DELETE

New service consumer applies changes to its DB in real-time
→ Near-zero lag with no application code change in monolith
```

### Strategy 4 — Expand-Contract for Schema Changes

```
Challenge: New service needs different schema than monolith
  Monolith: orders.customer_name VARCHAR(100)
  New service: orders.customer_id FK → customers table

Migration:
  Expand:
    1. Add customer_id column to monolith orders table (nullable first)
    2. Backfill: UPDATE orders SET customer_id = (SELECT id FROM customers WHERE name = customer_name)
    3. Make customer_id NOT NULL (after backfill verified)
    4. Dual-write includes customer_id

  Contract:
    5. New service uses customer_id (not customer_name)
    6. After cutover, remove customer_name from new service schema
    7. Eventually clean up from monolith too
```

---

## Topic 5 · 6-Month Migration Roadmap (Interview Answer)

### The Interviewer Question

> "You've been hired as SA at a 7-year-old fintech company. They have a Java monolith handling 10K transactions/day. 4 squads, all working in one repo. Deployments take 2 weeks and require full regression. Design a 6-month migration plan."

### Month-by-Month Roadmap

```
Month 1 — Assess & Prepare
  ├── Domain mapping: event storming to identify bounded contexts
  ├── Coupling analysis: which modules share tables? which are isolated?
  ├── Dependency graph: what calls what? find seams (loosely coupled = extract first)
  ├── DevOps foundation: CI/CD pipeline, Docker, Kubernetes (non-negotiable prerequisite)
  ├── Observability: add distributed tracing + structured logging to monolith
  └── Decision: choose first 2 services to extract (lowest coupling)

Month 2 — Facade + First Extraction (Notifications)
  ├── Deploy Nginx/API Gateway in front of monolith (transparent — no behaviour change)
  ├── Extract NotificationService (most isolated — async, no shared write tables)
  ├── Dual-write: monolith still sends notifications but also publishes events to Kafka
  ├── NotificationService consumes events, sends email/SMS/push
  ├── Validate: both paths produce same notifications; compare in shadow mode
  └── Cutover reads + disable monolith's direct notification code

Month 3 — User & Auth Extraction
  ├── Extract UserService (profile, preferences — isolated CRUD)
  ├── Auth stays in monolith for now (too risky to move early)
  ├── Dual-write user data; validate consistency
  ├── Trickle migration: Debezium CDC syncs historical user data to new DB
  └── Cutover user reads to UserService

Month 4 — Catalog Extraction
  ├── Extract ProductCatalogService → Elasticsearch + PostgreSQL
  ├── Migrate product data (read-only historical migration is simpler)
  ├── Route all /catalog/* traffic to CatalogService via gateway
  ├── Add caching layer (Redis) now that catalog is isolated
  └── Monolith now only handles: orders, payments, reporting

Month 5 — Order + Payment Extraction (Most Complex)
  ├── OrderService extracted — most complex (coupled to inventory, payment, notifications)
  ├── Use orchestration saga (replaces monolith's synchronous call chain)
  ├── Dual-write with strict validation (financial data — 0% mismatch tolerance)
  ├── PaymentService extracted — wraps Razorpay; stores payment records
  ├── Canary: 5% → 25% → 50% → 100% traffic over 2 weeks
  └── Rollback plan: gateway can switch traffic back to monolith instantly

Month 6 — Decommission + Stabilise
  ├── Remove dual-write code from all extracted services
  ├── Decommission monolith (or keep as legacy reporting shell)
  ├── Clean up shared DB: drop migrated tables from monolith DB
  ├── Establish SLOs for each service
  ├── Chaos engineering: test circuit breakers, failover paths
  └── Retrospective: document what to do differently next migration
```

### Risk Mitigation Table

| Risk | Mitigation |
|---|---|
| Data inconsistency during dual-write | Shadow read validator; 0% mismatch gate before cutover |
| New service bugs in production | Canary deployment (5% traffic); instant rollback via gateway |
| Team unfamiliar with distributed patterns | Proof-of-concept for Saga pattern before Month 5 |
| Downstream teams broken by API changes | Consumer-driven contract testing (Pact) before cutover |
| Monolith regression during extraction | Don't touch monolith code unless necessary; route only at gateway |
| Increased operational complexity | DevOps foundation (Month 1) is non-negotiable prerequisite |

---

## Topic 6 · Anti-Patterns — What NOT to Do

### Anti-Pattern 1: Big Bang Rewrite

```
"We'll rewrite everything in microservices in 6 months while the monolith still runs"
→ Reality: rewrite takes 18 months, monolith still gets bug fixes,
           new system never catches up → project cancelled
→ Fix: Strangler Fig — extract incrementally; the monolith keeps running
```

### Anti-Pattern 2: Distributed Monolith

```
Symptom: "We have 20 microservices but deploy them all together"
  → Services share a DB → schema changes require multi-team coordination
  → Service A calls Service B synchronously → tight temporal coupling
  → "Microservices" in name only; all the downsides, none of the benefits
  
Fix: Enforce database-per-service. Break synchronous chains with events.
     If you can't deploy one service without coordinating with 5 others,
     you have a distributed monolith.
```

### Anti-Pattern 3: Wrong Extraction Order

```
"Let's extract the core Order service first — it's the most important"
→ Order service has 15 internal dependencies in the monolith
→ You end up rewriting half the monolith to extract one service
→ Fix: Extract lowest-coupling services first; move inward as you gain confidence
```

### Anti-Pattern 4: No Rollback Plan

```
"We deployed the new PaymentService to 100% of traffic. It has a bug."
→ No feature flag, no canary, no way to route back to monolith
→ Fix: Keep monolith running during migration. Gateway routing = instant rollback.
       Never cut over payments at 100% without a tested rollback path.
```

---

## Interview Q&A (40L SA Level)

**Q: How would you migrate a monolith to microservices without downtime?**
A: Strangler Fig pattern. Step one: put a facade (API Gateway or Nginx) in front of the monolith — no behaviour change, just routing control. Step two: identify the lowest-coupling module (usually notifications or user preferences) and extract it as the first microservice. Route its traffic through the facade to the new service. Step three: dual-write to both the monolith DB and the new service DB; validate consistency with shadow reads until mismatch is zero. Step four: flip reads to the new service; keep dual-write active for safety. Step five: once stable, remove the monolith write path. Repeat for each domain. The monolith runs throughout — no downtime, instant rollback at the gateway level.

**Q: How do you handle shared database tables during extraction?**
A: Three steps. First, the Expand phase — add the new columns or tables the microservice needs alongside the existing ones; backfill data. Second, dual-write — both paths write to both schemas simultaneously; validate consistency. Third, the Contract phase — after cutover, clean up the old columns from both schemas. I never do a direct schema rename or drop on live systems. Debezium CDC is ideal for keeping new service DB in sync during migration without touching monolith application code.

**Q: What's the biggest risk in monolith-to-microservices migration, and how do you mitigate it?**
A: The distributed monolith anti-pattern — you extract services but they remain tightly coupled through a shared database or synchronous call chains. It looks like microservices but has all the downsides: deployment coordination, cascading failures, schema coupling. The mitigation is enforcing database-per-service from the start — each service gets its own schema even if it's on the same Postgres instance initially. And breaking synchronous chains with Kafka events rather than direct service calls. If you can't deploy one service independently, you haven't really decoupled.

**Q: When would you advise NOT to migrate to microservices?**
A: When the team is small (under 10 engineers), when the domain boundaries aren't well understood, or when there's no real operational pain driving the migration. A modular monolith — single deployable with strict module boundaries and no circular dependencies — gives you most of the maintainability benefit at a fraction of the operational cost. I'd recommend microservices only when you have concrete evidence that a monolith can't solve the problem: independent scaling needs, team autonomy blocked by shared codebase, or technology heterogeneity requirements. "Microservices are modern" is not a reason.

---

## Day 10 Quick Reference

| Topic | Key Interview Answer |
|---|---|
| Strangler Fig | Facade → route by domain → extract lowest-coupling first → dual-write → cutover → decommission |
| First service to extract | Lowest coupling (notifications, preferences) — never start with core transaction services |
| Dual-write | Write primary + secondary; validate shadow reads; flip reads; remove old write path |
| Debezium CDC | Reads PostgreSQL WAL → Kafka → new service DB; real-time sync with no app changes |
| Expand-Contract | Add new column/table → backfill → dual-write → cutover → drop old |
| Distributed monolith | Services deployed separately but share DB or are synchronously chained — worst of both worlds |
| Rollback strategy | Keep monolith running; gateway routes; feature flags; canary on new services |
| When NOT to migrate | Small team, unclear domain, no real scaling pain → Modular Monolith instead |
| 6-month roadmap | Month 1: assess+DevOps; M2: facade+notifications; M3: users; M4: catalog; M5: orders+payments; M6: decommission |

---

*Tags: #strangler-fig #monolith #microservices #migration #dual-write #Debezium #CDC #expand-contract #distributed-monolith #data-migration #S2*
