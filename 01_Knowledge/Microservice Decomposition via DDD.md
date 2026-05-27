Decomposition means breaking apart a single, giant application (a Monolith) into small, independent services (Microservices). We use **Strategic DDD** as the scalpel to decide exactly where to cut.

### 1. The Strategy: <mark style="background: #ABF7F7A6;">Bounded Context = Microservice Boundary</mark>
The industry standard rule is simple: <mark style="background: #ADCCFFA6;">**One Bounded Context should map directly to One Microservice.**</mark>

```
[ THE MONOLITH MONSTER ]
┌────────────────────────────────────────────────────────┐
│  Code Core (Shared DB Tables)                          │
│  [User Table] <──> [Order Code] <──> [Shipping Logic]  │
└────────────────────────────────────────────────────────┘
                           │
                           ▼ (Decomposition Cut)
                           
[ THE MICROSERVICE SOLUTION ]
┌─────────────────────────┐     Async Event     ┌─────────────────────────┐
│ CHECKOUT MICROSERVICE   │────────────────────►│ SHIPPING MICROSERVICE   │
│ (Database: Checkout DB) │     (via Kafka)     │ (Database: Shipping DB) │
└─────────────────────────┘                     └─────────────────────────┘
```

#### The Two Golden Rules of Cutting:

1. **Database per Service:** <mark style="background: #FFB86CA6;">Every microservice must own its own physical database tables</mark>. The Checkout Microservice cannot touch the Shipping Microservice's tables.
2. **Independent Deployments:** The Checkout team must be able to push new code to production on a Friday without needing permission, testing, or coordination from the Shipping team.
    
### 2. The Decomposition Process: Step-by-Step
When you are staring at a giant legacy codebase, you do not rewrite everything at once. You extract services one by one using this step-by-step sequence.

**Step 1: Identify Domain Subdomains:**  The Blueprint.
Analyze the business. Divide features into <mark style="background: #ADCCFFA6;">**Core**</mark> (makes you money, like custom pricing engines), <mark style="background: #ADCCFFA6;">**Supporting**</mark> (necessary but simple, like inventory tracking), and <mark style="background: #ADCCFFA6;">**Generic**</mark> (standard utilities, like email notifications).

**Step 2: Define Bounded Contexts:**  Language Lines.
Draw boundaries around specific <mark style="background: #FFF3A3A6;">language meanings</mark>. Group code where definitions match. (e.g., separate checkout code from delivery tracking code).

**Step 3: Isolate the Database First:** Data Segregation.
<mark style="background: #ABF7F7A6;">Break the shared database apart</mark> _before_ changing code. Separate your database tables logically into clean schemas, removing hard SQL `JOIN` statements across boundaries.

**Step 4: Extract Code as an Independent Unit:** The Cut.
<mark style="background: #D2B3FFA6;">Move the code into its own repository.</mark> <mark style="background: #ABF7F7A6;">Wrap it in a clean API (REST/gRPC) and put it on its own deployment pipeline (e.g., Docker/Kubernetes container).</mark>

### 3. Solving the Hardest Problem: Data Dependencies
The biggest trap during decomposition is data dependency: <mark style="background: #FFB8EBA6;">_What if Service A needs information that belongs to Service B?_</mark>

You have two practical industry strategies to handle this without building a slow network loop:
#### Strategy A: Asynchronous Data Replication (High Performance)
Instead of calling Service B over the network every single time you need data, <mark style="background: #ABF7F7A6;">Service A keeps a lightweight, read-only cache clone</mark> of the data inside its own database.

```
[Service B (Owner)] ──► (Publishes Event) ──► [Kafka] ──► [Service A] ──► (Saves Local Copy)
```

- **Example:** The Checkout service needs to know if a user's account is active before letting them buy items.
- **The Blueprint:** Checkout doesn't call the User service via HTTP during payment. Instead, it listens to a `UserStatusChanged` Kafka event stream and <mark style="background: #FFF3A3A6;">maintains a simple `Local_Users` look-up cache table inside its own Checkout Database.</mark> Lookups are instant and completely local.

#### Strategy B: The Strangler Fig Pattern (Safe Migration)
If you are moving from an old monolith to microservices, you don't turn off the monolith overnight. You <mark style="background: #D2B3FFA6;">place **a routing proxy** (like an API Gateway) in front of the application.</mark>

```
                       ┌──► [ New Microservice (Handles extracted API routes) ]
                       │
[ API GATEWAY PROXY ] ─┤
                       │
                       └──► [ Legacy Monolith  (Handles remaining old routes) ]
```

The gateway slowly routes traffic away from the monolith to the new microservice, one single API path at a time. The monolith "strangles" over a year until it can be turned off safely.

### Summary Checklist for your Obsidian Notes

> **"Microservice Decomposition Manifesto:**
> 1. <mark style="background: #FFB8EBA6;">**Never Cut Code First:**</mark> <mark style="background: #ADCCFFA6;">Always separate your shared database layers into isolated schemas</mark> before splitting your backend code repositories.
> 2. <mark style="background: #FF5582A6;">**Ban Synchronous HTTP Chains:**</mark> If Service A must hit Service B, which then hits Service C just to load a single page, your architecture is broken. <mark style="background: #BBFABBA6;">Use Kafka event replication to keep data local.</mark>
> 3. **Size by Team, Not Code:** <mark style="background: #ADCCFFA6;">A microservice is the right size if a small team of 5–8 developers can fully manage,</mark> understand, and deploy it independently."