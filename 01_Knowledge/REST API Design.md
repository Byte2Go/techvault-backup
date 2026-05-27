## I. Core Architectural Constraints (The "Why")
<mark style="background: #ADCCFFA6;">REST is not a specification; it is an architectural style</mark> defined by six core constraints. In system design, these translate directly to performance and scalability:

- **Statelessness:** <mark style="background: #ABF7F7A6;">Every request from a client must contain all the information needed to understand and process the request.</mark> The server does not store session context.
    - _System Design Impact:_ <mark style="background: #BBFABBA6;">High availability</mark>. Any server node can handle any request, making <mark style="background: #BBFABBA6;">horizontal auto-scaling</mark> trivial.
- **Uniform Interface:** <mark style="background: #FFB86CA6;">Resources must be **uniquely identified (URIs)**</mark> and manipulated through standard representations (JSON/XML).
- **Cacheability:** <mark style="background: #ADCCFFA6;">Responses must explicitly define themselves as cacheable or not</mark> (via headers like `Cache-Control` or `ETag`) to prevent stale data while reducing server load.

## II. Resource Modeling & URI Design
<mark style="background: #D2B3FFA6;">URIs should represent **nouns (resources)**</mark>, never verbs (actions).
### 1. Hierarchical Relationships
Structure your URIs from collections to individual resources, and then sub-collections:
- `GET /api/v1/users` (Get all users)
- `GET /api/v1/users/{userId}` (Get a specific user)
- `GET /api/v1/users/{userId}/orders` (Get orders belonging to that specific user)

### 2. The "Action" Dilemma (Non-Resource Actions)
How do you handle actions that don't fit a clean CRUD noun? (e.g., locking an account, approving a transaction).
- **Anti-Pattern (RPC style):** `POST /api/v1/users/{id}/lockUser`
- **Sub-Resource Pattern:** Treat the state change as a resource itself.
    - `PUT /api/v1/users/{id}/lock`
- **Controller Pattern (Best for business processes):** Treat the action as a submission to an execution engine.
    - `POST /api/v1/transactions/{id}/approvals`

## III. Advanced HTTP Semantics: Idempotency & Safety
Understanding the mathematical guarantees of HTTP methods is critical for distributed system resilience:

| **Method** | **Safe?** | **Idempotent?** | **Architectural Behavior**                                                                                            |
| ---------- | --------- | --------------- | --------------------------------------------------------------------------------------------------------------------- |
| **GET**    | ✅ Yes     | ✅ Yes           | Reads data. Multiple calls return identical data (assuming no external mutations).                                    |
| **POST**   | ❌ No      | ❌ No            | ==Creates resources.== Executing twice creates two distinct resources.                                                |
| **PUT**    | ❌ No      | ✅ Yes           | Replaces/Upserts a resource completely. Executing multiple times results in the exact same state.                     |
| **PATCH**  | ❌ No      | ❌ No            | ==Partially modifies a resource.== _Can_ be idempotent if designed carefully, but inherently is not guaranteed.       |
| **DELETE** | ❌ No      | ✅ Yes           | Deletes a resource. The first call deletes it (200/204); subsequent calls return 404 but the _state_ remains deleted. |

### Implementing Idempotency for POST Requests
When a network glitch occurs during a credit card payment via `POST /payments`, the client retries. <mark style="background: #ABF7F7A6;">To prevent a double-charge, you must implement an **Idempotency Key Architecture**:</mark>

```
[Client] ─POST /payments(Header:X-Idempotency-Key: uuid-123)──> [API Gateway/App]
                                                                        │
                   ┌────── Checks Redis/DB for Key ─────────────────────┤
                   ▼                                                    ▼
 [Key Found: Processed]                                    [Key Not Found]
  Return cached 200 OK Response                           Save Key as "In-Flight"
  (Bypasses payment processor)      Execute Payment ──> Change State to "Success"
```

## IV. Enterprise REST Patterns

### 1. Filtering, Sorting, and Pagination
<mark style="background: #FF5582A6;">Never return raw, unbounded collections from a database.</mark>
- **Filtering:** Use <mark style="background: #BBFABBA6;">query parameters.</mark> `GET /api/v1/products?category=electronics&status=instock`
- **Sorting:** Standardize on a clear syntax. `GET /api/v1/products?sort=-price,createdAt` (The minus sign indicates descending).
- **Pagination:** 
	* _Offset-Based (`page=2&size=50`):_ Simple, but suffers from performance degradation on deep pages ($O(N)$ database scan) and misses/duplicates items if data changes mid-scroll.
    - ==_Cursor-Based== (`starting_after=prod_xyz`):_ High performance ($O(1)$ <mark style="background: #D2B3FFA6;">lookup using database indexes</mark>) and immune to data drifting. **Mandatory for high-throughput social/feed apps.**

### 2. Versioning Strategies
- **URL Path Versioning (Recommended for Public APIs):** `GET /api/v1/users`
    - _Pros:_ Explicit, <mark style="background: #BBFABBA6;">easily cacheable by standard CDNs and reverse proxies</mark>.
- **Header / Content Negotiation Versioning:** `GET /api/v1/users` with Header `Accept: application/vnd.company.v1+json`
    - _Pros:_ Keeps URIs pristine; clean representation of the underlying resource. Drops the caching burden onto custom `Vary` headers.

### 3. Asynchronous Long-Running Operations
If an API trigger takes <mark style="background: #FFB86CA6;">longer than 2-3 seconds</mark> (e.g., generating a massive PDF report), keeping the HTTP connection open invites gateway timeouts (504). <mark style="background: #FFB86CA6;">Use the **Asynchronous Request-Reply Pattern**</mark>:
1. Client sends request: `POST /api/v1/reports`
2. Server <mark style="background: #BBFABBA6;">responds immediately with **`202 Accepted`** and includes a **tracking location** header</mark>:
    `Location: /api/v1/reports/tasks/status-abc-123`
3. Client polls `GET /api/v1/reports/tasks/status-abc-123` which returns:
    - `200 OK` with status `PROCESSING`
    - Or `303 See Other` with a `Location: /api/v1/reports/file-999` once the job is finished.

## V. Defensive Design & Security Controls
- **Rate Limiting Metadata:** Always return `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers <mark style="background: #ABF7F7A6;">so clients can self-throttle before hitting hard</mark> `429 Too Many Requests` blockers.
- **Input Validation Responses:** Standardize errors using <mark style="background: #FFF3A3A6;">**RFC 7807 (Problem Details for HTTP APIs)**.</mark> Instead of raw exceptions, return structured JSON:

    ```JSON
    {
      "type": "https://api.example.com/errors/validation-error",
      "title": "Your request parameters didn't validate.",
      "status": 400,
      "invalid-params": [
        { "name": "email", "reason": "Must be a valid corporate email address" }
      ]
    }
    ```

- **Data Minimization:** Avoid `SELECT *`. <mark style="background: #ADCCFFA6;">Ensure your REST layer uses Data Transfer Objects (DTOs) to explicitly strip sensitive metadata </mark>(internal database IDs, passwords hashes) before serialization.

### Cross-Links for your Knowledge Graph:
- `[[6_Web_Request_Processing_Architecture]]` -> To map how these HTTP endpoints hit the internal server thread pools.
- `[[21_Backward_Compatibility_Data_Governance]]` -> To link API versioning directly with breaking change policies.
- `[[25_API_Gateway_Rate_Limiting]]` -> To map how your edge handles the 429 logic.