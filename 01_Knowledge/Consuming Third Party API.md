Consuming third-party APIs means connecting your own internal enterprise systems to external services, vendors, SaaS platforms, or financial providers.

<mark style="background: #FFF3A3A6;">Unlike exposing an API where you make the rules</mark>, <mark style="background: #FFB8EBA6;">consuming an API means you are at the mercy of an external system.</mark> <mark style="background: #FF5582A6;">You do not control their uptime, their performance, or their network stability.</mark> Because of this, <mark style="background: #ADCCFFA6;">your architecture must be highly defensive to prevent external failures from breaking your application</mark>.

---
## 🏗 Typical Integration Flow
When your application calls an external API, the request must pass through a dedicated integration layer designed to protect your system:

```
[Internal Service] ──> [API Client Wrapper] ──> [Circuit Breaker / Timeout] ──> [External API]
```

1. **Internal Service:** Your core business logic that needs external data (e.g., an Order Service that needs to process a payment).
2. **API <mark style="background: #FFB86CA6;">Client Wrapper</mark>:** A dedicated code module that <mark style="background: #FFB86CA6;">translates your internal data into the specific format </mark>required by the vendor. This isolates the vendor's specific design from the rest of your codebase.
3. **Resilience Layer:** Software guards (like timeouts and circuit breakers) that <mark style="background: #ABF7F7A6;">monitor the network call and step in immediately</mark> <mark style="background: #ADCCFFA6;">if the external API slows down or crashes.</mark>
---
## 🔒 Key Architectural Concerns
An architect must address four main risk areas when integrating an external API:
### 1. Reliability (What if they slow down or crash?)
- **Timeout Management:** <mark style="background: #ADCCFFA6;">Never wait indefinitely for a response</mark>. If a vendor API usually takes 200 milliseconds but suddenly takes 10 seconds, <mark style="background: #FF5582A6;">your system will pool open threads and crash</mark>. <mark style="background: #FFB86CA6;">Set strict timeouts (e.g., maximum 2 seconds) and cut the connection if they take too long.</mark>
- **The Retry Pattern:** If a call fails due to a temporary network glitch, try again automatically. Always use **exponential backoff** (waiting longer between each retry, like 1 second, then 2 seconds, then 4 seconds) so you do not accidentally flood a struggling vendor with requests.
- **The Circuit Breaker:** <mark style="background: #FFF3A3A6;">If the external API fails completely or times out repeatedly, the circuit breaker "trips" open.</mark> For the next few minutes, all internal requests to that vendor fail instantly without wasting network resources, protecting your system's uptime.
### 2. Operational Risk (What if they change things?)
- **SLA Mismatch:** If your application promises $99.9\%$ uptime to your customers, but your core payment vendor only guarantees $99\%$ uptime, <mark style="background: #FF5582A6;">your system is mathematically exposed to operational failure.</mark>
- **Contract Changes:** External vendors can change their data schemas or deprecate API versions. <mark style="background: #FFB86CA6;">Your client wrapper must validate incoming responses</mark> <mark style="background: #ABF7F7A6;">to ensure mandatory fields exist before passing that data deep into your core business logic.</mark>
### 3. Security (How do we protect access?)
- **Secret Management:** Never hardcode API keys, client secrets, or OAuth2 credentials directly into your source code. Store them securely in an <mark style="background: #BBFABBA6;">environment variable manager or a dedicated vault.</mark>

### 4. Data Concerns (What if we send duplicates?)
- **Idempotency:** Networks are unreliable. Sometimes you send a request (like "Charge $100"), the vendor processes it successfully, but the network drops before they can send you the confirmation. <mark style="background: #FF5582A6;">If you blindly retry, the customer gets charged twice. </mark><mark style="background: #FFB86CA6;">You must pass a unique **Idempotency Key** so the vendor knows it is the exact same transaction request.</mark>

---
## 🔄 Common Integration Patterns

- **Direct Sync Calls (REST/GraphQL):** Making a live request and waiting on the line for an immediate answer (e.g., asking a tax API to calculate sales tax during a checkout flow).
- **Webhook Callbacks:** Instead of waiting on the line for a slow process to finish, <mark style="background: #ADCCFFA6;">you give the vendor an API endpoint on your system.</mark> <mark style="background: #ABF7F7A6;">The vendor calls you back the moment the job is done</mark> (e.g., a background fraud check takes 5 minutes, and the vendor hits your webhook when finished).
- **Fallback Strategy:** What happens when the vendor is totally down? A great architecture has a backup plan. For example, if your primary SMS notification provider goes offline, your system instantly routes the text messages through a secondary backup provider.
---
## ⚠️ Common Mistakes to Avoid
- **Infinite Retries:** <mark style="background: #FF5582A6;">Retrying a failed call forever in a tight loop</mark>. <mark style="background: #FFF3A3A6;">This acts like a self-inflicted DDoS attack</mark> <mark style="background: #FF5582A6;">that eats your own server memory and destroys</mark> the vendor's chances of recovering.
- **Vendor Contract Leakage:** Allowing the vendor's specific data structures to pass deeply into your databases or internal services. If you switch vendors next year, you will be forced to rewrite your entire application. <mark style="background: #FFB86CA6;">Keep the vendor models strictly contained inside the **client wrapper**</mark>.
- **Assuming Happy Paths:** Designing code assuming the external system will always be online, fast, and accurate.

---

## 🧠 The Architect's Core Rule

Assume every third-party API is **unreliable by default**.

Your primary goal when consuming an external API is **blast radius minimization**. If a third-party shipping calculator goes down, your users should still be able to log in, browse products, and view their shopping carts. <mark style="background: #BBFABBA6;">Never let a failure at an external company become a fatal crash for your own business.</mark>

---

## 🔗 Related Concepts
- **[[Circuit Breaker Pattern]]**: Automatically stopping requests to a failing network target to protect system resources.
- **[[Saga Pattern]]**: Managing distributed transactions and running "compensating actions" (like issuing a refund) if a later step in a multi-API workflow fails.
- **[[Idempotency Thinking]]**: Designing safe network retry mechanics to eliminate the risk of duplicate data processing.