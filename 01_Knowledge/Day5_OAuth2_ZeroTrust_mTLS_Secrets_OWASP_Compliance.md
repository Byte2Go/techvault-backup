# P4 · Day 5 — OAuth2/OIDC · Zero Trust · mTLS · Secrets · OWASP · Compliance
**Pillar:** P4 — Security Architecture  
**Role Priority:** SA 🔵 Core · Java ⚪ Supporting · AI ⚪ Supporting  
**Day in Plan:** Day 5 (Week 1)  
**Time:** ~3 hours study + 1 hour Q&A practice

> **Cross-reference:** Service Mesh (Istio/Linkerd) and Zero Trust architecture patterns were covered in Day 2 notes. This day focuses on the security design layer — auth flows, secrets, API security, and compliance.

---

## Topic 1 · OAuth2 & OIDC — Flows You Must Know

### In One Line
OAuth2 is an authorization framework; OIDC adds identity on top — together they are the standard for securing modern APIs and user login flows.

### OAuth2 Roles
```
Resource Owner  = User (owns the data)
Client          = Application requesting access (SPA, mobile app, microservice)
Authorization Server = Issues tokens (Keycloak, Auth0, AWS Cognito, Okta)
Resource Server = API that accepts tokens (your microservice)
```

### Flow 1 — Authorization Code + PKCE (for SPAs & Mobile Apps)

```
1. User clicks "Login"
2. SPA → redirects to Auth Server:
   GET /authorize?response_type=code
     &client_id=spa-client
     &redirect_uri=https://app.company.com/callback
     &scope=openid profile orders:read
     &code_challenge=<PKCE challenge>      ← prevents auth code interception
     &state=<random value>                 ← CSRF protection

3. User authenticates at Auth Server (login page)
4. Auth Server → redirects back:
   https://app.company.com/callback?code=ABC123&state=<same value>

5. SPA → exchange code for tokens:
   POST /token
   grant_type=authorization_code
   code=ABC123
   code_verifier=<PKCE verifier>          ← proves it's the same client

6. Auth Server → returns:
   { "access_token": "jwt...",            ← short-lived (15 min)
     "refresh_token": "opaque...",        ← long-lived (7 days)
     "id_token": "jwt...",               ← OIDC — user identity
     "expires_in": 900 }

7. SPA calls API:
   GET /orders
   Authorization: Bearer <access_token>

8. Resource Server validates JWT:
   → Check signature (public key from Auth Server JWKS endpoint)
   → Check exp, iss, aud claims
   → Extract scopes → authorize action
```

**PKCE (Proof Key for Code Exchange):** Public clients (SPAs, mobile) can't keep a client secret. PKCE replaces the secret — client generates a random verifier, hashes it as the challenge, sends hash to auth server, then proves it has the original verifier when exchanging the code. Prevents authorization code interception attacks.

### Flow 2 — Client Credentials (Service-to-Service)

```
Service A (Client) → POST /token
  grant_type=client_credentials
  client_id=order-service
  client_secret=<secret>                  ← stored in Vault/Secrets Manager
  scope=payments:write

Auth Server → { "access_token": "jwt...", "expires_in": 3600 }

Service A → POST /payments
  Authorization: Bearer <access_token>

Payment Service → validates token (same JWT validation)
```

**Use for:** Machine-to-machine — microservice calling another microservice, batch job calling API, CI/CD calling internal API.  
**Not for:** User-facing flows — no user context in the token.

### Flow 3 — Implicit Flow (DEPRECATED — DO NOT USE)
- Returned token directly in URL fragment — visible in browser history, logs, referrer headers
- Replaced entirely by Auth Code + PKCE for SPAs

### JWT Structure & Validation

```
Header.Payload.Signature (Base64url encoded, dot-separated)

Header: { "alg": "RS256", "kid": "key-id-1" }
Payload: {
  "sub": "user-123",           ← subject (user ID)
  "iss": "https://auth.company.com",  ← issuer
  "aud": "order-service",      ← audience (which service this token is for)
  "exp": 1749999999,           ← expiry (Unix timestamp)
  "iat": 1749999099,           ← issued at
  "scope": "orders:read orders:write",
  "roles": ["CUSTOMER", "PREMIUM"]
}
Signature: RS256(base64(header) + "." + base64(payload), privateKey)
```

**Validation steps (resource server must do ALL):**
1. Verify signature using auth server's public key (fetched from JWKS endpoint)
2. Check `exp` — reject if expired
3. Check `iss` — must match expected issuer
4. Check `aud` — must include this service's identifier
5. Check `nbf` (not before) if present
6. Extract `scope` / `roles` → enforce authorization

### JWT Hygiene Rules

| Rule | Reason |
|---|---|
| Short expiry (15 min) for access tokens | Limits blast radius if stolen |
| Refresh tokens in HttpOnly cookie | JS can't steal them (XSS protection) |
| Never store access tokens in localStorage | XSS trivially reads localStorage |
| Rotate refresh tokens on use (refresh token rotation) | Detects token theft — old refresh token becomes invalid |
| Include `aud` claim, validate it | Prevents a token for Service A being used at Service B |
| Use RS256 (asymmetric) not HS256 (symmetric) | Resource servers need only public key — no shared secret |
| Token revocation via short expiry + blacklist | JWTs are stateless — revoke via Redis blacklist on logout |

### Interview Q&A (40L SA Level)

**Q: Explain the OAuth2 Authorization Code flow with PKCE.**
A: The user is redirected to the Authorization Server, which authenticates them and returns an authorization code. The SPA exchanges this code (plus the PKCE verifier) for an access token and refresh token. PKCE replaces client secrets for public clients — the client generates a random verifier, sends its hash to the auth server, and proves it has the original verifier during exchange. This prevents an attacker who intercepts the authorization code from using it without the verifier. The access token is kept in memory (not localStorage), and the refresh token in an HttpOnly cookie.

**Q: When would you use Client Credentials vs Authorization Code flow?**
A: Authorization Code is for user-facing applications — a human authenticates and the token carries their identity and consent. Client Credentials is for machine-to-machine — Service A authenticating to Service B with no user context. In a microservices system: the external-facing API uses Authorization Code (user logs in, token has their claims), while internal service-to-service calls use Client Credentials (order-service authenticates to payment-service as itself).

**Q: Why is the Implicit flow deprecated?**
A: The Implicit flow returned tokens directly in the URL fragment (hash) — visible in browser history, server logs, and HTTP referrer headers. It was designed before PKCE existed. Authorization Code + PKCE solves the same problem (no client secret for public clients) without leaking tokens in URLs. No new systems should use Implicit flow.

---

## Topic 2 · Zero Trust Architecture (Security Design)

### In One Line
Zero Trust is a security model: never trust any request based on network location alone — verify identity, device, and context on every request.

### Core Principles

```
1. Verify Explicitly       — authenticate and authorize every request (user + device + context)
2. Least Privilege Access  — minimum permissions needed for the job, time-limited
3. Assume Breach           — design as if attacker is already inside; segment, detect, respond
```

### Zero Trust in a Microservices Architecture

```
External User Request:
  Browser → [WAF] → [CDN] → [API Gateway]
                              ↓ validates JWT
                        [Order Service]
                              ↓ mTLS + AuthorizationPolicy
                        [Payment Service]
                              ↓ mTLS
                        [Payment DB]

Controls at each hop:
  API Gateway:    JWT validation, rate limiting, WAF rules
  Service Mesh:   mTLS between services, AuthorizationPolicy (which service → which service)
  Service:        Fine-grained authorization (does this user have permission for THIS order?)
  DB:             Least privilege DB user (SELECT-only for reads, no DROP TABLE)
```

### Identity Propagation
In Zero Trust, user identity flows through all service calls:
```
User JWT → API Gateway → Order Service → Payment Service
                                ↓
               Propagate user context via:
               - JWT forwarded (validate at each service)
               - or: service extracts userId, passes in header X-User-Id
               - or: service issues a new internal JWT (with user context)
```

### Network Segmentation
```
VPC → Subnets → Security Groups → NACLs → Service Mesh AuthorizationPolicy
Each layer reduces blast radius:
  - Payment DB only accessible from Payment Service SG
  - Payment Service only callable from Order Service (mesh policy)
  - No service directly calls DB of another service
```

### Zero Trust vs Perimeter Security

| Perimeter | Zero Trust |
|---|---|
| Trust inside network | Trust nothing, verify everything |
| VPN = safe | VPN = one more thing to compromise |
| North-South traffic secured | All traffic secured (N-S + E-W) |
| "Castle and moat" | "Assume breach" |

---

## Topic 3 · mTLS Between Services

### In One Line
mTLS (mutual TLS) means both client AND server present certificates — not just server proving identity to client (standard TLS), but both sides proving identity to each other.

### Standard TLS vs mTLS

```
Standard TLS:
  Client → connects → Server presents certificate
  Client verifies server cert → encrypted tunnel established
  (Server doesn't know WHO the client is)

mTLS:
  Client → connects → Server presents certificate
  Client verifies server cert
  Server requests client certificate
  Client presents certificate → Server verifies
  → encrypted tunnel where BOTH sides are authenticated
```

### Why mTLS for Microservices

Without mTLS inside cluster:
- Any pod that can reach Payment Service can call it (no identity)
- Attacker who compromises any service → lateral movement to any other service

With mTLS:
- Payment Service only accepts connections from services with valid certificates
- Certificate = service identity (SPIFFE ID: `spiffe://cluster.local/ns/production/sa/order-service`)
- Compromised service can only call what its certificate permits (+ AuthorizationPolicy)

### mTLS via Service Mesh (Istio)

```yaml
# Enable mTLS in STRICT mode (reject plain-text)
apiVersion: security.istio.io/v1beta1
kind: PeerAuthentication
metadata:
  name: default
  namespace: production
spec:
  mtls:
    mode: STRICT   # PERMISSIVE allows plain-text (dev only) — STRICT = production

---
# Allow only order-service to call payment-service
apiVersion: security.istio.io/v1beta1
kind: AuthorizationPolicy
metadata:
  name: payment-service-policy
  namespace: production
spec:
  selector:
    matchLabels:
      app: payment-service
  rules:
  - from:
    - source:
        principals: ["cluster.local/ns/production/sa/order-service"]
    to:
    - operation:
        methods: ["POST"]
        paths: ["/payments"]
```

### Certificate Management
- Istio uses its own CA (Citadel/istiod) to issue and rotate certificates automatically
- Certificates rotate every 24 hours by default — no manual cert management
- Certificate = SPIFFE ID tied to Kubernetes ServiceAccount → service identity

---

## Topic 4 · Secrets Management

### In One Line
Secrets (DB passwords, API keys, TLS certs) must never be in code, config files, or environment variables in plaintext — use a dedicated secrets manager with rotation and audit.

### The Problem with Secrets in Code/Config
```
# BAD — all of these are insecure
application.properties: spring.datasource.password=mysecret123
Dockerfile ENV: ENV DB_PASSWORD=mysecret123
Kubernetes ConfigMap: data: db-password: mysecret123  ← ConfigMaps are NOT encrypted
```

What goes wrong: leaked in Git history, visible to anyone with kubectl access, no rotation, no audit.

### HashiCorp Vault

**Architecture:**
```
App → authenticate to Vault (using k8s ServiceAccount)
   → Vault verifies identity via k8s token review API
   → returns short-lived secret (or dynamic credential)
   → App uses secret → secret auto-expires

Dynamic secrets (Vault killer feature):
  App requests DB credentials → Vault creates a NEW DB user (e.g., v-order-svc-abc123)
  → credentials valid for 1 hour → auto-revoked after 1 hour
  → no long-lived shared DB passwords
```

**Spring Boot integration:**
```yaml
# application.yml
spring:
  config:
    import: vault://
  cloud:
    vault:
      uri: https://vault.company.com
      authentication: KUBERNETES
      kubernetes:
        role: order-service
      kv:
        enabled: true
        backend: secret
        default-context: order-service
```

### AWS Secrets Manager

```java
// Retrieve secret in Java
SecretsManagerClient client = SecretsManagerClient.builder()
    .region(Region.AP_SOUTH_1)
    .build();

GetSecretValueResponse response = client.getSecretValue(
    GetSecretValueRequest.builder()
        .secretId("production/order-service/db-credentials")
        .build()
);

String secret = response.secretString();  // JSON string with credentials
```

**Auto-rotation:** AWS Secrets Manager rotates RDS credentials automatically (Lambda function handles rotation) — no app restart needed if using latest secret on each connection.

### Kubernetes Secrets — Not Enough Alone

```yaml
# Kubernetes Secret — base64 encoded, NOT encrypted by default
apiVersion: v1
kind: Secret
metadata:
  name: db-credentials
type: Opaque
data:
  password: bXlzZWNyZXQxMjM=  # Just base64, not encrypted!
```

**Harden with:**
- **Encryption at rest** — enable EncryptionConfiguration (KMS) for etcd
- **External Secrets Operator** — syncs from Vault/AWS Secrets Manager into k8s Secrets automatically
- **Sealed Secrets** (Bitnami) — encrypt secrets in Git (can only be decrypted by cluster)

### Secrets Best Practices

| Practice | Reason |
|---|---|
| Never commit secrets to Git | Git history is permanent |
| Rotate secrets regularly | Limits blast radius if leaked |
| Audit all secret access | Who accessed what, when |
| Least privilege per secret | Order service reads DB password; cannot read payment keys |
| Use dynamic secrets where possible | Auto-expiring > long-lived shared credentials |
| Environment-specific secrets | Dev secrets ≠ prod secrets |

### Interview Q&A
**Q: How do you manage database credentials in a Kubernetes microservices environment?**
A: External Secrets Operator syncing from AWS Secrets Manager or HashiCorp Vault into Kubernetes Secrets — Secrets Manager handles rotation automatically, the operator syncs changes to the cluster. In the app, credentials are injected as environment variables from the Secret (not hardcoded). For highest security, I use Vault's dynamic secrets — Vault creates a unique, time-limited DB user per app instance, so there's never a shared long-lived password. All secret access is audited in Vault/CloudTrail.

---

## Topic 5 · OWASP Top 10 for APIs (API Security Architect Must-Know)

### In One Line
OWASP API Security Top 10 lists the most critical API vulnerabilities — an SA designing APIs must know these and architect controls against each.

### OWASP API Security Top 10 (2023)

**API1 — Broken Object Level Authorization (BOLA)**
```
GET /orders/12345  ← User A gets Order 12345 (belongs to User B) — just by guessing the ID
```
Fix: Every request must verify the authenticated user owns the resource being accessed.
```java
Order order = orderRepo.findById(orderId);
if (!order.customerId().equals(currentUser.id())) {
    throw new ForbiddenException();
}
```

**API2 — Broken Authentication**
- Weak tokens, no expiry, tokens in URLs, no brute-force protection
- Fix: Short-lived JWTs, PKCE, MFA for sensitive operations, rate limit auth endpoints

**API3 — Broken Object Property Level Authorization**
- User can update fields they shouldn't (e.g., changing their own role to ADMIN via PATCH)
- Fix: Explicit allow-list of updatable fields; never deserialize user input directly to domain object

**API4 — Unrestricted Resource Consumption**
- No rate limits → DDoS, cost explosion (AI API), DB overload
- Fix: Rate limiting at API Gateway (per user, per IP), request size limits, pagination on list endpoints

**API5 — Broken Function Level Authorization**
- Admin endpoints accessible to regular users (e.g., `DELETE /admin/users/{id}`)
- Fix: Role-based authorization on every endpoint; admin endpoints in separate namespace

**API6 — Unrestricted Access to Sensitive Business Flows**
- Automated abuse of business flows (buy all limited stock via bots, create fake accounts in bulk)
- Fix: CAPTCHA, device fingerprinting, rate limits per business action, anomaly detection

**API7 — Server Side Request Forgery (SSRF)**
- API accepts a URL parameter and fetches it server-side → attacker points it at internal services
```
POST /import { "url": "http://169.254.169.254/latest/meta-data/" }  ← AWS metadata!
```
Fix: Validate and whitelist allowed URL schemes/hosts; block private IP ranges

**API8 — Security Misconfiguration**
- Default credentials, verbose error messages (stack traces in prod), unnecessary HTTP methods
- Fix: Security headers (HSTS, CSP, X-Frame-Options), disable debug endpoints, custom error handler

**API9 — Improper Inventory Management**
- Old API versions still running and unprotected, undocumented internal APIs exposed
- Fix: API catalog, deprecation policy, decommission old versions, API Gateway routes only known versions

**API10 — Unsafe Consumption of APIs**
- Your service blindly trusts a third-party API response → injection, redirect attacks
- Fix: Validate and sanitize all data from external APIs; don't pass raw external data to DB

### Key Controls to Architect

```
Input Validation:     Validate all inputs server-side (size, type, format, range)
Output Encoding:      Encode output to prevent injection in consumers
Auth on Every Endpoint: No "public" endpoints without deliberate decision
Rate Limiting:        Per user, per IP, per API key at gateway level
Security Headers:     HSTS, CSP, X-Content-Type-Options, X-Frame-Options
Structured Error:     Never expose stack traces or internal info in error responses
```

---

## Topic 6 · Compliance — RBI IT Framework, DPDP, SOC2, PCI-DSS

### In One Line
For fintech and enterprise SA roles in India, knowing compliance frameworks is a differentiator — most candidates can design systems, few can map controls to regulations.

### RBI IT Framework (for Banks & NBFCs in India)

**What it covers:** IT governance, risk management, IS audit, cyber security, data management, IT operations for RBIs regulated entities.

**Key control areas SA must address:**

| Area | Architectural Control |
|---|---|
| Data Localization | All customer financial data stored in India (Mumbai region only) |
| Audit Trail | Immutable logs of all transactions and data access (cannot be deleted) |
| Patch Management | OS and middleware patched within defined timelines (critical = 24hrs) |
| Incident Response | CIRT team, defined RTO for cyber incidents, RBI notification within 2-6 hours |
| Vendor Risk | Third-party cloud/SaaS must meet RBI standards; right to audit |
| BCP/DR | RTO and RPO tested annually; alternate processing site |
| Access Control | Role-based, principle of least privilege, privileged access management (PAM) |
| Encryption | Data encrypted at rest (AES-256) and in transit (TLS 1.2+) |

**SA architecture decisions driven by RBI:**
- Prod DB only in `ap-south-1` (Mumbai) — no cross-border data transfer for regulated data
- CloudTrail + centralized log archive with WORM (write-once-read-many) S3 policy
- All privileged access via PAM tool (CyberArk / BeyondTrust) — no direct SSH to prod

### DPDP — Digital Personal Data Protection Act 2023 (India)

**What it is:** India's data privacy law (similar to GDPR). Effective 2024-25.

**Key principles:**

| Principle | Architectural Impact |
|---|---|
| Purpose Limitation | Collect only data needed for stated purpose; log the purpose |
| Consent | Explicit user consent before collecting personal data |
| Data Minimization | Don't store what you don't need |
| Right to Erasure | User can request deletion; must be able to purge from all stores |
| Data Breach Notification | Notify DPBI within defined timeframe of a breach |
| Cross-border transfer | Only to countries with adequate protection (whitelist) |

**SA decisions:**
- Data classification layer: tag PII fields in all schemas
- Soft-delete + hard-delete capability for erasure requests
- Consent management service — stores consent audit trail
- Data retention policies enforced via automated purge jobs

### SOC2 (Service Organization Control 2)

**What it is:** US audit standard proving a service organization's controls meet Trust Service Criteria. Required by enterprise B2B customers (US market).

**5 Trust Service Criteria:**

| Criteria | Controls |
|---|---|
| **Security** | Access control, encryption, firewall, IDS/IPS |
| **Availability** | SLA, uptime monitoring, DR testing |
| **Processing Integrity** | Accurate, timely data processing; no unauthorized modification |
| **Confidentiality** | Sensitive data classified and protected |
| **Privacy** | GDPR/DPDP controls for personal data |

**SA architecture for SOC2 Type II:**
- Continuous control monitoring (AWS Security Hub, CloudTrail)
- Automated evidence collection (Drata, Vanta, Secureframe)
- Penetration testing annually
- All access via SSO + MFA; no shared accounts

### PCI-DSS (Payment Card Industry Data Security Standard)

**What it is:** Mandatory for any org that stores, processes, or transmits cardholder data.

**Key requirements SA must know:**

| Requirement | Architectural Control |
|---|---|
| **Req 1: Network segmentation** | Cardholder Data Environment (CDE) in separate VPC/subnet; no direct internet access |
| **Req 2: No defaults** | Change all default passwords/settings before deployment |
| **Req 3: Protect stored data** | Never store CVV/CVV2 after authorization; encrypt PAN at rest (AES-256); tokenize |
| **Req 4: Encrypt in transit** | TLS 1.2+ for all cardholder data in transit |
| **Req 6: Patch management** | Critical patches within 1 month; OWASP testing |
| **Req 7: Restrict access** | Least privilege; only staff who need cardholder data |
| **Req 10: Audit logs** | Log all access to cardholder data; retain 12 months |
| **Req 11: Security testing** | Quarterly vulnerability scans + annual penetration test |
| **Req 12: Security policy** | Written and maintained |

**SA shortcut — Tokenization:**
```
Customer enters card → Payment Gateway (Razorpay/Stripe)
  → Processes card → returns Token (e.g., tok_abc123)
  → Your system stores ONLY the token
  → No PAN, no CVV stored in your DB → dramatically reduces PCI scope
```

> "Use Razorpay/Stripe for card processing — they absorb PCI scope. You store tokens, not card data. Your PCI scope drops to SAQ-A (simplest)."

### Interview Q&A (40L SA Level)

**Q: How would you architect a fintech payment system to meet RBI IT Framework requirements?**
A: Four layers. Data residency — all customer and transaction data in AWS Mumbai (ap-south-1), no cross-region replication for regulated data. Audit trail — immutable CloudTrail + S3 with WORM policy; all DB queries logged; tamper-evident. Access control — no direct prod access; all privileged access via PAM (CyberArk); break-glass procedure for emergency. DR — active-passive in two AZs, RTO <4hr, RPO <1hr, tested quarterly. Encryption — AES-256 at rest (RDS encryption, S3 SSE-KMS), TLS 1.2+ in transit, KMS for key management with annual rotation.

**Q: What is PCI-DSS and how do you minimize scope?**
A: PCI-DSS is the payment card security standard — mandatory for any system that stores, processes, or transmits cardholder data. The most powerful scope reduction technique is tokenization: route all card data through a compliant payment gateway (Razorpay, Stripe) that handles the PAN and returns a token. Your system never sees or stores raw card numbers — your PCI scope drops to SAQ-A, the simplest level. For systems that do handle card data directly, cardholder data must be in a segmented Cardholder Data Environment (CDE) with strict access control, encrypted storage, and no CVV stored post-authorization.

**Q: What is DPDP and what architectural changes does it require?**
A: India's Digital Personal Data Protection Act requires explicit consent before collecting personal data, purpose limitation (collect only what's needed), and right to erasure. Architecturally: a data classification layer to tag PII fields across all schemas, a consent management service that stores and audits consent, soft-delete capability for erasure requests (with hard-delete across all stores including backups), and data retention automation. Cross-border data transfer requires DPBI-approved countries. Every service that handles personal data needs to be documented in a data inventory.

---

## Day 5 Quick Reference

| Topic | Key Interview Answer |
|---|---|
| Auth Code + PKCE | Code exchanged at backend + PKCE verifier prevents interception; replaces Implicit |
| Client Credentials | M2M auth — service authenticates as itself; no user context |
| JWT validation | Signature + exp + iss + aud — all 5 checks; RS256 not HS256 |
| Zero Trust | Never trust by location; verify every request; least privilege; assume breach |
| mTLS | Both sides present certificates; service identity via SPIFFE; Istio enforces |
| Secrets | Never in Git/ConfigMap; use Vault (dynamic creds) or AWS Secrets Manager + rotation |
| BOLA | Most critical OWASP API vulnerability — verify resource ownership per request |
| PCI-DSS | Tokenize card data via Razorpay/Stripe → your scope drops to SAQ-A |
| RBI IT Framework | Data in India, immutable audit logs, PAM for privileged access, tested DR |
| DPDP | Consent management, right to erasure, data classification, purpose limitation |

---

*Tags: #OAuth2 #OIDC #JWT #PKCE #ZeroTrust #mTLS #secrets #Vault #OWASP #BOLA #PCI-DSS #RBI #DPDP #SOC2 #compliance*
