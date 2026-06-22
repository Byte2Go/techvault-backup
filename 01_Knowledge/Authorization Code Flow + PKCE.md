## Architectural Objective
Public Clients (Single Page Applications like React/Angular and Mobile Apps) are fundamentally **untrusted**. Because their source code can be fully inspected via browser Developer Tools or decompilation, <mark style="background: #FF5582A6;">**they cannot securely store a private corporate password (Client Secret).**</mark> This entire flow is engineered <mark style="background: #FFF3A3A6;">to securely authenticate users and issue tokens to a public environment</mark> <mark style="background: #FFB8EBA6;">without ever exposing backend secrets</mark> or risking token interception.

 **Authorization Code + PKCE Flow (for SPAs & Mobile Apps)**
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

## 1. Flow Explanation

- **state:** [[OAuth 2.0 Security- The State Parameter & Login CSRF Defense]]
- **PKCE:** [[PKCE (Proof Key for Code Exchange)]]

| **Parameter / Token** | **Who Generates It?** | **Where is it Evaluated?** | **Form Factor**       | **Core Architectural Purpose**                                                                                                                                               |
| --------------------- | --------------------- | -------------------------- | --------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`id_token`**        | Authorization Server  | Frontend UI App            | Readable JWT          | **Authentication (Who you are).** Contains identity metadata (`name`, `email`). Read exclusively by the UI to customize the layout. **Backend APIs completely ignore this.** |
| **`access_token`**    | Authorization Server  | API Gateway / Microservice | Signed JWT            | **Authorization (What you can touch).** A valet key containing strictly capabilities (`scopes`, `client_id`). Passed directly to APIs to authorize database transactions.    |
| **`refresh_token`**   | Authorization Server  | Authorization Server       | Opaque String (UUID)  | **Session Extension.** A long-lived token used to swap for a fresh, short-lived Access Token silently when it expires, preventing user logout friction.                      |
| **`expires_in`**      | Authorization Server  | Frontend UI App            | Integer (e.g., `900`) | **Token Lifetime Manager.** Explicitly declares the remaining life (in seconds) of the current Access Token so the UI can schedule silent background refreshes.              |

## 2. The Step-by-Step Architectural Execution


```
[ Browser / SPA ]          [ Authorization Server ]          [ API Gateway ]
        │                             │                             │
        │ ── Step 1 & 2: /authorize ─►│                             │
        │    (challenge, state)       │                             │
        │                             │                             │
        │ ◄── Step 3 & 4: /callback ──│                             │
        │    (auth_code, state)       │                             │
        │                             │                             │
        │ ── Step 5 & 6: /token ─────►│                             │
        │    (verifier, auth_code)    │                             │
        │ ◄── Returns Tokens ─────────│                             │
        │                                                           │
        │ ── Step 7 & 8: API Call with Access Token ───────────────►│
        │                                (Fetches JWKS Public Key)  │
```

### Step 1: The User Intent
The user clicks the "Login" button inside the Single Page Application (SPA).

### Step 2: Client Perimter Registration (The Outbound Request)
The SPA acts as a front-gate checkpoint. Before changing the browser URL, the JavaScript application prepares its environment:

- It generates a cryptographically random value called `state` and saves it locally inside the browser's `sessionStorage`.
- It generates a random string called `code_verifier`, hashes it using SHA-256 to create the `code_challenge`, and keeps the raw verifier hidden in memory.

The browser is then forcefully redirected to the Authorization Server with these parameters:

```HTTP
GET /authorize?response_type=code
  &client_id=spa-client
  &redirect_uri=https://app.company.com/callback
  &scope=openid profile orders:read
  &code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWBuGJSstw-cM
  &state=xyzSecureRandom987
```

### Step 3: Direct User Authentication
The browser lands on the Authorization Server's domain. <mark style="background: #FFB86CA6;">The user interacts directly with a secure login page hosted by the Auth Server</mark> (submitting credentials, passing MFA, etc.). The <mark style="background: #FFB8EBA6;">frontend application code cannot see, track, or record any keystrokes during this step</mark>.

### Step 4: The Controlled Routing Hand-Off
Once authentication succeeds, <mark style="background: #BBFABBA6;">the Auth Server issues a short-lived **Authorization Code**</mark> (`ABC123`) and <mark style="background: #D2B3FFA6;">attaches it to the pre-registered redirect route.</mark> It forces the browser back to the UI:

```HTTP
HTTP/1.1 302 Found
Location: https://app.company.com/callback?code=ABC123&state=xyzSecureRandom987
```

#### Architectural Design Rationales for this Step:

> **Why `/callback` instead of the Homepage?** > The `/callback` route is a dedicated, silent routing path inside your frontend SPA router. It boots a highly specific script whose sole job is to<mark style="background: #ADCCFFA6;"> grab the sensitive code out of the URL string and clean up the browser's history bar immediately</mark>. This prevents browser extensions, history sync engines, or shoulder-surfers from capturing the authorization code.
> 
> **The `state` Validation Check:** > Before processing anything, the UI script pulls the returned `state` from the URL and checks it against the value stored in its local `sessionStorage`. If the values do not match, **the request is killed instantly**. This ensures that an attacker cannot inject a malicious, pre-stolen authorization code into a user's browser session (Cross-Site Request Forgery Protection).

### Step 5: Cryptographic Proof Verification (The Secure Swap)
The UI script completely strips the code parameter out of the URL path and <mark style="background: #ADCCFFA6;">fires a background, non-blocking `POST` request directly to the token endpoint.</mark> It hands over the raw `code_verifier` string that it kept hidden in memory:

```HTTP
POST /token HTTP/1.1
Host: auth.company.com
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code
&client_id=spa-client
&code=ABC123
&code_verifier=super_secret_unpredictable_string_generated_in_step_2
```

#### Architectural Design Rationale for this Step:

> **The Mechanics of PKCE:** > The Authorization Server hashes this incoming `code_verifier`. If `SHA256(code_verifier) == code_challenge`, it proves that the exact same frontend instance that kicked off the request in Step 2 is the one currently asking for tokens in Step 5.
> 
> If a rogue browser extension or mobile malware app had successfully intercepted the raw authorization code (`code=ABC123`) during the redirect step, it would not be able to redeem it. The attacker cannot calculate or deduce the original raw string from the hash value, causing the token swap to fail completely.

### Step 6: Token Package Delivery
The Authorization Server verifies the cryptographic math, marks the temporary authorization code as burned/expired so it can never be reused, and responds with a bundle of structured tokens:

```JSON
{
  "access_token": "eyJhbGciOi...", 
  "refresh_token": "8x9a-2b3c-4d5e", 
  "id_token": "eyJhbGciOi...", 
  "expires_in": 900
}
```

#### Architectural Design Rationales for this Step:

> **Separation of Concerns (ID Token vs. Access Token):** > The `id_token` is an open identity card meant for the **Frontend UI Application**. It is parsed locally by JavaScript to extract data like `name` or `profile_picture` to draw the user profile layout.
> 
> <mark style="background: #FFB86CA6;">The `access_token` is a capability key meant exclusively for the **Backend APIs**. </mark>The UI does not inspect it; it treats it as an opaque credential that it must attach to all network requests.
> 
> **Refresh Token Isolation Strategy:** > Because JavaScript variables and browser memory spaces can be entirely read by malicious scripts during a Cross-Site Scripting (XSS) attack, storing highly sensitive tokens locally is dangerous. In production architectures, the frontend application passes this entire payload over a secure proxy layer where the long-lived `refresh_token` is stripped and encrypted into an **HttpOnly, Secure, SameSite Cookie** that JavaScript code can never access or modify.

### Step 7: API Gateway Resource Invocation
The frontend application triggers a standard data query, <mark style="background: #ADCCFFA6;">embedding the short-lived access token directly inside the standard HTTP protocol request headers</mark>:

```HTTP
GET /orders HTTP/1.1
Host: api.company.com
Authorization: Bearer eyJhbGciOi...
```

### Step 8: Stateless Edge Validation
The API Gateway or Edge Security Controller intercepts the incoming request before it is routed to any internal core business microservices.

#### Architectural Design Rationale for this Step:
> **Cryptographic Signature Verification:** > <mark style="background: #FFB86CA6;">The access token is a signed JSON Web Token (JWT). </mark>The API Gateway downloads the <mark style="background: #ABF7F7A6;">Authorization Server's public verification key from its exposed JWKS endpoint</mark>.
> 
> The Gateway validates the token's cryptographic signature using this public key, and verifies that the system timestamps have not crossed the expiration boundary (`exp`). If an attacker has manually tampered with the payload data inside the JWT to alter user roles or permissions, the signature validation calculation fails immediately.
> 
> Because this process relies entirely on asymmetric cryptography, the API Gateway evaluates the token locally and completely **statelessly**, without needing to fire a slow, blocking network call back to the Authorization Server database for every incoming API request. Once validated, the claims are unpacked and the request is safely cleared for execution.