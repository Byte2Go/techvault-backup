# P1 · Day 2 — Service Mesh · Polyglot Microservices · SPA+API · CQRS · Contract Testing
**Pillar:** P1 — Microservices & System Design  
**Role Priority:** SA 🔵 Core · Java 🟢 Core · AI 🟣 Supporting  
**Time:** ~3 hours study + 1 hour Q&A practice

---

## Topic 1 · Service Mesh & Zero Trust Architecture
### In One Line
A <mark style="background: #ADCCFFA6;">service mesh manages all east-west (service-to-service) traffic with mTLS</mark>, <mark style="background: #FFB86CA6;">retries, circuit breaking, and observability</mark> — <mark style="background: #BBFABBA6;">without changing application code.</mark>

### Why It Matters
Enterprise JDs (especially fintech, insurance, large-scale SA roles) mention Istio, Linkerd, Zero Trust. You <mark style="background: #FFB8EBA6;">must be able to explain what problem a service mesh solves and when you'd actually use it vs when it's overkill.</mark>

### The East-West Traffic Problem
In a microservices system, services call each other constantly. Without a mesh:
- How do you <mark style="background: #FFB86CA6;">enforce mTLS</mark> between every pair of services?
- How do you <mark style="background: #FFF3A3A6;">add retries, timeouts, circuit breakers per route</mark>?
- How do you get <mark style="background: #ABF7F7A6;">request-level traces across 20 services</mark>?
- Answer: <mark style="background: #FF5582A6;">every dev team re-implements these in their service </mark>— inconsistently

### How Service Mesh Works — Sidecar Pattern
```
  [Service A Pod]                    [Service B Pod]
  App Container                      App Container
  Sidecar Proxy (Envoy)  ←mTLS→    Sidecar Proxy (Envoy)
       ↑                                   ↑
  Control Plane (Istiod) — pushes config to all sidecars
```
- Sidecar proxy (Envoy) [^1] <mark style="background: #D2B3FFA6;">intercepts all in/out traffic</mark> from the app
- App code is unchanged — <mark style="background: #FFB86CA6;">mesh is infrastructure</mark>
- Control plane(Istiod) <mark style="background: #FFF3A3A6;">manages certificates, routing rules, policies</mark>

### What Service Mesh Provides

| Feature                | What It Means                                                                                                                                                                                                                                                                                                                                                                                                                     |
| ---------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **mTLS**               | Every service-to-service call is encrypted and mutually authenticated  [^2]                                                                                                                                                                                                                                                                                                                                                       |
| **Traffic management** | Canary deployments, traffic splitting (90/10), retries, timeouts per route                                                                                                                                                                                                                                                                                                                                                        |
| **Circuit breaking**   | Automatically stop sending traffic to unhealthy services. ==In Enterprise we use **Istio** as the first line of defense to quickly drop dead, crashing pods from the network layer so the system stays responsive.== At the same time, we use **Resilience4j** inside their core Java services to gracefully handle business fallbacks when backend databases or critical third-party APIs experience business-logic degradation. |
| **Observability**      | Distributed traces, per-route metrics, <mark style="background: #BBFABBA6;">without code changes</mark>                                                                                                                                                                                                                                                                                                                           |
| **Policy enforcement** | "<mark style="background: #FFB86CA6;">Service A is allowed to call Service B; Service C is not"</mark>                                                                                                                                                                                                                                                                                                                            |
|                        |                                                                                                                                                                                                                                                                                                                                                                                                                                   |
### Service Mesh Mechanics in Canary Deployments
A **canary deployment** is a strategy where you release a new version of your software to a tiny subset of users (e.g., 2%, then 25%, then 100%) before rolling it out to everyone. This minimizes risk because if the new version has a bug, only a few users notice it.

Using a **Service Mesh (like Istio)** makes this traffic splitting smooth and safe by handling the decision-making at the sender's side.
#### The Two Traffic Routes
##### 1. Internal Traffic (Service-to-Service / East-West)
When one internal service calls another, the application code inside the calling pod makes a blind network request. Before that request can exit the pod, the **Caller's Envoy Sidecar** snatches it. The sidecar runs the traffic-splitting math right there, picks the target pod version (V1 or V2), and fires the packet directly to that specific IP.
##### 2. External Traffic (User-to-Service / North-South)
When an outside user hits your cluster, the request lands at the edge on the **Istio Ingress Gateway**. The gateway reads the traffic-splitting rules immediately at the entrance, does the math, and shoots the request straight to the correct backend pod version.
#### <mark style="background: #ABF7F7A6;">The Unified Engine: Envoy</mark>
**The Edge (Ingress Gateway) and the Pod (Sidecar) are running the exact same software engine.** They are both **Envoy Proxies**.
```
        ┌───────────────────────────────────────────────────────┐
        │      Istio Control Plane (istiod)                     │
        └────────────┬───────────────────────────────┬──────────┘
                     │                               │
                (Pushes Maps)                   (Pushes Maps)
                     ▼                               ▼       
       Istio Ingress Gateway                     Envoy Sidecar Proxy         
      - Role: The Front Door                     - Role: The Pod Bodyguard   
      - Software: Envoy Proxy                    - Software: Envoy Proxy 
```

- **The Ingress Gateway** is an Envoy proxy configured to act as your cluster's front door.
- **The Sidecar** is an Envoy proxy configured to act as a bodyguard sitting right next to your application container.

Because both components constantly talk to the central manager (**`istiod`**), they receive the exact same configuration maps and routing policies at the exact same time. This allows the edge gateway and the internal sidecars to execute Canary splits, mTLS encryption, and security rules together as one single, cohesive unit.
### Zero Trust Architecture
**Old model (Castle & Moat):** Trust everything inside the network perimeter.  
**Zero Trust:** Never trust, <mark style="background: #FFF3A3A6;">always verify — regardless of network location.</mark>

**Principles:**
1. Verify explicitly — <mark style="background: #ADCCFFA6;">every request authenticated and authorized </mark>(not just at edge)
2. Least privilege — <mark style="background: #D2B3FFA6;">services only have access to what they need</mark>
3. Assume breach — design as if attacker is already inside

**How Service Mesh enforces Zero Trust:**
```
Without mesh: Service A calls Service B via IP → no auth, no encryption inside cluster

With mesh + mTLS: Service A presents certificate → Service B validates → encrypted tunnel

AuthorizationPolicy: only OrderService can call PaymentService
```

**SPIFFE/SPIRE** — standard for service identity (used by Istio under the hood):
- Each service gets a SPIFFE ID: `spiffe://cluster.local/ns/default/sa/order-service`
- <mark style="background: #FFB86CA6;">Certificate issued, rotated automatically</mark>
### Istio vs Linkerd

| Dimension | Istio | Linkerd |
|---|---|---|
| Complexity | High — many features, steep learning curve | Low — simpler, opinionated |
| Performance overhead | Higher (Envoy proxy) | Lower (Rust proxy) |
| Feature set | Comprehensive | Core features only |
| Adoption | Wider enterprise adoption | Simpler environments |
| **Use when** | Complex traffic management, multi-cluster | Simplicity is priority |

### When NOT to Use Service Mesh
- Small system (< 5 services) — operational overhead isn't worth it
- Team without Kubernetes expertise — <mark style="background: #FFB8EBA6;">mesh needs k8s</mark>
- No mTLS or traffic management requirements — API Gateway alone is sufficient

### Real Scenario
> "You have 30 microservices in Kubernetes. <mark style="background: #ABF7F7A6;">Security requires all service-to-service traffic to be encrypted and authorized.</mark> How do you implement this without touching each service?"

**Answer:** <mark style="background: #BBFABBA6;">Deploy Istio service mesh.</mark> Enable mTLS in STRICT mode (all inter-service traffic must use mTLS). <mark style="background: #ABF7F7A6;">Define AuthorizationPolicies (which service can call which).</mark> <mark style="background: #FFB86CA6;">Sidecars handle encryption/auth transparently. </mark>App teams write zero additional security code.

### Interview Q&A
**Q: What is the difference between API Gateway and Service Mesh?**
A: <mark style="background: #D2B3FFA6;">API Gateway handles north-south traffic — external clients entering the system</mark>. <mark style="background: #ABF7F7A6;">Service mesh handles east-west traffic — services talking to each other inside the cluster.</mark> They're complementary. <mark style="background: #BBFABBA6;">API Gateway is for external consumers; service mesh is for internal security and reliability.</mark> In a mature architecture, you have both: AWS API Gateway at the edge and Istio for internal communication.

**Q: What is Zero Trust and how does a service mesh implement it?**
A: Zero Trust means we don't assume any request is safe just because it's inside our network. <mark style="background: #FFF3A3A6;">The service mesh implements it through mTLS</mark> — every service has a certificate (via SPIFFE [^3] implemeted in Istio), and <mark style="background: #ABF7F7A6;">every call is mutually authenticated and encrypted</mark>. <mark style="background: #FFB86CA6;">**AuthorizationPolicies** then enforce that only specific services can communicate with each other. </mark>An attacker who gets inside the cluster cannot freely call any service.

**Q: When would you choose not to deploy a service mesh?**
A: <mark style="background: #FFB8EBA6;">When the operational complexity outweighs the benefit.</mark> <mark style="background: #ADCCFFA6;">A mesh requires Kubernetes proficiency, adds latency (sidecar overhead ~1-2ms per hop),</mark> and has a learning curve. For systems with fewer than 10 services, or teams not yet on Kubernetes, I'd achieve similar goals <mark style="background: #D2B3FFA6;">with application-level mTLS libraries and a good API Gateway.</mark> Mesh makes sense when you have many services, security requirements for zero trust, and teams who shouldn't have to implement retry/circuit-breaking themselves.

### Gotchas
- Service mesh is NOT a replacement for API Gateway — different traffic planes
- mTLS in PERMISSIVE mode (allows plain text) is a trap — use STRICT in production
- <mark style="background: #ADCCFFA6;">Istio adds latency — measure it; for latency-sensitive services, evaluate **Linkerd**</mark>

---
## Topic 2 · Polyglot Microservices Architecture

### In One Line
<mark style="background: #FFF3A3A6;">Each microservice can use the best technology for its problem</mark> — Java, Python, Node.js, Go — <mark style="background: #FFB86CA6;">as long as they communicate through well-defined contracts</mark>.

### Why It Matters
This is in many SA JDs explicitly. You need to <mark style="background: #FFB86CA6;">design systems where a Java team, a Python ML team, and a Node.js team all coexist without chaos.</mark>

### What Polyglot Means
```
Order Service (Java/Spring Boot) ──── REST/gRPC ────→ Recommendation Service (Python/FastAPI)

Payment Service (Java/Spring Boot) ← Kafka events ← Fraud Detection (Python/Scikit-learn)

API Gateway (Node.js/Express BFF)  ──────────────→ all services
```

### How It Works in Practice
<mark style="background: #BBFABBA6;">**Communication contracts (language-neutral)</mark>:**
- **REST + OpenAPI spec** — <mark style="background: #FFF3A3A6;">any language can implement or consume it</mark>
- **gRPC + Protobuf [^5]** — <mark style="background: #ADCCFFA6;">binary protocol with language-neutral schema</mark>, <mark style="background: #BBFABBA6;">code-gen for all languages</mark>
- **AsyncAPI + Kafka** — event schema (Avro Schema [^4]/JSON Schema) <mark style="background: #D2B3FFA6;">registered in Schema Registry</mark>

**Shared infrastructure (language-neutral):**
- Service discovery: Kubernetes DNS (`http://payment-service.default.svc.cluster.local`) [[Kubernetes Service Discovery & Traffic Routing Architecture]]
- Observability: <mark style="background: #FFB86CA6;">OpenTelemetry SDK</mark> [^6] available in Java, Python, Node, Go
- Health checks: <mark style="background: #ABF7F7A6;">`/health` endpoint — standard across all languages</mark>
- Config: <mark style="background: #ADCCFFA6;">environment variables or ConfigMaps — language-neutral</mark>

**What each language is good at:**

| Language         | Strengths                                                   | Typical Microservice Use             |
| ---------------- | ----------------------------------------------------------- | ------------------------------------ |
| Java/Spring Boot | Enterprise patterns, mature ecosystem, JPA, Spring Security | Core business services               |
| Python/FastAPI   | ==ML libraries== (scikit-learn, PyTorch), rapid prototyping | ==AI/ML inference==, data processing |
| Node.js          | I/O-bound, ==real-time, BFF, API aggregation==              | ==BFF layer==, notification service  |
| Go               | High performance, low memory, concurrency                   | High-throughput proxies, CLI tools   |
| Rust             | Extreme performance, safety                                 | Service mesh sidecar (Linkerd)       |

### Schema Registry — Keeping Polyglot in Sync
For Kafka-based communication, every service (regardless of language) registers its <mark style="background: #FFF3A3A6;">event schema</mark>:
```
Confluent Schema Registry:
  - OrderPlaced schema (Avro) — Java producer registers, Python consumer validates
  - Schema evolution rules enforced centrally
  - Backward/forward compatibility checked on publish
```

### Challenges and Mitigations

| Challenge                                     | Mitigation                                                             |
| --------------------------------------------- | ---------------------------------------------------------------------- |
| Each service needs separate CI/CD pipelines   | Standardize on Docker + Kubernetes; ==pipeline template per language== |
| Debugging cross-language issues               | ==Distributed tracing (OpenTelemetry)== provides end-to-end trace      |
| Security vulnerabilities across languages     | Separate dependency scanning per language in CI pipeline               |
| Operational burden (5 languages = 5 runtimes) | Limit to 2-3 languages; "paved road" for approved stacks               |
| Knowledge silos per service                   | Document APIs thoroughly (OpenAPI); contract testing                   |

### The "Paved Road" Model
<mark style="background: #FFB8EBA6;">Don't allow unlimited language choice</mark>. Define an approved stack with tooling support:
```
Tier 1 (fully supported): Java/Spring Boot, Python/FastAPI
Tier 2 (use case specific): Node.js (BFF only), Go (high-perf only)
Tier 3 (not approved): Ruby, PHP, etc.
```

### Interview Q&A
**Q: How do you manage polyglot microservices without creating chaos?**
A: Three things: <mark style="background: #FFB86CA6;">standardize on contracts (OpenAPI or Protobuf</mark> — not ad-hoc), <mark style="background: #ADCCFFA6;">standardize on infrastructure (Docker, Kubernetes, OpenTelemetry </mark>— <mark style="background: #BBFABBA6;">every service speaks these regardless of language</mark>), and limit the approved languages (paved road model). Teams can choose within approved options, not invent freely. <mark style="background: #FFB86CA6;">The integration layer is language-neutral</mark>; the implementation is language-free.

**Q: How do you handle schema evolution when a Java service and Python service share a Kafka topic?**
A: Register schemas in <mark style="background: #ADCCFFA6;">Confluent Schema Registry</mark> [^7].  <mark style="background: #ABF7F7A6;">Enforce backward compatibility rules — new fields must be optional with defaults</mark>. <mark style="background: #FFB8EBA6;">The registry rejects schema changes that would break consumers. </mark> This is language-neutral: <mark style="background: #D2B3FFA6;">both Java (kafka-avro-serializer) and Python (confluent-kafka-python) use the same registry</mark>. Consumer updates happen independently of producer updates.

---

## Topic 3 · SPA + Microservices API Architecture
### In One Line
Single Page Applications (React/Angular) <mark style="background: #ADCCFFA6;">consume microservices via **a BFF or API Gateway** </mark> <mark style="background: #BBFABBA6;">using REST or GraphQL,</mark> with careful attention to CORS [^8], auth, and state management.

### Why It Matters
Most enterprise products have a web frontend. SA interviews often ask you to design the full stack — frontend included. Knowing <mark style="background: #ADCCFFA6;">how SPA integrates with a microservices backend shows depth.</mark>

### SPA Integration Patterns
**Pattern 1: SPA → API Gateway → Microservices**
```
React App → API Gateway (AWS GW)       → Order Service
                                       → User Service
                                       → Payment Service
```
- Gateway handles<mark style="background: #FFB86CA6;"> auth (JWT validation), rate limiting,</mark> routing [[Edge Routing Topologies- API Gateways vs Ingress Controllers]]
- SPA uses one base URL; <mark style="background: #D2B3FFA6;">gateway routes to correct service</mark>
- Simple, works for most cases

**Pattern 2: SPA → BFF → Microservices (preferred for complex UIs)**
```
React App → Web BFF (Node.js) → Order Service
                              → Inventory Service (aggregated)
```
- BFF aggregates <mark style="background: #FFB86CA6;">multiple service calls into one UI-optimized response</mark>
- BFF handles <mark style="background: #BBFABBA6;">session management for web (HttpOnly cookies)</mark>
- Frontend team owns BFF — iterate independently [[The Backend-For-Frontend (BFF) Pattern= Code-Driven Orchestration]]

**Pattern 3: SPA → GraphQL Gateway → Microservices**
```
React App → Apollo Federation Gateway → Order subgraph
                                      → User subgraph
                                      → Product subgraph
```
- SPA queries exactly what it needs (no over/under-fetching)
- Federation stitches subgraphs from multiple services
- More complex — worth it for large teams with many data types
- <mark style="background: #BBFABBA6;">Read in Detail:</mark> [[GraphQL Federation Pattern= Schema-Driven Orchestration]]

### Authentication in SPA + Microservices

**JWT flow:**
```
1. SPA → POST /auth/login → Auth Service → returns JWT (access token) + refresh token
2. SPA stores: access token in memory (NOT localStorage — XSS risk)
               refresh token in HttpOnly cookie (inaccessible to JS — CSRF protected)
3. SPA → GET /orders → API Gateway (validates JWT) → Order Service
4. On 401 → SPA calls /auth/refresh → gets new access token → retries request
```

**Why NOT localStorage for tokens:**
- XSS attack can steal tokens from localStorage
- HttpOnly cookies cannot be accessed by JavaScript at all

### CORS (Cross-Origin Resource Sharing)

**Problem:** Browser blocks SPA at `https://app.company.com` from calling API at `https://api.company.com`

**Solution:** API Gateway adds CORS headers:
```
Access-Control-Allow-Origin: https://app.company.com
Access-Control-Allow-Methods: GET, POST, PUT, DELETE
Access-Control-Allow-Headers: Authorization, Content-Type
Access-Control-Allow-Credentials: true  (needed if using cookies)
```

**Preflight:** Browser sends OPTIONS request first; gateway must respond with 200 + CORS headers.

### State Management Architecture
For large SPAs with many microservices:
- **Server state** (from APIs): React Query or SWR — handles caching, refetching, stale-while-revalidate
- **Client state** (UI-only): Zustand or Redux — minimal, only for truly local state
- **URL state**: Browser URL for navigable state (filters, tabs, pagination)

### Interview Q&A (40L SA Level)

**Q: How do you design authentication between a React SPA and your microservices?**
A: OAuth 2.0 Authorization Code flow with PKCE for the SPA. After login, Auth Service issues a short-lived JWT (15-minute access token) and a longer-lived refresh token. Access token stored in memory (never localStorage — XSS risk). Refresh token in HttpOnly, Secure, SameSite=Strict cookie — JS cannot access it. API Gateway validates JWT on every request. SPA automatically refreshes tokens before expiry using the refresh token.

**Q: When would you use GraphQL over REST for a SPA?**
A: GraphQL shines when the frontend has complex, varying data needs — different screens need different shapes of the same data, or data comes from many entities. For a product page needing data from Product, Inventory, Review, and Pricing services, a REST SPA makes 4 calls; GraphQL makes one. But GraphQL adds complexity: schema design, N+1 query problems (must use DataLoader), caching is harder than REST. I use REST by default and reach for GraphQL when the over/under-fetching problem is real and measurable.

---

## Topic 4 · CQRS (Command Query Responsibility Segregation)

### In One Line
Separate the write model (commands that change state) from the read model (queries that read state), allowing each to be optimized independently.

### Why It Matters
CQRS appears in SA interviews as a solution to read/write performance asymmetry. It's often paired with Event Sourcing and DDD — and interviewers expect you to know when to use it AND when not to.

### The Problem CQRS Solves
Single model trying to serve both writes and reads:
- Write path: complex domain logic, validations, aggregate invariants
- Read path: flat, joined, aggregated data for UI (50 fields from 5 tables)
- Same model can't be optimal for both → either reads are slow or domain is polluted

### CQRS Architecture

```
Command Side (Write):
User → POST /orders (Command) → Command Handler → Aggregate (domain logic) → Event Store / DB
                                                                           → publishes OrderPlaced event

Query Side (Read):
User → GET /orders/summary (Query) → Query Handler → Read Model (denormalized, optimized) → Response
                                                            ↑
                                             Event Projector (listens to events, builds read model)
```

**Read model examples:**
- SQL view or materialized view (denormalized)
- Elasticsearch index (for search)
- Redis cache (for hot data)
- MongoDB document (for complex nested reads)

### CQRS + Event Sourcing (Often Paired)

**Event Sourcing:** Store every state change as an event, not just current state.
```
DB stores:
  - OrderPlaced {orderId, customerId, items, total}
  - ItemAdded {orderId, item}
  - OrderShipped {orderId, trackingNumber}
  - OrderCancelled {orderId, reason}

Current state = replay all events for an orderId
```

**Benefits of Event Sourcing:**
- Full audit log — know exactly what happened and when
- Temporal queries — "what did the order look like yesterday at 3pm?"
- Replay to rebuild any read model

**Costs of Event Sourcing:**
- Event store grows indefinitely (need snapshots for old aggregates)
- Eventual consistency between command and read sides
- Complex to implement, debug, and query
- Tooling: Axon Framework (Java), EventStoreDB

### When to Use CQRS

✅ Use when:
- Read and write have very different scaling needs (reads 100x more than writes)
- Read model needs data from multiple aggregates (denormalized dashboard)
- Need audit log of all changes (financial, medical records)
- Separate teams owning read vs write optimization

❌ Don't use when:
- CRUD app with simple reads and writes
- Small system — too much complexity for limited benefit
- Team unfamiliar with eventual consistency — operational risk

### Critical Tradeoffs

| Benefit | Cost |
|---|---|
| Write side: clean domain model | Two codebases to maintain |
| Read side: optimized per query | Eventual consistency (write → event → projection → read) |
| Independent scaling | Debugging cross-side issues harder |
| Event replay = free audit log | Event store size grows; need snapshots |

### Real Scenario
> "Design a reporting dashboard for a trading platform. Trades happen 10K/sec. Dashboard shows portfolio summary, P&L, position history."

**Why CQRS:** Write side (trade execution) needs strict domain rules and low latency. Read side (dashboard) needs denormalized data aggregated across many trades.

**Solution:**
- Command side: TradeExecutionService writes to PostgreSQL via aggregate
- Events: TradeExecuted published to Kafka
- Read model projectors: PortfolioProjector builds Redis-cached portfolio summary; PositionProjector builds Elasticsearch index for position history queries
- Dashboard queries: Redis (portfolio, <1ms), Elasticsearch (position history, <50ms)

### Interview Q&A (40L SA Level)

**Q: What is CQRS and when would you use it?**
A: CQRS separates the command model — which enforces business rules and changes state — from the query model, which is optimized for reading. I'd use it when read and write have different scaling needs, when the domain model is too complex to also serve denormalized queries, or when I need an audit log via event sourcing. I avoid it for simple CRUD systems — it adds eventual consistency complexity that you don't need unless the problem demands it.

**Q: What is the consistency model in CQRS?**
A: Eventual consistency between command and read sides. A user places an order (command), the event is published, the projection updates the read model — this takes milliseconds to seconds. The client may read stale data briefly. For most UIs this is fine (optimistic updates help). For critical checks (inventory availability), you query the command-side DB directly, bypassing the read model.

**Q: How do you handle the growing event store in Event Sourcing?**
A: Snapshots. After N events for an aggregate, save a snapshot of the current state. When replaying, load the last snapshot and only replay events after it. Store old events in cold storage (S3 Glacier). Define a retention policy for events older than your audit requirement (e.g., 7 years for financial data).

### Gotchas
- CQRS does not require Event Sourcing — they're separate patterns (though often used together)
- Eventual consistency between command and read side catches many teams off guard in production
- Don't CQRS everything — apply selectively to the bounded contexts where it solves a real problem

---

## Topic 5 · Contract Testing for Microservices

### In One Line
Instead of integration tests that spin up real services, contract tests verify that a consumer's expectations and a provider's API are compatible — independently, in CI.

### Why It Matters
In microservices, you have 20 services each evolving independently. How do you prevent Service A from breaking when Service B changes its API? Integration tests are slow, flaky, and require all services running. Contract testing solves this.

### Consumer-Driven Contract Testing — Pact

**The flow:**
```
1. Consumer (Order Service) writes a Pact test:
   "I expect GET /payments/{id} to return {paymentId, status, amount}"
   → generates a Pact contract file (JSON)

2. Contract published to Pact Broker (shared repo of contracts)

3. Provider (Payment Service) CI pipeline runs verification:
   → downloads consumer contract from Pact Broker
   → spins up Payment Service
   → replays consumer's expected requests
   → verifies responses match the contract
   → passes/fails

4. Result: Provider knows immediately if a change breaks any consumer
```

**Key principle:** Consumers define what they need, providers verify they deliver it. No shared integration environment required.

### Spring Cloud Contract (Java Ecosystem)

Alternative to Pact for Spring-to-Spring services:
- Provider defines contracts (Groovy DSL or YAML)
- Contract generates: provider-side tests + consumer-side stubs
- Consumer uses generated stub in unit tests (WireMock under the hood)
- Tighter Spring integration, easier setup for pure Java shops

**When to choose:**
- Pact: polyglot (Java → Python, Node → Java)
- Spring Cloud Contract: Spring-only shop, provider-owns-contract approach

### Contract Testing in CI Pipeline

```
Consumer CI:
  - Unit tests (with provider stub from contract)
  - Generate Pact contract
  - Publish contract to Pact Broker
  - "Can I deploy?" check (has provider verified this contract?)

Provider CI:
  - Unit tests
  - Download consumer contracts from Pact Broker
  - Run contract verification tests
  - Publish verification results
  - "Can I deploy?" check (will this change break any consumer?)
```

### Contract vs Integration vs E2E Testing

| Type | Speed | What It Catches | Environment Needed |
|---|---|---|---|
| **Contract** | Fast (~seconds) | API contract breaks | None (stubs) |
| **Integration** | Medium (~minutes) | Cross-service logic | Staging/test env |
| **E2E** | Slow (~hours) | Full user journeys | Full system |

**SA recommendation:** Heavy contract testing (fast, CI-friendly), selective integration testing for complex cross-service flows, minimal E2E for critical user journeys only.

### Interview Q&A (40L SA Level)

**Q: How do you prevent API changes in one microservice from breaking consumers?**
A: Consumer-driven contract testing with Pact. Each consumer codifies its expectations as a contract test — what endpoints it calls, what response shape it needs. Contracts are published to a Pact Broker. In the provider's CI pipeline, it downloads all consumer contracts and verifies it still satisfies them. If a provider change breaks a consumer contract, the provider's build fails before deployment. This catches breaking changes without running a full integration environment.

**Q: What's the difference between contract testing and integration testing?**
A: Integration tests verify actual service-to-service behavior in a shared environment — they're slow, brittle, and require all services running. Contract tests verify the API contract (the interface agreement) independently — consumers test against stubs, providers verify against consumer expectations. Contract tests run in seconds in CI; integration tests take minutes and require environment coordination. I use contract tests for every service boundary and reserve integration tests for truly complex orchestration flows.

**Q: When would you use Spring Cloud Contract over Pact?**
A: When all services are Java/Spring — Spring Cloud Contract integrates naturally (Groovy DSL, WireMock stubs, Maven/Gradle plugins). When I have polyglot services (Java consuming a Python API, or Node.js consuming a Java service), I use Pact because it's language-neutral with clients for all major languages.

### Gotchas
- Contract testing doesn't replace integration tests — it complements them
- Pact Broker needs to be part of your deployment pipeline ("can I deploy?" gate)
- Contracts should be source-controlled by the consumer, not the provider

---

## Day 2 Quick Reference

| Topic | Key Interview Answer |
|---|---|
| Service Mesh | East-west traffic; mTLS, retries, circuit breaking via sidecars; complements API Gateway |
| Zero Trust | Never trust, always verify; mTLS + AuthorizationPolicy per service |
| Istio vs Linkerd | Istio = feature-rich, complex; Linkerd = simple, low overhead |
| Polyglot | Standardize contracts (OpenAPI/Protobuf) + infrastructure (Docker/k8s/OpenTelemetry); limit approved languages |
| SPA Auth | JWT in memory + refresh token in HttpOnly cookie; never localStorage |
| CQRS | Separate write (domain logic) from read (optimized model); eventual consistency; not for CRUD |
| Event Sourcing | Store events not state; replay = current state; snapshots for performance |
| Contract Testing | Consumer defines expectations; provider verifies; Pact (polyglot) or Spring Cloud Contract (Java) |

---

*Tags: #service-mesh #istio #zero-trust #mTLS #polyglot #SPA #JWT #CORS #CQRS #event-sourcing #contract-testing #pact*

---

[^1]: **Envoy**:  is an independent open-source proxy project. It has become the **absolute industry standard** for data routing in the cloud-native ecosystem. Because Envoy is so incredibly fast, light, and powerful, it has become the **"Universal Data Plane"** that almost all competing service mesh products use under the hood. **Example:** When you look inside an Istio mesh, the physical sidecar container running next to your pod is literally an Envoy Proxy (packaged with a few custom Istio plug-ins).  HashiCorp Consul, Open Service Mesh (OSM), Kuma, and Gloo Mesh all use Envoy as their default, first-class sidecar proxy.

[^2]: **Mutual authentication**, or two-way authentication, is ==a security process where both sides of a communication channel verify each other's identity before exchanging data==. Instead of only the client checking the server, the server also authenticates the client to ensure both parties are legitimate

[^3]: **SPIFFE** (==Secure Production Identity Framework for Everyone==) is an open-source standard for securing, verifying, and establishing uniform identities for software workloads (microservices, AI agents, and other non-human entities) in dynamic and heterogeneous environments.

[^4]: An **Apache Avro schema** is ==a plain JSON document that explicitly defines the structure, data types, and constraints of serialized data==. It serves as a strict, language-agnostic data contract between data producers and consumers in streaming architectures like Apache Kafka and big data systems like Apache Hadoop.

[^5]: **Protocol Buffers (Protobuf)** is ==Google's free, open-source, and language-neutral mechanism for serializing structured data==. Widely used in microservices and gRPC, it acts as a lightweight, lightning-fast alternative to XML or JSON by encoding data into binary format.  **Define Schemas:** You write data structures in a `.proto` text file, acting as a strict contract between systems. **Generate Code:** The `protoc` compiler translates this schema into native data access classes for programming languages like Java, Python, C++, and Go

[^6]: OpenTelemetry (OTel) is an open-source observability framework used ==to generate, collect, and export software telemetry data (such as traces, metrics, and logs) from your applications==. It acts as a universal standard, allowing engineering teams to monitor system health and troubleshoot complex microservices without vendor lock-in. The **OpenTelemetry (OTel) SDK** is ==the engine that executes the OpenTelemetry API==. While the API defines _what_ telemetry data (traces, metrics, and logs) to track, the SDK handles _how_ that data is processed, sampled, filtered, and exported to your monitoring and observability platforms

[^7]: **[Confluent Schema Registry](https://docs.confluent.io/platform/current/schema-registry/index.html)** is ==a centralized repository and service layer that provides a RESTful interface for storing, managing, and versioning schemas used in Apache Kafka data pipelines==. It serves as a contract arbitrator between decoupled applications, ensuring data quality and consistency as schemas evolve over time.

[^8]: **Cross-Origin Resource Sharing (CORS)** is ==a browser security mechanism that allows a web page from one domain to request and access resources from a different domain==. By default, browsers enforce the Same-Origin Policy (SOP), which blocks cross-domain requests unless the server explicitly permits them using specific HTTP response headers.
