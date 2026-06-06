# P1 · Day 1 — Microservices Decomposition · BFF · API Gateway · HLD/LLD · Web API Architecture
**Pillar:** P1 — Microservices & System Design  
**Role Priority:** SA 🔵 Core · Java 🟢 Core · AI 🟣 Supporting  
**Time:** ~3 hours study + 1 hour Q&A practice

---

## Topic 1 · Microservices Architecture & Service Decomposition

### In One Line
Break a system into <mark style="background: #BBFABBA6;">independently deployable services</mark> <mark style="background: #ABF7F7A6;">aligned to business capabilities</mark>, <mark style="background: #ADCCFFA6;">each owning its data</mark>.

### Why It Matters
Every SA interview starts here. You'll be given a monolith and asked "how would you break it up?" or given a new system and asked "how would you design this?" If you can't decompose cleanly, everything downstream fails.

### Decomposition Strategies

**By Business Capability** — org chart alignment (what the business does)
```
E-commerce → Order Management, Inventory, Catalog, Payments, Shipping, Notifications
```

**By DDD Bounded Context** — <mark style="background: #FFB86CA6;">language boundary alignment</mark> (where terms mean different things)
```
"Customer" in CRM ≠ "Customer" in Billing ≠ "Customer" in Shipping
→ Three separate bounded contexts → three separate services
```

**Strangler Fig Pattern** — for decomposing existing monolith:
```
Monolith → API Gateway in front → route new traffic to microservice → strangle old code
→ Never rewrite all at once; extract service by service
```

### Service Boundary Rules (Goldilocks Problem)
Too coarse = distributed monolith (services deploy together, <mark style="background: #FF5582A6;">share DB</mark>)  
Too fine = <mark style="background: #FF5582A6;">nano-services (chatty network</mark>, high latency, operational nightmare)

**Right size signals:**
- <mark style="background: #ABF7F7A6;">One team can own it</mark> end-to-end (2-pizza rule)
- Has <mark style="background: #BBFABBA6;">one primary reason to change</mark> (SRP at service level)
- Can be <mark style="background: #BBFABBA6;">deployed independently</mark> without coordinating with other teams
- Has its <mark style="background: #BBFABBA6;">own data store</mark>

### Inter-Service Communication

| Need                      | Pattern         | Technology          |
| ------------------------- | --------------- | ------------------- |
| Real-time response needed | Sync REST/gRPC  | HTTP/2, REST        |
| Decouple + async          | Async messaging | Kafka, RabbitMQ     |
| High-performance internal | gRPC            | Protobuf            |
| Query across services     | API Composition | Gateway aggregation |
| State sync                | Domain events   | Kafka topics        |

### Data Consistency — Saga Pattern

**Problem:** Distributed transaction across services (e.g., Order + Payment + Inventory)

**Choreography Saga** — <mark style="background: #FFB86CA6;">services react to events</mark>, no central coordinator
```
Order Service → publishes OrderPlaced
  → Payment Service listens → charges card → publishes PaymentCharged
  → Inventory Service listens → reserves stock → publishes StockReserved
  → Notification Service listens → sends confirmation
```
✅ Simple, no SPOF  
❌ Hard to see the overall flow, event chains hard to debug

**Orchestration Saga** — central orchestrator (Saga Orchestrator) tells each service what to do
```
Order Orchestrator → calls Payment → calls Inventory → calls Notification
                  ← compensates if any step fails
```
✅ Flow visible in one place, easier to debug  
❌ Orchestrator becomes a coordination bottleneck, potential SPOF

**Compensating Transactions** — undo already-committed steps on failure:
```
PaymentCharged → StockReservationFailed → RefundPayment (compensating tx)
```

### Critical Tradeoffs

| Decision                | Benefit                         | Cost                                               |
| ----------------------- | ------------------------------- | -------------------------------------------------- |
| Separate DB per service | Independent schema, tech choice | Joins across services impossible → API composition |
| Async communication     | Decoupled, resilient            | Eventual consistency, harder to trace              |
| gRPC over REST          | 5-10x performance               | Binary protocol, harder to debug                   |
| Choreography saga       | No SPOF                         | Flow visibility poor                               |
| Orchestration saga      | Flow visible                    | Orchestrator coupling                              |

### Real Scenario
> "Design order management for an e-commerce platform at 50K orders/day"

**Decompose:** OrderService, InventoryService, PaymentService, NotificationService, ShippingService  
**Communication:** REST for sync (place order API), Kafka for async (OrderPlaced event to downstream)  
**Consistency:** Orchestration saga for order placement flow (need clear failure compensation)  
**Data:** Each service owns DB — OrderDB (Postgres), InventoryDB (Postgres), NotificationDB (Mongo)

### Interview Q&A

**Q: How do you decide service boundaries?**
A: Start with business capabilities, validate against DDD bounded contexts. Key test: can this service be deployed without coordinating with another team? If not, the boundary is wrong. Also check: does it have a single reason to change? If a service changes when Payments changes AND when Shipping changes, it's doing too much.

**Q: How do you handle distributed transactions in microservices?**
A: Two-phase commit doesn't work at scale — it's synchronous and creates cross-service locks. Use the Saga pattern: break the transaction into a sequence of local transactions with compensating actions on failure. For complex flows with clear rollback needs, I prefer orchestration saga (visibility). For simple event chains, choreography.

**Q: What's the biggest mistake teams make when adopting microservices?**
A: Shared database. Services look independent but are coupled at the data layer — schema changes break multiple services. Second biggest: decomposing too early before domain boundaries are understood. Start with a modular monolith, extract when you hit concrete scaling or team autonomy pain.

### Gotchas & What Impresses Interviewers
- Mention Conway's Law: "I align service boundaries to team boundaries, not just technical boundaries"
- Say "strangler fig" when asked about migration — it signals real-world experience
- Call out the "distributed monolith" anti-pattern proactively
- Know that Saga ≠ 2PC. Never suggest 2PC across microservices.

---

## Topic 2 · BFF Pattern (Backend for Frontend)

### In One Line
A dedicated backend per frontend client type <mark style="background: #BBFABBA6;">that aggregates and shapes data specifically for that client's needs.
</mark>
### Why It Matters
Mobile apps need different data shapes than web. <mark style="background: #FFB86CA6;">Partner APIs need different contracts than internal UIs</mark>. BFF is the architectural answer — and it's in nearly every enterprise SA JD.

### The Problem BFF Solves
Single general-purpose API:
- Returns everything, clients filter → over-fetching (wastes mobile bandwidth)
- Returns too little → under-fetching (mobile makes 5 calls for one screen)
- Mobile and web have different update cycles but are blocked on shared API changes

### BFF Architecture
```
Mobile App → [Mobile BFF] → microservices
Web App    → [Web BFF]    → microservices  
Partner    → [Partner BFF / API Gateway] → microservices
```

Each BFF:
- <mark style="background: #ABF7F7A6;">Aggregates calls from multiple services</mark>
- Shapes response for its specific client
- <mark style="background: #ADCCFFA6;">Handles auth/session</mark> for that client type
- Can be independently deployed and versioned

### BFF vs API Gateway

| Dimension     | API Gateway                              | BFF                                   |
| ------------- | ---------------------------------------- | ------------------------------------- |
| Purpose       | Cross-cutting: auth, rate limit, routing | Client-specific aggregation & shaping |
| Who builds it | Platform/infra team                      | Frontend team (owns it)               |
| Logic         | Minimal business logic                   | Aggregation + transformation          |
| Count         | One (or few)                             | ==One per client type==               |
| Evolution     | Stable                                   | Changes with frontend                 |

> Key answer: "API Gateway is infrastructure; BFF is product." Both coexist.

### When NOT to Use BFF
- You have one client type → overkill
- All clients need the same data → shared API is fine
- Team too small to own multiple BFFs

### Real Scenario
> "Design the API layer for a fintech app with mobile (Android/iOS), web dashboard, and third-party partner integration"

**Solution:**
- Mobile BFF: lightweight payloads, push notification triggers, offline sync support
- Web BFF: full data, rich filters, server-side pagination
- Partner API (via API Gateway + dedicated service): versioned, documented, rate-limited
- <mark style="background: #D2B3FFA6;">All three consume same microservices (AccountService, TransactionService, etc.)</mark>

### Interview Q&A

**Q: When would you use a BFF over a generic API?**
A: When clients have meaningfully different data needs, or <mark style="background: #ABF7F7A6;">when frontend teams need to iterate independently without being blocked on a shared backend.</mark> <mark style="background: #FFB8EBA6;">If mobile needs 5 fields and web needs 50 from the same screen, a shared API either over-fetches on mobile or under-fetches on web.</mark> <mark style="background: #BBFABBA6;">BFF solves this by giving each client its own backend contract.</mark>

**Q: Who should own the BFF?**
A: The frontend team. This is the key insight — the BFF is not infrastructure, it's a product component. <mark style="background: #FFB8EBA6;">When the platform team owns it, it becomes a coordination bottleneck (frontend needs a change, submits a ticket, waits)</mark>. <mark style="background: #ABF7F7A6;">Frontend ownership means the team can evolve their client and BFF together at their own pace.</mark>

### Gotchas
- BFF is not a replacement for API Gateway — they serve different purposes
- BFF can become a monolith if you put too much logic in it — keep domain logic in microservices
- <mark style="background: #FFB86CA6;">GraphQL is sometimes used as a BFF alternative</mark> (single flexible query layer) — worth mentioning

---

## Topic 3 · API Gateway Architecture

### In One Line
A <mark style="background: #BBFABBA6;">reverse proxy at the edge of your microservices system</mark> that handles cross-cutting concerns: <mark style="background: #FFB86CA6;">routing, auth, rate limiting, SSL termination, observability</mark>.

### Why It Matters
<mark style="background: #ADCCFFA6;">In every microservices system, you need a single entry point</mark>. <mark style="background: #BBFABBA6;">API Gateway is that entry point</mark>, and SA interviews test whether you understand what it should and shouldn't do.

### What API Gateway Does

**It handles:**
- Request routing to correct microservice
- <mark style="background: #D2B3FFA6;">Authentication verification (JWT validation, OAuth token introspection)</mark>
- Rate limiting and throttling [^1]
- SSL/TLS termination [^2]
- Request/response transformation [^3]
- Load balancing [^4]
- Observability (request logging, metrics, traces) [^5]
- API versioning routing (`/v1/` → service-v1, `/v2/` → service-v2)

**It does NOT handle:**
- Business logic
- Database access
- <mark style="background: #FFB8EBA6;">Service-to-service communication</mark> (that's service mesh)

### Rate Limiting Algorithms

| Algorithm          | How it works                                                                               | Pros                                | Cons                                            |
| ------------------ | ------------------------------------------------------------------------------------------ | ----------------------------------- | ----------------------------------------------- |
| **Fixed Window**   | Count resets every minute                                                                  | Simple                              | ==Burst at window boundary (2x rate possible)== |
| **Sliding Window** | Rolling count over last N seconds. Counts requests in a rolling time frame (e.g. last 60s) | Smooth                              | More memory                                     |
| **Token Bucket**   | Bucket fills at rate R; each request consumes 1 token                                      | ==Allows bursts up to bucket size== | Slightly complex                                |
| **Leaky Bucket**   | Requests drip out at ==fixed rate==                                                        | Strict, predictable                 | No burst allowed                                |

> **SA Answer:** "I use ==Token Bucket for most APIs== — it allows short bursts for legitimate traffic spikes while still enforcing a long-term average rate. Fixed Window is fine for simple quotas."

# API Gateways, Ingress, & Service Meshes
This guide details the complete <mark style="background: #FFB86CA6;">end-to-end mechanics of container networking</mark>. It covers <mark style="background: #ABF7F7A6;">how edge traffic enters your cluster and hands off to backend code</mark>, <mark style="background: #ADCCFFA6;">as well as how internal microservices talk directly across same-cluster and multi-cluster boundaries</mark>.
## The Traffic Planes
- **North-South:** Traffic <mark style="background: #FFB8EBA6;">crossing the external network boundary into your cluster</mark> (Client $\rightarrow$ Application).
- **East-West:** <mark style="background: #BBFABBA6;">Traffic moving internally from container to container</mark> within your ecosystem (Service $\rightarrow$ Service).

## 1. The 3-Layer Responsibility Matrix

| **Layer** | **Component**                                   | **Core Operational Role**                                                                                                                                   | **Physical Location**                      |
| --------- | ----------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------ |
| **L 1**   | **External API Gateway** _(AWS GW, Broadcom)_   | **Business & Security Edge:** Validates consumer API keys, checks monetization/billing limits, and enforces global user rate limiting.                      | **Outside Kubernetes**                     |
| **L 2**   | **Ingress Controller** _(NGINX, Istio Ingress)_ | **Cluster Traffic Entry:** Evaluates inbound HTTP routing paths (like `/retail`), decodes SSL/TLS certificates, and balances traffic across active Pod IPs. | **Inside Kubernetes** (Cluster Edge)       |
| **L 3**   | **Service Mesh** _(Istio, AWS VPC Lattice)_     | **Microservice Network Plane:** Handles zero-trust internal encryption (mTLS), internal communication failure retries, and distributed transaction tracing. | **Inside Kubernetes** (Pod-to-Pod Network) |

## 2. Integrated Traffic Flow Blueprints

### Flow A: External Call Handoff & Edge Mechanics (North-South $\rightarrow$ East-West)
When an external client calls your system, **both Layer 2 (Ingress) and Layer 3 (Service Mesh) look at the same underlying Kubernetes data,** but they use it to handle two entirely separate stages of the entrance handshake.

```
                       [ External Client ] 
                               │
                        (Public Internet)
                               ▼
┌───────────────────────────────────────────────────────────────────┐
│ Layer 1: External API Gateway (AWS Gateway / Broadcom)            │
│ - Checks API keys, user billing, and global traffic limits.       │
└──────────────────────────────┬────────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────┐
│ Layer 2: Ingress Controller (NGINX / Istio Ingress)         │
│                                                             │
│  1. Looks at the URL path (like /retail).                   │
│  2. Matches that path to a Service Name using a local map.  │
│  3. Chooses a live Pod IP using its own load balancing.     │
│  4. Handles the SSL/TLS security encryption decryption.     │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼ (Traffic fires directly to the chosen Pod IP)
┌─────────────────────────────────────────────────────────────┐
│ Layer 3: Service Mesh (Istio Envoy Sidecar)                 │
│ - Automatically catches the packet right before it hits app.│
│ - Upgrades the connection to secure mTLS mesh encryption.   │
└──────────────────────────────┬──────────────────────────────┘
                               │
                               ▼
                       [ Destination Pod ]
```

#### 1. How the Ingress Controller Maps `/retail` to a Pod IP
To stay fast under heavy load, **the Ingress Controller does not query the central Kubernetes API database [^6] on every request.** That would overwhelm the cluster with network lookups. Instead, it maintains a live configuration map in its local memory cache:

```
[ INGRESS CONTROLLER INTERNAL MEMORY MAP ]

   HTTP Path         Target K8s Service          Live Pod IPs (Endpoints Array)
  ───────────        ──────────────────          ──────────────────────────────
   /retail   ───►     retail-service     ───►    [ 10.244.0.5, 10.244.1.9 ]
   /corp     ───►     corp-service       ───►    [ 10.244.2.40 ]
```

##### The Real Traffic Flow Steps:
1. An external user request hits the Ingress Controller asking for the path `/retail`.
2. The Ingress Controller scans its local map and resolves the logic: _"`/retail` means I need to send this to `retail-service`."_
3. It instantly pulls the array of raw, active container IPs tied to that service: `[10.244.0.5, 10.244.1.9]`.
4. **The Ingress Controller handles the load balancing itself.** It uses its own logic (like Round-Robin, alternating turns) to pick a single target IP—for example, `10.244.0.5`—and shoots the request directly to that pod.

```
                           [ External Request ]
                                    │
                                    ▼
                      ┌───────────────────────────┐
                      │ Layer 2 Ingress (NGINX)   │
                      │                           │
                      │ Holds local memory array: │
                      │ [10.244.0.5, 10.244.1.9]  │
                      └─────────────┬─────────────┘
                                    │
                 ┌──────────────────┴──────────────────┐
                 │ (NGINX runs Round-Robin algorithm   │
                 │  and picks a target IP itself)      │
                 ▼                                     ▼
        ┌─────────────────┐                   ┌─────────────────┐
        │  Pod 1 Target   │                   │  Pod 2 Target   │
        │  (10.244.0.5)   │                   │  (10.244.1.9)   │
        └─────────────────┘                   └─────────────────┘
```

#### 2. Cache Maintenance & Handling Dead Pods
If the Ingress Controller relies on a local memory map, _what stops it from routing traffic to a container that just crashed?_ Kubernetes solves this with an **Event-Driven Push Model**.
- **The Watch Subscription:** When the Ingress Controller boots up, it opens a persistent network stream (a "Watch") to the central **Kubernetes API Server**. It registers for live updates regarding any changes to pods or endpoints.
- **The Instant Update:** The exact millisecond pod `10.244.0.5` dies, the cluster manager updates the core database, registers the death, and broadcasts a push notification straight to the Ingress Controller: _`[REMOVE ENDPOINT: 10.244.0.5]`_.
- **The Clean Cache:** The Ingress Controller catches the event message and erases that IP from its internal memory map in the blink of an eye.

##### The High-Availability Safety Net: "Retry on Next Upstream"
If a packet leaves the Ingress at the exact microsecond a pod crashes, before the database alert can arrive, a fail-safe mechanism kicks in:
> If the Ingress data plane fires a packet to `10.244.0.5` and receives an immediate connection refusal or network timeout, **it does not throw an error.** It catches the socket failure internally, drops that IP from the active rotation, selects the next live IP in its array (`10.244.1.9`), and forwards the user's request there. The user never experiences a drop in service.

#### 3. The Hand-off to Layer 3 (The Istio Interception)
The moment the network packet leaves the Ingress Controller and reaches the target pod's network boundary (`10.244.0.5`), the Ingress is completely out of the picture. Layer 3 networking takes over.

```
┌────────────────────────────────────────────────────────┐
│  LAYER 2: NGINX Ingress Pod                            │
│  - Reads its own map directly from K8s API Server.     │
│  - Selects destination Pod IP: 10.244.0.5              │
│  - Fires a standard HTTP packet across the cluster.    │
└───────────────────────────┬────────────────────────────┘
                            │
                            │ (Standard Network Packet)
                            ▼
┌────────────────────────────────────────────────────────┐
│  LAYER 3: Destination Pod Boundary (IP: 10.244.0.5)    │
│                                                        │
│   1. Linux Network Layer (iptables / eBPF)             │
│      - Catches the incoming packet at the pod door.    │
│      - Transparently redirects it into Envoy Sidecar.  │
│                                                        │
│   2. Envoy Sidecar Proxy                               │
│      - Uses the map/policies pushed to it by istiod.   │
│      - Logs metrics and checks security rules.         │
│                                                        │
│   3. Local Loopback Handoff                            │
│      - Delivers the clean request to the Application.  │
└────────────────────────────────────────────────────────┘
```

- **The Interception:** Inside the pod's network environment, Linux routing tables (`iptables` or `eBPF` hooks) trap the inbound request. They block it from hitting the application code directly, transparently diverting the traffic into the **Istio Envoy Sidecar Proxy** running inside the same pod container.
- **Independent Configuration Processing:** The sidecar processes the packet using rules and routing directories pushed to it **exclusively by the Istio Control Plane (`istiod`)**.
- **The Mesh Polish:** The <mark style="background: #FFB86CA6;">Envoy proxy performs an active security validation: it evaluates identity parameters, verifies if the sender has permission to connect via Istio Authorization Policies</mark>, logs tracing spans for observability metrics, and finally passes the decoded payload over a local loopback (`localhost`) down to the actual **Application Container**.

### Flow B: Internal Same-Cluster Call (Pure East-West)
When Service A calls Service B inside the same Kubernetes cluster, **traffic completely bypasses the Ingress Controller.** Communication stays entirely horizontal and flows directly pod-to-pod.

```
        ┌─────────────────────────────────────────────┐
        │        Service-to-Service Direct Path       │
        └─────────────────────────────────────────────┘
  ┌───────────────────────────┐           ┌───────────────────────────┐
  │ Pod A                     │           │ Pod B                     │
  │  ┌─────────────────────┐  │           │  ┌─────────────────────┐  │
  │  │ Application Code    │  │           │  │ Application Code    │  │
  │  └──────────┬──────────┘  │           │  └──────────▲──────────┘  │
  │             │             │           │             │             │
  │             ▼             │  (mTLS)   │             │             │
  │  ┌─────────────────────┐  │──────────►│  ┌─────────────────────┐  │
  │  │ Envoy Sidecar Proxy │  │  Direct   │  │ Envoy Sidecar Proxy │  │
  │  └─────────────────────┘  │  Routing  │  └─────────────────────┘  │
  └───────────────────────────┘           └───────────────────────────┘
```

#### 1. How Sidecars Receive Network Maps (Discovery)
The central **Istio Control Plane (`istiod`)** tracks the master Kubernetes database. However, rather than forcing individual application containers to query the K8S API server, **`istiod` compiles the cluster topology data and pushes it down to every sidecar proxy.**

Inside **Pod A**, the local Envoy sidecar maintains its own lookup table:

```
[ POD A'S ENVOY PROXY LOCAL MEMORY MAP ]

   Target K8s Service          Live Pod IPs (Endpoints Array)
   ──────────────────          ──────────────────────────────
    retail-service     ───►    [ 10.244.0.5, 10.244.1.9 ]
    corp-service       ───►    [ 10.244.2.40 ]
```

#### 2. Step-by-Step Internal Routing
1. **The Code Initiates a Call:** The application runtime inside Pod A sends a plain HTTP call to `http://corp-service`. The application code does not know the physical location of the server; it simply triggers a standard network payload.
2. **The Sidecar Interception:** <mark style="background: #FFB86CA6;">Local `iptables` route modifications</mark> snatch the outbound request before it can exit the pod, passing it directly to **Pod A's Envoy Sidecar**.
3. **The Proxy Load Balances:** The <mark style="background: #FFB86CA6;">local proxy looks up the target destination</mark> (`corp-service`), pulls the live IP options, runs its own balancing math, and selects an active container IP (`10.244.2.40`).
4. **The Secure Mesh Tunnel:** Pod A's sidecar <mark style="background: #FFF3A3A6;">wraps the connection payload inside an encrypted mutual TLS (**mTLS**) tunnel</mark> and shoots the traffic **directly over the virtual pod network** to Pod B, bypassing all edge components.
5. **The Handoff:** Pod B's Envoy proxy catches the network stream, <mark style="background: #ABF7F7A6;">validates the cryptographic credentials, confirms access permissions, decrypts the request,</mark> and delivers it locally to Pod B's application container.

### Flow C: Cross-Cluster Call (Multi-Cluster East-West)
If a service target resides on a **completely separate Kubernetes cluster** located in another cloud region or data center, traffic still **bypasses the external Layer 2 Ingress Controller.**

```
    CLUSTER 1 (US-East)                               CLUSTER 2 (US-West)
┌───────────────────────────┐                       ┌───────────────────────────┐
│ Pod A                     │                       │ Pod B                     │
│  ┌─────────────────────┐  │                       │  ┌─────────────────────┐  │
│  │ Application Code    │  │                       │  │ Application Code    │  │
│  └──────────┬──────────┘  │                       │  └──────────▲──────────┘  │
│             │             │                       │             │             │
│             ▼             │                       │             │             │
│  ┌─────────────────────┐  │                       │  ┌─────────────────────┐  │
│  │ Envoy Sidecar Proxy │  │                       │  │ Envoy Sidecar Proxy │  │
│  └──────────┬──────────┘  │                       │  └──────────▲──────────┘  │
└─────────────┼─────────────┘                       └─────────────┼─────────────┘
              │                                                   ▲
              │ (Encrypted mTLS Tunnel)                           │ (DirectRoute)
              ▼                                                   │
   ┌─────────────────────┐                               ┌────────┴────────────┐
   │ Main Ingress (L2)   │ [BYPASSED]                    │  East-West Gateway  │
   └─────────────────────┘                               └────────▲────────────┘
              │                                                   │
              └─────────────── (Public/Private WAN) ──────────────┘
```

#### 1. Unified Mesh Discovery
<mark style="background: #BBFABBA6;">The individual cluster control planes (`istiod` on Cluster 1 and `istiod` on Cluster 2) are securely cross-linked. </mark> <mark style="background: #FFF3A3A6;">They share service registries over an internal network channel, binding both environments into a single **"Virtual Mesh."**</mark> Because of this cross-pollination, Pod A's sidecar address directory knows exactly which target dependencies run inside the remote cluster.

#### 2. Cross-Cluster Traffic Routing
1. **The Request:** The application container code in Pod A (Cluster 1) triggers a standard network connection to `http://service-b`.
2. **The Location Check:** Pod A's local sidecar proxy intercepts the connection and checks its pre-synced map. It notices that zero copies of `service-b` are active locally in Cluster 1, but valid targets exist in Cluster 2.
3. **Routing to the Bridge:** Because individual cluster pod networks are isolated and cannot talk directly over the public internet, <mark style="background: #FFB86CA6;">Pod A's sidecar wraps the request in an mTLS tunnel and targets the public/routable IP of **Cluster 2's East-West Gateway (Port 15443)**.</mark>
4. **The Gateway Handshake:** The <mark style="background: #ADCCFFA6;">East-West Gateway on Cluster 2</mark> accepts the incoming stream. It verifies the cross-cluster credentials, confirms the routing paths, and forwards the payload inside the cluster directly to the private network interface of **Pod B**.
5. **Delivery:** Pod B's local Envoy sidecar catches the packet from the gateway, handles the final decryption step, and hands the request over to Pod B's application container.

|**Gateway Feature**|**Istio Ingress Gateway (L2)**|**Istio East-West Gateway**|
|---|---|---|
|**Primary Traffic Plane**|**North-South** (Public internet $\rightarrow$ Cluster)|**East-West** (Cluster 1 $\rightarrow$ Cluster 2)|
|**Standard Network Port**|Port **80 / 443** (Standard Web Traffic)|Port **15443** (Istio Mutual TLS Port)|
|**Who talks to it?**|Web browsers, external mobile apps, public clients.|Envoy sidecars from _other_ companion Kubernetes clusters.|
|**What it does with traffic**|Decrypts public SSL, reads the HTTP path (`/retail`), and passes it inside.|Validates internal mesh certificates and safely forwards traffic to a private Pod IP.|

## 3. Architecture Synchronization Summary
To keep your concepts perfectly clear, remember this master mapping of how data syncs and traffic routes across different configurations:

|**Component**|**Where does it get its Pod IP list?**|**How does it get updated?**|**Operational Role**|
|---|---|---|---|
|**NGINX Ingress** _(Layer 2)_|Direct from the **Kubernetes API Server**.|**Event-Driven Push:** The core K8s API server sends a real-time event alert directly to NGINX when a pod changes.|Handles entry routing for **North-South** external traffic.|
|**Istio Ingress Gateway** _(Layer 2)_|From the central **`istiod` Control Plane**.|**Event-Driven Push:** `istiod` watches the API server and flattens updates down to the Ingress Gateway container via gRPC.|Handles entry routing for **North-South** external traffic.|
|**Envoy Sidecars** _(Layer 3)_|From the central **`istiod` Control Plane**.|**Event-Driven Push:** `istiod` watches the API server and flattens updates down to every sidecar proxy via gRPC.|Handles internal security and routing for **East-West** traffic.|

## 4. Technical Concept Summary
> - **The Kubernetes Master Registry (`etcd`):** The central database managed by the API Server. It serves as the single source of truth for which containers are alive and what IP addresses they hold.
> - **The Ingress Controller (Layer 2):** The edge traffic dispatcher. It watches path parameters, maps configurations to specific services, saves pod IP records in its local cache, and load-balances inbound external requests.
> - **The Service Mesh (Layer 3):** The zero-trust internal network security guard. It relies on a central coordinator (`istiod`) to push fresh address books down to sidecar proxies, wrapping every container in automated encryption (mTLS), performance telemetry tracking, and failure resilience.

## 3. Fast Product Guide
- **Broadcom / Mulesoft:** Best for old-school enterprise apps (Legacy SOAP, heavy compliance audits). Lives entirely outside K8s.
- **AWS API Gateway:** Best for AWS-native setups, serverless (Lambda), and quick developer portals. Lives outside K8s.
- **NGINX:** Unique because they <mark style="background: #BBFABBA6;">can play **both Layer 1 and Layer 2**. </mark>They can sit on the edge _and_ act as the K8s Ingress Controller natively.
- **Istio:** The gold standard for an <mark style="background: #FFB86CA6;">East-West K8s service mesh</mark>. Can also act as Layer 2 using the _Istio Ingress Gateway_.
- **AWS VPC Lattice:** An <mark style="background: #FFB86CA6;">AWS-only service mesh</mark> that builds networking into the AWS infrastructure plane, removing the need for sidecar proxies.
- **Consul:** The best <mark style="background: #FFB86CA6;">service mesh</mark> choice if you need to connect K8s pods to legacy bare-metal VMs.

## 4. Architectural Truths (The "Why")
### 💡 External Gateways Cannot Replace Ingress
AWS API Gateway or Broadcom live outside Kubernetes. <mark style="background: #FFB8EBA6;">They have no idea when pods scale up, down, or change internal IPs.</mark> Y<mark style="background: #ABF7F7A6;">ou **always** need an internal Ingress Controller</mark> (like NGINX) to receive edge traffic and track dynamic pod environments.
### 💡 Ingress Controllers Must Have K8s Services
An Ingress Controller doesn't route traffic directly to random pod IPs on its own. ==It relies on the **Kubernetes Service** to maintain a stable registry of active pods.== You cannot skip the K8s Service.
	When we say _"The Ingress Controller relies on the Kubernetes Service,"_ here is the exact chain of communication that happens under the hood:
	
When you deploy an application, you never hardcode IP addresses. Instead, Kubernetes dynamically connects everything using a text-tagging system called **Labels and Selectors**.
#### 1. The Pod Labeling (The Name Tag)
When you deploy 3 replicas of your retail application, Kubernetes spins them up with random names and random IP addresses. However, your deployment blueprint stamps a matching <mark style="background: #FFB86CA6;">key-value text label</mark> onto all of them: `app: retail`
#### 2. The Service Record (The Static Anchor)
You <mark style="background: #ABF7F7A6;">create a configuration object called a **Kubernetes Service** named</mark> `retail-service`. You do not give it IP addresses. Instead, you give it a rule called a **Selector**:
_"Find any pod in this cluster stamped with the tag `app: retail`."_ This definition is saved as a permanent, static data record directly inside the central **Kubernetes API Server**.
#### 3. The API Server Response & Ingress Handoff
The **Ingress Controller** connects to the **Kubernetes API Server** via its permanent "Watch" subscription to build its local routing memory map.

<mark style="background: #FFF3A3A6;">If a pod crashes and is replaced, the new pod automatically inherits the `app: retail` tag. The **Kubernetes API Server** instantly catches the new IP address change and pushes the updated list straight to your Ingress Controller.</mark> You never have to track a single changing IP manually.
```
1. YOU CREATE:  [ Your App Pods ]  ◄── Linked By ──►  [ K8s Service: "retail-service" ]
                                                              │
                                                   (Saved as a database record)
                                                              ▼
2. STORED IN:                                    [ Kubernetes API Server ]
                                                              ▲
                                                   (Subscribes via a "Watch")
                                                              │
3. DISCOVERED BY:                                [ Ingress Controller (NGINX) ]
```



### 💡 Watch for Product Duplication
Running AWS API Gateway _and_ NGINX Ingress together means you have two different layers both trying to do <mark style="background: #FFB8EBA6;">Layer 7 HTTP routing.</mark> <mark style="background: #FFB86CA6;">Make sure you actually need the external layer's specific business features (like billing or portals)</mark> to justify the extra network hop.

## 5. Simplified Decision Matrix

| **If your infrastructure looks like...** | **Use at the Edge (L1)** | **Use for Ingress (L2)** | **Use for Mesh (L3)** |
| ---------------------------------------- | ------------------------ | ------------------------ | --------------------- |
| **Legacy On-Prem / Heavy Compliance**    | Broadcom / Mulesoft      | NGINX                    | None / Optional       |
| **AWS Cloud-Native**                     | AWS API Gateway          | NGINX or Istio Ingress   | VPC Lattice or Istio  |
| **Pure K8s (Advanced Security/mTLS)**    | None (Direct to LB)      | Istio Ingress            | Istio                 |
| **Hybrid (K8s + Bare-Metal VMs)**        | NGINX                    | NGINX                    | HashiCorp Consul      |
## 6. Clean Interview Answers

**Q: API Gateway vs Service Mesh?**
> "An API Gateway handles external, North-South traffic coming into the company (Auth, Billing, Rate Limiting). A Service Mesh handles internal, East-West traffic between your backend services (mTLS, Retries, Circuit Breaking)."

**Q: Both Layer 2 Ingress and Layer 3 Service Mesh read the K8s Service Registry. What's the difference in how they use it?**
> "Layer 2 Ingress reads the registry to accept external (North-South) traffic and figure out which pod IP to route it to. Layer 3 Service Mesh reads the same registry to distribute a real-time network map to every sidecar proxy, allowing pods to communicate directly (East-West) using mTLS without needing to go back through the Ingress."

**Q: If Service A calls Service B inside the same cluster, does it go through the Ingress Controller?**
> "No. Internal service-to-service communication completely bypasses the Ingress Controller. Istio coordinates discovery automatically using the K8s Service registry and routes traffic directly from Pod A's sidecar proxy to Pod B's sidecar proxy."

**Q: What happens if the target service pod is in a completely different Kubernetes cluster?**
> "It still bypasses the main external Ingress Controller. Istio connects the two clusters' registries behind the scenes. When Pod A tries to call the cross-cluster service, its sidecar routes the traffic directly to Cluster 2's dedicated **East-West Gateway**, which safely routes it straight to the destination pod."

**Q: When external traffic hits an NGINX Ingress Controller, how does it enter the Istio Mesh?**
> "The external traffic hits the NGINX container first to evaluate path-routing rules. However, because the NGINX pod is injected with an Istio Envoy sidecar, any traffic leaving NGINX to head to an application pod is instantly intercepted by Envoy, upgraded to an mTLS mesh connection, and securely forwarded."
                                                        |
### Interview Q&A

**Q: What should and shouldn't go in an API Gateway?**
A: Cross-cutting concerns go in — <mark style="background: #FFB86CA6;">auth, rate limiting, SSL, routing, logging</mark>. Business logic stays out. The moment you put domain logic in the gateway (e.g., "if user is premium, route to premium service"), you've created a coupling that makes the gateway hard to change independently. Keep it dumb and fast.

**Q: How does API Gateway differ from a Service Mesh?**
A: API Gateway manages north-south traffic — external clients to your system. <mark style="background: #ABF7F7A6;">Service mesh manages east-west traffic — service to service inside the cluster.</mark> They solve different problems and coexist. In an enterprise setup I'd use  AWS API Gateway at the edge and Istio for internal service communication.

**Q: How would you make an API Gateway highly available?**
A: <mark style="background: #FFB86CA6;">Deploy multiple gateway instances across AZs behind a load balancer</mark>. <mark style="background: #ADCCFFA6;">Use stateless gateway design — no session state in the gateway (tokens are validated, not stored)</mark>. <mark style="background: #D2B3FFA6;">Rate limiting state goes in Redis (shared across instances).</mark> Health checks + auto-scaling on gateway pods/instances.

### Gotchas
- <mark style="background: #FF5582A6;">Don't route service-to-service calls through the API Gateway — adds latency and a dependency</mark>
- Rate limiting at gateway alone isn't enough — <mark style="background: #FFB86CA6;">services should also self-protect (circuit breaker)</mark>
- <mark style="background: #D2B3FFA6;">API Gateway is not an ESB — don't do message transformation or orchestration in it</mark>

---

## Topic 4 · HLD / LLD — Architecture Artifacts
### In One Line
HLD defines <mark style="background: #FFB86CA6;">what you're building and why</mark> at a system level; LLD defines exactly <mark style="background: #ABF7F7A6;">how each component works.</mark>

### Why It Matters
SA interviews often ask: "Walk me through how you would document this architecture." <mark style="background: #FFF3A3A6;">Knowing what goes in HLD vs LLD</mark> — and being able to produce them on a whiteboard — is a core SA competency.

### HLD (High-Level Design)
**Audience:** Tech leads, architects, product, management  
**Timing:** Before development starts  
**Format:** Diagrams + ADRs + NFR table

**Contents:**
1. **Business View (C4 L1 / System Context)** — system + external actors (users, third parties, existing systems).  It shows the high-level boundary of your system and how external actors interact with it.
2. **Application View (C4 L2 / Containers)** — apps, services, DBs, queues inside the system. It zooms inside the system box to show the internal applications, databases, and microservices.
3. **Security View** — what's inside vs outside trust boundary
4. **Deployment View** — cloud regions, AZs, Kubernetes clusters, CDN
5. **Architecture Decision Records (ADRs)** — why each key decision was made
6. **Non-Functional Requirements (NFRs)** — availability %, latency p99, throughput TPS, RPO/RTO
7. **Integration Points** — third-party APIs, legacy systems, data flows

### LLD (Low-Level Design)
**Audience:** Developers implementing the feature  
**Timing:** Before sprint, after HLD approved  
**Format:** Sequence diagrams + API specs + DB schema

**Contents:**
1. **Sequence Diagrams** — step-by-step flow for each use case
2. **API Contracts** — OpenAPI/Swagger specs (endpoints, request/response schemas, error codes)
3. **Database Schema** — tables, indexes, foreign keys, partitioning strategy
4. **Class/Component Design** — key interfaces, implementations (for Java Architect)
5. **Error Handling Strategy** — what happens when each dependency fails
6. **Caching Strategy** — what's cached, TTL, invalidation approach

### HLD vs LLD Anti-Patterns

| Anti-Pattern                                    | Fix                                                        |
| ----------------------------------------------- | ---------------------------------------------------------- |
| HLD with too much detail (class-level diagrams) | ==Keep HLD at container level==; LLD owns component detail |
| LLD without HLD (jump straight to code)         | Always establish system context first                      |
| HLD never updated (living document neglect)     | ==HLD is living — update when ADRs change==                |
| LLD as novels (100-page specs)                  | LLD should be =="just enough to unblock devs"==            |

### Interview Q&A

**Q: What's in an HLD and who is the audience?**
A: HLD answers: <mark style="background: #FFB86CA6;">what are we building</mark>, <mark style="background: #ADCCFFA6;">how do the pieces connect, and why did we make key decisions</mark>? Audience is tech leads, architects, and product. I use <mark style="background: #D2B3FFA6;">C4 L1+L2 diagrams for the structure</mark>, <mark style="background: #BBFABBA6;">ADRs for decisions, and an NFR table for non-functional targets</mark>. The goal is: <mark style="background: #ABF7F7A6;">someone can read this and understand the system without reading any code.</mark>

**Q: When would you skip LLD?**
A: For simple CRUD endpoints or well-understood patterns where the team has done this before. LLD investment scales with risk and novelty — high-risk integrations (payment, auth), new patterns (event sourcing for the first time), or complex business logic all warrant detailed LLD. Routine features don't.

---
## Topic 5 · Web API Architecture
### In One Line
Design principles for APIs that are stable, evolvable — covering<mark style="background: #BBFABBA6;"> versioning, idempotency, and backward compatibility.</mark>
### Richardson Maturity Model (REST Levels)

| Level  | Name                 | What It Means                           | Example                                                                        |
| ------ | -------------------- | --------------------------------------- | ------------------------------------------------------------------------------ |
| **L1** | Resources            | Separate URL per resource               | `POST /orders`, `GET /orders/123`                                              |
| **L2** | HTTP Verbs           | Correct HTTP methods + status codes     | `GET` for read, `POST` for create, `PUT/PATCH` for update, `DELETE`            |
| **L3** | Hypermedia (HATEOAS) | Response includes links to next actions | `{"orderId": 123, "links": [{"rel": "cancel", "href": "/orders/123/cancel"}]}` |

> **SA target: L2 minimum.** L3 is theoretically correct but rarely implemented in practice — mention it exists but say "most enterprise APIs stop at L2."

### API Versioning Strategies

| Strategy                | Example                                   | Pros                                   | Cons                            |
| ----------------------- | ----------------------------------------- | -------------------------------------- | ------------------------------- |
| **URI versioning**      | `/v1/orders`, `/v2/orders`                | Explicit, ==cacheable, easy to route== | URL pollution, not "pure REST"  |
| **Header versioning**   | `API-Version: 2`                          | Clean URLs                             | ==Harder to test in browser==   |
| **Query param**         | `/orders?version=2`                       | Easy to test                           | Cache issues, feels like a hack |
| **Content negotiation** | `Accept: application/vnd.company.v2+json` | Truly RESTful                          | Complex, rarely used            |

> **SA recommendation:** <mark style="background: #D2B3FFA6;">URI versioning for public APIs (explicit, easy to route at gateway)</mark>, <mark style="background: #ABF7F7A6;">Header versioning for internal APIs.</mark>

### Idempotency
**Definition:** Calling the same API multiple times produces the same result as calling it once.
**Why critical:** Network retries, client retries on timeout, duplicate messages from event broker.

**HTTP methods and idempotency:**
- `GET`, `PUT`, `DELETE` — naturally idempotent
- `POST` — NOT idempotent by default → must add idempotency key

**Implementing POST idempotency:**
```
Client sends: POST /payments
Headers: Idempotency-Key: uuid-abc-123

Server:
1. Check Redis: has key uuid-abc-123 been processed?
2. If YES → return cached response (don't charge again)
3. If NO → process payment, store result in Redis with key (TTL: 24h), return result
```

```java
// Pseudo-code
public PaymentResponse processPayment(PaymentRequest req, String idempotencyKey) {
    String cached = redis.get("idempotency:" + idempotencyKey);
    if (cached != null) return deserialize(cached);
    
    PaymentResponse response = paymentGateway.charge(req);
    redis.set("idempotency:" + idempotencyKey, serialize(response), Duration.ofHours(24));
    return response;
}
```

### Backward Compatibility Rules
**Breaking changes (never in existing version):**
- <mark style="background: #FFB8EBA6;">Removing a field</mark> from response
- Changing a <mark style="background: #FFB8EBA6;">field's type (string → integer)</mark>
- <mark style="background: #FF5582A6;">Making an optional field required</mark>
- Removing an endpoint

**Non-breaking changes (safe in existing version):**
- Adding a new optional field to response
- Adding a new optional request parameter
- Adding a new endpoint
- Relaxing validation (was required, now optional)

**Strategies:**
- **Expand-contract pattern:** <mark style="background: #FFF3A3A6;">Add new field alongside old,</mark> deprecate[^7] old, <mark style="background: #BBFABBA6;">then remove in next version</mark>
- **Tolerant reader pattern:** <mark style="background: #FFB86CA6;">Clients ignore unknown fields</mark> (critical for microservices consumer contracts)
- **Consumer-driven contract testing:** Pact / Spring Cloud Contract — <mark style="background: #ADCCFFA6;">consumers define what they need, providers verify they meet it</mark>

### Best Practices
```
✅ Use correct HTTP status codes:
   200 OK, 201 Created, 204 No Content
   400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found
   409 Conflict (duplicate), 422 Unprocessable Entity (validation)
   500 Internal Server Error, 503 Service Unavailable

✅ Consistent error format:
{
  "error": "PAYMENT_DECLINED",
  "message": "Insufficient funds",
  "correlationId": "req-abc-123",
  "timestamp": "2026-06-05T10:30:00Z"
}

✅ Correlation ID on every request — pass through all service calls for distributed tracing
✅ Pagination on all list endpoints: cursor-based for large datasets, offset for small
✅ HTTPS only — no HTTP
✅ Rate limit headers: X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset
```

### Interview Q&A
**Q: How do you handle API versioning in a microservices system?**
A: <mark style="background: #ABF7F7A6;">**URI versioning** for external/public APIs — it's explicit, easy to route at the API Gateway, and developers can test it in a browser.</mark> <mark style="background: #ADCCFFA6;">**Header versioning** for internal service-to-service APIs — keeps URLs clean and routes are invisible to external consumers.</mark> <mark style="background: #FFB8EBA6;">The key principle: never break existing clients; always give them a deprecation window (typically 6-12 months) before removing an old version.</mark>

**Q: How do you implement idempotency for payment APIs?**
A: <mark style="background: #FFB86CA6;">Client generates a unique Idempotency-Key (UUID) per transaction attempt.</mark> <mark style="background: #ADCCFFA6;">Server checks a Redis cache on arrival — if the key exists, return the cached response without reprocessing.</mark> <mark style="background: #ABF7F7A6;">If not, process the payment, cache the result with a TTL (24 hours), and return the response.</mark> This handles network retries safely.<mark style="background: #FFB8EBA6;"> The key insight: the TTL must be longer than any reasonable retry window.</mark>

**Q: What constitutes a breaking change in an API?**
A: Removing or renaming a field, changing a field's type, making an optional field required, or removing an endpoint. Non-breaking: adding new optional fields, new endpoints, new optional parameters. I follow the <mark style="background: #BBFABBA6;">**expand-contract pattern for migration**: add the new field, deprecate the old with a sunset header, give consumers time to migrate, then remove.</mark>

### Gotchas & What Impresses Interviewers
- Say "tolerant reader pattern" — consumers should ignore unknown fields; this future-proofs integrations
- Mention consumer-driven contract testing (Pact) for API stability in microservices
- Distinguish 401 (not authenticated) vs 403 (authenticated but not authorized) — many candidates get this wrong
- **Idempotency-Key pattern** is Stripe's standard — mentioning it shows real-world API awareness

---

## Day 1 Quick Reference

| Topic           | Key Interview Answer                                                              |
| --------------- | --------------------------------------------------------------------------------- |
| Decomposition   | Business capability → validate with DDD Bounded Context → team ownership test     |
| Saga            | Choreography for simple chains, Orchestration for complex flows with compensation |
| BFF             | ==Dedicated backend per client type==; owned by frontend team                     |
| Gateway vs Mesh | North-south (gateway) vs east-west (mesh); they coexist                           |
| Rate limiting   | ==Token bucket== for most cases; allows bursts, enforces average                  |
| REST level      | Target L2; mention L3 exists but impractical                                      |
| Versioning      | URI for public, Header for internal                                               |
| Idempotency     | Idempotency-Key + Redis cache; ==TTL > retry window==                             |
| Breaking change | Remove field/endpoint = breaking; add optional field = safe                       |

---

*Tags: #microservices #decomposition #saga #BFF #api-gateway #hld #lld #REST #idempotency #versioning #backward-compatibility*

---

[^1]: **Rate Limiting vs Throttling:** Rate limiting strictly caps the total number of requests in a time window and rejects excess. Throttling smooths traffic by queuing or delaying excess requests instead of rejecting them

[^2]: **SSL/TLS termination** (also called SSL/TLS offloading) is ==the process of decrypting encrypted web traffic (HTTPS) at the edge of a network—such as at a load balancer or reverse proxy (API Gateway)—before passing the unencrypted data to your backend servers.==

[^3]: **Request and response transformation** is ==the process of modifying the structure, data format, or metadata of an API call either before it reaches a backend service or before it returns to the client==. This action is primarily performed by API gateways or reverse proxies to decouple clients from backend changes, ensure security, and translate data structures seamlessly.

[^4]: An **API Gateway performs load balancing primarily at Layer 7 (the Application layer)** by ==analyzing incoming HTTP/HTTPS requests and distributing them across multiple healthy instances of backend microservices==. Unlike standard network load balancers that distribute raw traffic based on IP addresses, an API gateway uses application-level logic—such as request paths, headers, and service health—to route traffic intelligently.

[^5]: An ==**API Gateway achieves observability by acting as a centralized proxy** that intercepts all incoming traffic before it hits backend microservices==. Because it sits directly in the execution path, it can effortlessly extract telemetry data—**request logs, metrics, and traces**—without requiring any manual modifications to downstream code

[^6]: **K8S API Server:** Behind the API Server sits a database (called `etcd`). This database holds the master list (the **Registry**) of everything running in the cluster. It knows exactly which pods are alive, which services exist, and what their current IP addresses are.

[^7]: **Deprecated:** In technology, a "deprecated" feature or code is outdated but still usable, though developers are warned to stop using it as it will eventually be removed.
