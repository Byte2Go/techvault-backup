### PATTERN 1: IDENTITY THEFT (They pretend to be someone else)

| Vulnerability Name and  Attack                                                                                                 | The Real Root Cause                                         | The Architectural Fix                                                                                                                                                                |
| :----------------------------------------------------------------------------------------------------------------------------- | :---------------------------------------------------------- | :----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **BOLA** (Broken Object Level Authorization) => Hacker tries `GET /orders/1002` to see someone else's order                    | Code checks "Are you logged in?" but NOT "Do you own this?" | **Database-level ownership filtering** - Add user ID to every query                                                                                                                  |
| **BFLA** (Broken Function Level Authorization) => Normal user calls `DELETE /admin/users/999`                                  | Admin endpoints lack role checks                            | **Method-level security** - Annotate endpoints with `@PreAuthorize("hasRole('ADMIN')")`                                                                                              |
| **SSRF** (Server-Side Request Forgery) => Hacker submits `{"avatar": "http://169.254.169.254/latest/"}` to read cloud metadata | Server blindly fetches user-provided URLs                   | [[K8S Security-  Egress Proxy]]   **Egress proxy with blocklists (outbound network traffic leaving your private cloud environment ) ** - Route through proxy that blocks private IPs |
| **Broken Authentication** => Hacker brute-forces "admin/password123"                                                           | Weak passwords, no MFA, unlimited attempts                  | **Strong auth policies** - MFA, password complexity, login rate limiting                                                                                                             |

---
### PATTERN 2: DATA MANIPULATION (They change things they shouldn't)

| Vulnerability Name and  Attack                                                               | The Real Root Cause                                       | The Architectural Fix                                                                      |
| -------------------------------------------------------------------------------------------- | --------------------------------------------------------- | ------------------------------------------------------------------------------------------ |
| **Mass Assignment** => Hacker adds `"role":"ADMIN"` to profile update JSON                   | System saves ALL fields from request directly to database | **[[DTO (Data Transfer Object)]] boundaries** - Only allow specific fields in request DTOs |
| **Unsafe API Consumption** => Third-party API returns `{"temp": "25'; DROP TABLE users;--"}` | System blindly trusts external API responses              | **Schema validation + parameterized queries** - Validate all external data                 |
| **Security Misconfiguration** => Debug mode enabled in production exposing stack traces      | Default/insecure settings left unchanged                  | **Secure defaults** - ==Disable debug, HTTPS only, remove default passwords==              |
| **Business Logic Abuse** => Bot automates checkout 10,000 times to drain loyalty points      | ==No limits on sensitive business operations==            | **Flow rate limiting** - CAPTCHA, daily limits, anomaly detection                          |

---
### PATTERN 3: RESOURCE EXHAUSTION (They overwhelm your system)

| The Attack                                                                         | The Real Root Cause                     | The Architectural Fix                                                 |
| ---------------------------------------------------------------------------------- | --------------------------------------- | --------------------------------------------------------------------- |
| **Unrestricted Resource Consumption**=> Botnet fires 50,000 search requests/second | No limits on request rate or complexity | [[Distributed Rate Limiting]] - Redis-backed token buckets at Gateway |

---
### PATTERN 4: DISCOVERY (They find hidden weaknesses)

| OWASP ID | Vulnerability Name | The Attack | The Real Root Cause | The Architectural Fix |
|----------|-------------------|------------|-------------------|---------------------|
| **API9** | **Shadow APIs** | Hacker finds forgotten `/api/v1/users` with no security | Old endpoints remain running without routing maps | **Gateway allow-lists** - Only explicitly defined routes get through |

---

## THE QUICK REFERENCE: 4 Architectural Boundaries
When an interviewer asks "How do you secure APIs?", don't list 10 items. Give them **these 4 layers**:

```
┌─────────────────────────────────────────────────────────────────┐
│                   1. GATEWAY PERIMETER                          │
│                   (API Gateway Layer)                           │
│                                                                 │
│   ✅ Rate Limiting (Redis token buckets)                       │
│   ✅ Route Allow-List (Only defined paths pass)                │
│   ✅ Extract User Context (Parse JWT once, reuse)              │
│                                                                 │
│  Fixes: API4 (Resource Exhaustion), API9 (Shadow APIs)          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   2. CONTROLLER BOUNDARY                        │
│                   (Spring Security/Controller Layer)            │
│                                                                 │
│  ✅ DTO Validation (Only allowed fields accepted)              │
│  ✅ Role Checks (@PreAuthorize)                                │
│  ✅ Input Validation (Validate all user input)                 │
│                                                                 │
│  Fixes: API3 (Mass Assignment), API5 (BFLA)                     │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   3. DATA ACCESS LAYER                          │
│                   (Repository/DAO Layer)                        │
│                                                                 │
│  ✅ Ownership Queries (Always filter by user ID)                │
│  ✅ Parameterized Queries (No SQL injection)                    │
│  ✅ Field-Level Security (Only return allowed fields)           │
│                                                                 │
│  Fixes: API1 (BOLA), API10 (Unsafe Consumption)                 │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                   4. EGRESS BOUNDARY                            │
│                   (Outbound Network Layer)                      │
│                                                                 │
│  ✅ Proxy with Blocklists (Block private IPs)                   │
│  ✅ Timeout Controls (Don't wait forever)                       │
│  ✅ Response Validation (Validate external data)                │
│                                                                 │
│  Fixes: API7 (SSRF), API10 (External API attacks)               │
└─────────────────────────────────────────────────────────────────┘
```

---
## SUMMARY: What to Remember

| Layer | Fixes | Vulnerabilities |
|-------|-------|-----------------|
| **Gateway** | Rate limiting, route allow-list | API4, API9 |
| **Controller** | DTOs, role checks | API3, API5, API8 |
| **Data Layer** | Ownership queries | API1, API10 |
| **Egress** | Proxy with blocklists | API7 |

**The Golden Rule:** 
> **Never trust user input, always check ownership, always validate roles, always limit requests.**

```
"I would build a defense-in-depth architecture with 4 layers:

1. GATEWAY: Rate limiting + route validation
2. CONTROLLER: DTOs + role-based access
3. DATA: Ownership filtering in all queries
4. EGRESS: Proxy to block internal network access

This covers all OWASP Top 10 vulnerabilities by design,
not by adding patches one by one."

```
