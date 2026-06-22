# P4 · Day 5 — OAuth2/OIDC · Zero Trust · mTLS · Secrets · OWASP · Compliance
**Pillar:** P4 — Security Architecture  
**Role Priority:** SA 🔵 Core · Java ⚪ Supporting · AI ⚪ Supporting  
**Day in Plan:** Day 5 (Week 1)  
**Time:** ~3 hours study + 1 hour Q&A practice

> **Cross-reference:** Service Mesh (Istio/Linkerd) and Zero Trust architecture patterns were covered in Day 2 notes. This day focuses on the security design layer — auth flows, secrets, API security, and compliance.

---

## Topic 1 · OAuth2 & OIDC — Flows You Must Know

### In One Line
<mark style="background: #FFB86CA6;">OAuth2 is an authorization framework</mark>; <mark style="background: #ADCCFFA6;">OIDC adds identity on top</mark> — together they are the standard for <mark style="background: #BBFABBA6;">securing modern APIs and user login flows.</mark>
### OAuth2 Roles
```
Resource Owner  = User (owns the data)
Client          = Application requesting access (SPA, mobile app, microservice)
Authorization Server = Issues tokens (Keycloak, Auth0, AWS Cognito, Okta, ForgeRock, Ping)
Resource Server = API that accepts tokens (your microservice)
```

### Flow 1 — [[Authorization Code Flow + PKCE]] (for SPAs & Mobile Apps)

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

**PKCE (Proof Key for Code Exchange):** Public clients (SPAs, mobile) can't keep a client secret. PKCE replaces the secret — <mark style="background: #FFB86CA6;">client generates a random verifier, hashes it as the challenge, sends hash to auth server</mark>, <mark style="background: #ADCCFFA6;">then proves it has the original verifier when exchanging the code. </mark>Prevents authorization code interception attacks.

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


### JWT Hygiene Rules

| Rule                                                  | Reason                                                    |
| ----------------------------------------------------- | --------------------------------------------------------- |
| Short expiry (15 min) for access tokens               | Limits blast radius if stolen                             |
| Refresh tokens in HttpOnly cookie                     | JS can't steal them (XSS protection)                      |
| Never store access tokens in localStorage             | XSS trivially reads localStorage                          |
| Rotate refresh tokens on use (refresh token rotation) | Detects token theft — old refresh token becomes invalid   |
| Include `aud` claim, validate it                      | Prevents a token for Service A being used at Service B    |
| Use RS256 (asymmetric) not HS256 (symmetric)          | Resource servers need only public key — no shared secret  |
| Token revocation via short expiry + blacklist         | JWTs are stateless — revoke via Redis blacklist on logout |

### Interview Q&A

**Q: Explain the OAuth2 <mark style="background: #FFB86CA6;">Authorization Code</mark> flow with PKCE.**
A: The user is redirected to the Authorization Server, which authenticates them and returns an authorization code. <mark style="background: #FFB86CA6;">The SPA exchanges this code (plus the PKCE verifier) for an access token and refresh token.</mark> PKCE replaces client secrets for public clients — the client generates a random verifier, sends its hash to the auth server, and proves it has the original verifier during exchange. This prevents an attacker who intercepts the authorization code from using it without the verifier. The access token is kept in memory (not localStorage), and the refresh token in an HttpOnly cookie.

**Q: When would you use Client Credentials vs Authorization Code flow?**
A: <mark style="background: #ABF7F7A6;">Authorization Code is for user-facing applications</mark> — a human authenticates and the token carries their identity and consent. <mark style="background: #BBFABBA6;">Client Credentials is for machine-to-machine</mark> — Service A authenticating to Service B with no user context. <mark style="background: #FFF3A3A6;">In a microservices system: the external-facing API uses Authorization Code (user logs in, token has their claims), while internal service-to-service calls use Client Credentials (order-service authenticates to payment-service as itself).</mark>

---

## Topic 2 · Zero Trust Architecture (Security Design)

### In One Line
Zero Trust is a security model: <mark style="background: #ABF7F7A6;">never trust any request based on network location alone</mark> — verify identity, device, and context on every request.

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
mTLS (mutual TLS) means <mark style="background: #FFB86CA6;">both client AND server present certificates</mark> — not just server proving identity to client (standard TLS), but <mark style="background: #FFB86CA6;">both sides proving identity to each other.</mark>

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
- <mark style="background: #FF5582A6;">Attacker who compromises any service </mark>→ lateral movement to any other service

With mTLS:
- Payment Service only accepts connections from services with valid certificates
- <mark style="background: #BBFABBA6;">Certificate = service identity</mark> (SPIFFE ID: `spiffe://cluster.local/ns/production/sa/order-service`)
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
- Istio uses its own<mark style="background: #FFB86CA6;"> CA (Citadel/istiod) to issue and rotate certificates automatically</mark>
- Certificates rotate every 24 hours by default — no manual cert management
- Certificate = SPIFFE ID tied to Kubernetes ServiceAccount → service identity

---
## Topic 4 · [[Secrets Management]]

---
## Topic 5 · [[OWASP Top 10 for APIs]]  (API Security Architect Must-Know)

==Open Worldwide Application Security Project== is a nonprofit foundation dedicated to improving software security. Driven by a global community, it provides free, open-source resources, tools, documentation, and standards to help developers and security professionals identify, prevent, and mitigate application vulnerabilities.


---

## Day 5 Quick Reference

| Topic              | Key Interview Answer                                                                |
| ------------------ | ----------------------------------------------------------------------------------- |
| Auth Code + PKCE   | Code exchanged at backend + PKCE verifier prevents interception; replaces Implicit  |
| Client Credentials | M2M auth — service authenticates as itself; no user context                         |
| JWT validation     | Signature + exp + iss + aud — all 5 checks; RS256 not HS256                         |
| Zero Trust         | Never trust by location; verify every request; least privilege; assume breach       |
| mTLS               | Both sides present certificates; service identity via SPIFFE; Istio enforces        |
| Secrets            | Never in Git/ConfigMap; use Vault (dynamic creds) or AWS Secrets Manager + rotation |


---

*Tags: #OAuth2 #OIDC #JWT #PKCE #ZeroTrust #mTLS #secrets #Vault #OWASP #BOLA #PCI-DSS #RBI #DPDP #SOC2 #compliance*
