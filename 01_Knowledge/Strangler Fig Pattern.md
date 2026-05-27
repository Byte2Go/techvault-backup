# The Strangler Fig Strategy

Instead of a high-risk "big bang" rewrite of a legacy monolith, you <mark style="background: #BBFABBA6;">gradually replace specific functionalities with new services</mark> piece-by-piece using <mark style="background: #FFB86CA6;">an network router</mark>. Once the migration is complete and the monolith is decommissioned and the role of Network Router changes from an **intercepting router to a permanent Ingress Controller / API Gateway**. 

---
## 🧭 The Evolution of the Router

### Stage 1: During the Migration (The "Strangler" Phase)

While breaking down the monolith, the <mark style="background: #ABF7F7A6;">router functions as a **Smart Interceptor** inspecting incoming HTTP paths</mark>:
- If a request is for an unmigrated feature (`/orders`), it routes it to the **Monolith**.
- If a request is for a newly migrated feature (`/payments`), it routes it to the new **Microservice**.

### Stage 2: After the Migration (The Permanent API Gateway)
Once the legacy system is gone, the router cleanly transitions into its permanent role as an **API Gateway / Ingress Controller** (e.g., NGINX, Kong, or AWS API Gateway). Its daily job shifts to handling standard platform responsibilities:
- **Central Entry Point:** Serves as the single URL <mark style="background: #FFF3A3A6;">layer for all client traffic</mark>.
- **Reverse-Proxy Routing:** Maps out paths across the decoupled ecosystem (e.g., `/payments` to the payment service, `/users` to the user service).
- **Cross-Cutting Concerns:** Centrally manages <mark style="background: #ABF7F7A6;">**Rate Limiting**, **SSL Termination**, **Authentication/Authorization**, and **Global Logging**</mark>.

---
## 💾 The Strangler Fig Database Strategy
You cannot just decouple the code; you must decouple the data. During a Strangler Fig migration, you use a <mark style="background: #D2B3FFA6;">**Database Decomposition** strategy</mark> governed by a strict rule of thumb: <mark style="background: #ADCCFFA6;">**The service that owns the business logic must own its data</mark>.**

### 1. The Isolated Target State
When you extract a feature (e.g., the Payment Service), you spin up a brand-new, isolated **Payment Database** completely dedicated to that service. The legacy monolith database retains only the remaining unmigrated data (e.g., Users, Orders, Inventory).
### 2. The Golden Rule of Data Access
Once the new service is live, <mark style="background: #FFB8EBA6;">**direct cross-database access is strictly forbidden**</mark>.
- The Monolith cannot read or write directly to the New DB. If it needs payment data, it <mark style="background: #ABF7F7A6;">_must_ request it via the new **Payment Service API**</mark>.
- The New Service cannot query the Monolith DB directly. If it needs user profile data, it <mark style="background: #ABF7F7A6;">_must_ fetch it via the **Monolith's API**</mark>.
### 3. Phased Data Migration (Handling Shared Data)
If the new service relies on data historical to the monolithic database, you migrate it using a safe, three-phase approach:
- **Phase A (Sync):** Deploy the new service with its separate database. <mark style="background: #D2B3FFA6;">Use data synchronization tools or background event workers to replicate relevant data tables</mark> from the old DB to the new DB in real-time.
- **Phase B (Cutover):** <mark style="background: #FFB86CA6;">Once the data is verified to be identical, flip the system write-switch</mark>. <mark style="background: #D2B3FFA6;">All new writes go directly to the new service API</mark> and its database, establishing it as the new **Source of Truth**.
- **Phase C (Cleanup):** Safely drop and delete the obsolete tables from the legacy monolithic database to complete the decomposition.