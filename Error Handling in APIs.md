This is a paramount entry for your **`5_Web_API_Architecture`** note. In distributed systems, error handling isn’t just about catching an exception and throwing a string back to the user. It is a critical operational boundary that dictates your system's observability, security posture, and client integration resilience.

When an API fails, how it communicates that failure directly impacts MTTR (Mean Time to Resolution) for downstream engineering teams.

# Error Handling in Web APIs: Enterprise Architecture Blueprint

## I. The Three Levels of Error Classification
An elegant error handling framework separates errors by **ownership** and **actionability** before they leave the cluster boundary:
1. **Client Errors (Operational - 4xx Series):** The request failed because of something the client did wrong (bad payloads, missing auth, invalid states).
    - _System Behavior:_ Highly actionable by the consumer. The server remains healthy.
2. **Server Errors (Infrastructural/Bug - 5xx Series):** The request failed because of an unhandled code bug, database timeout, or dependency crash.
    - _System Behavior:_ Alerting mechanisms should fire. These are actionable **only** by internal engineers.
3. **Transient Errors (Network/Distributed - Mix of 4xx/5xx):** Temporary failures like rate-limits (`429`) or gateways dropping connections (`503`/`504`).
    - _System Behavior:_ Signals the client to back off and try again using specialized retry algorithms.

## II. Standardizing the Payload: RFC 7807 (Problem Details)
Never return inconsistent JSON payloads across different endpoints (e.g., `/users` returning `{"msg": "err"}` while `/orders` returns `{"error_code": 102}`).

The enterprise standard is **RFC 7807 (Problem Details for HTTP APIs)**. It enforces a predictable, machine-readable JSON schema for all error states.

### The RFC 7807 Standard Schema:

```JSON
{
  "type": "https://api.example.com/errors/insufficient-funds",
  "title": "Your account balance is too low.",
  "status": 400,
  "detail": "Your current balance is $12.50, but the transaction requires $50.00.",
  "instance": "/api/v1/accounts/acc_88392/transact",
  "invalid-params": [
    { "name": "amount", "reason": "Value exceeds maximum available overdraft limit." }
  ]
}
```

- **`type`**: A URI reference that points to documentation explaining the error code (allows clients to look up fix procedures).
- **`title`**: A short, human-readable summary of the problem type (should _never_ change for a specific error type).
- **`invalid-params`**: An optional extension array explicitly listing exactly which fields failed input validation rules.

## III. Crucial Enterprise Error Patterns

### 1. The Global Exception Handler Pattern (Application Layer)
Never let your controller endpoints catch and log exceptions independently. This creates massive code duplication and leaks structural data. Instead, implement a centralized global interceptor middleware (e.g., `@ControllerAdvice` in Spring Boot, or global Error Middleware in Express/Koa).

```
[Incoming Request] ──> [Controller Route] ──(Throws Uncaught Exception)──┐
                                                                         ▼
[Client Response] <── [Standardized RFC 7807 JSON] <── [Global Exception Interceptor]
```

- **The Benefit:** No matter where a code execution fails inside your application layer, it gets caught by the interceptor, mapped cleanly to an HTTP status code, sanitized, and serialized uniformly.

### 2. Error Sanitization & Data Leaks (Security Control)
A major security vulnerability is exposing raw database or language stack traces to public clients. Returning a `NullPointerException` or a `SQL Grammar Exception` gives malicious actors an intimate map of your internal infrastructure.
- **The Rule of Sanitization:** Your global interceptor must explicitly catch generic server errors, generate a distinct, random tracking ID (UUID), log the raw stack trace internally alongside that ID, and return _only_ the tracking ID to the external client.


```JSON
// Public Payload Returned to Client (Sanitized)
{
  "title": "Internal Server Error",
  "status": 500,
  "detail": "An unexpected error occurred. Please contact support with this Tracking Reference.",
  "error-tracking-id": "err_abc_12345"
}
```

## IV. Core HTTP Status Codes for Distributed Environments
Avoid status code proliferation; stick to a strict, highly communicative subset across your systems:

|**Status Code**|**Meaning**|**System Design Context**|
|---|---|---|
|**400 Bad Request**|Malformed Syntax / Validation|Input payload failed regex, type matching, or schema verification.|
|**401 Unauthorized**|Identity Missing or Invalid|The token is missing, expired, or has a broken cryptographic signature.|
|**403 Forbidden**|Identity Known but Disallowed|The token is valid, but the user's roles/scopes don't grant permission to this resource.|
|**404 Not Found**|Resource Missing|The endpoint path or the specific ID string does not exist in the database.|
|**409 Conflict**|State Mutation Clash|Concurrent update failure (e.g., two requests trying to book the exact same hotel room seat simultaneously—Optimistic Locking failure).|
|**422 Unprocessable Entity**|Syntactically Correct, Logically Broken|The JSON is perfectly valid, but business rules are violated (e.g., trying to process a delivery date set in the past).|
|**429 Too Many Requests**|Rate Limit Tripped|The client breached their allowed quota inside a specific sliding window.|
|**500 Internal Error**|Unhandled Code Bug|An uncaught error inside the app layer code itself.|
|**502 Bad Gateway**|Upstream Down|Proxy/Ingress cannot establish contact with the underlying application pod container.|
|**503 Service Unavailable**|Overloaded Engine|The backend is alive but rejecting connections due to database thread pool exhaustion or deliberate circuit breaker trips.|

## V. Observability: Correlating Errors with Distributed Tracing
An error log is completely useless in a microservice setup if you cannot trace the request path across multiple internal services.
- Every error response sent to an external client or passed between internal systems should automatically include a **Trace ID** header (`X-Trace-ID` or using W3C Trace Context standard headers).
- When an app service logs an exception to an external aggregator (ELK, Datadog), it must attach that specific trace ID to the log entry. This allows an engineer to take a single ID from a client's support ticket and instantly pull up the exact end-to-end journey of the request across all backend nodes.

### Suggested Cross-Links for your Knowledge Graph:

- `[[14_Resilience_Architecture]]` $\rightarrow$ Connect 503 errors directly to your **Circuit Breaker** and **Retry with Exponential Backoff** patterns.
- `[[28_Monitoring_Observability_Architecture]]` $\rightarrow$ Connect error payload tracking IDs to your logging and tracing pipelines.
- `[[32_Application_Security_Engineering]]` $\rightarrow$ Link data sanitization parameters directly to OWASP Top 10 API Security controls.