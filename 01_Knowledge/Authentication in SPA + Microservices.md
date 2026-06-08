From a **Security Architecture** perspective, <mark style="background: #ADCCFFA6;">storing tokens in an single-page application (SPA) requires balancing protection </mark>against two primary web vulnerabilities: **[[Cross-Site Scripting (XSS)]]** and **[[Cross-site request forgery (CSRF)]]**.
## 1. The Core Vulnerability Trade-Off
Before looking at the network traffic, it is vital to understand <mark style="background: #FFB86CA6;">_why_ we split tokens between browser memory and cookies</mark>:

### The <mark style="background: #D2B3FFA6;">LocalStorage</mark> Flaw (XSS Vulnerability - <mark style="background: #FFF3A3A6;">Token</mark>)
If an attacker successfully injects a malicious script into your React app (via an npm package vulnerability, an unsanitized input field, or a third-party script), that script can execute `localStorage.getItem("access_token")`.
- **The Result:** The <mark style="background: #FFB8EBA6;">attacker instantly steals the token</mark>, exfiltrates it to their own server, and can impersonate the user from anywhere in the world until the token expires.

### The <mark style="background: #D2B3FFA6;">Cookie</mark> Flaw (CSRF Vulnerability - <mark style="background: #FFF3A3A6;">Cookies</mark>)
Browsers automatically attach cookies to every single HTTP request sent to a domain. If a user visits a malicious website while logged into your app, that malicious site can fire a silent background request to `https://api.mycompany.com/delete-account`.
- **The Result:** The browser blindly sends your <mark style="background: #FFB8EBA6;">authenticated cookie along with the malicious request.</mark>

### The Hybrid Solution
- **Access Tokens** are kept in **Short-Lived <mark style="background: #BBFABBA6;">Browser Memory (JS Variables)</mark>**. If an XSS attack happens, there is nothing in `localStorage` to steal.
- **Refresh Tokens** are kept in a **Long-Lived `HttpOnly` Cookie**. <mark style="background: #ADCCFFA6;">Because it is marked `HttpOnly`, browser JavaScript cannot read or steal it, neutralizing XSS.</mark>


## 2. Step-by-Step Architecture Flow
This pattern coordinates the SPA client, the API Gateway, and a dedicated Identity/Auth microservice.

```
 ┌───────────┐             ┌─────────────────┐             ┌─────────────────┐
 │SPA Client │             │   API Gateway   │             │  Auth Service   │
 └─────┬─────┘             └────────┬────────┘             └────────┬────────┘
       │                            │                               │
       │ 1. POST /auth/login        │                               │
       ├────────────────────────────┼──────────────────────────────►│
       │                            │                               │
       │ 2. Returns Access Token (In Memory)                        │
       │    & Refresh Token (HttpOnly Cookie)                       │
       ◄────────────────────────────┼───────────────────────────────┤
       │                            │                               │
       │ 3. GET /orders             │                               │
       │    (Bearer Access Token)   │                               │
       ├───────────────────────────►│                               │
       │                            │ (Validates JWT)               │
       │                            ├──────────────┐                │
       │                            │              │                │
       │                            │◄─────────────┘                │
       │                            │                               │
       │ 4. Routes to Order Service │                               │
       ▼                            ▼                               ▼
```

### Step 1: The Login Request
The user types their username and password into the React app. The SPA fires a standard HTTP `POST` over to the `/auth/login` route.
### Step 2: The Dual-Token Response
The Auth Service validates the credentials and generates two distinct tokens:
1. **Access Token:** A short-lived JSON Web Token (e.g., expires in 15 minutes)  <mark style="background: #ADCCFFA6;">sent back inside the JSON response payload.</mark> <mark style="background: #D2B3FFA6;">The React application captures this string and saves it as a local variable in **application memory** </mark>(e.g., inside a React state or a clean JavaScript closure).
2. **[[Refresh Token]]:** A long-lived token (e.g., expires in 7 days) <mark style="background: #ADCCFFA6;">attached to the HTTP response header as a secure cookie</mark>:

    ```HTTP
    Set-Cookie: refresh_token=xyz987; Secure; HttpOnly; SameSite=Strict; Path=/auth/refresh
    ```


> **Crucial Security Flags Configured on the Cookie:**
> - **`HttpOnly`:** Blocks browser JavaScript from running `document.cookie`. XSS scripts cannot read this token.
> - **`Secure`:** Forces the browser to only transmit the cookie over encrypted HTTPS connections.
> - **`SameSite=Strict`:** Prevents the browser from sending the cookie during cross-site requests, completely neutralizing CSRF attacks.
> - **`Path=/auth/refresh`:** Ensures the <mark style="background: #ADCCFFA6;">browser _only_ sends this cookie when hitting the refresh endpoint</mark>, shielding your main API routes from receiving unnecessary cookie payloads.

### Step 3: Making Authenticated API Calls
When the SPA needs to pull data (e.g., `GET /orders`), <mark style="background: #D2B3FFA6;">it manually grabs the access token from its local JavaScript memory variable</mark> <mark style="background: #FFB86CA6;">and injects it into the HTTP header</mark>:

<mark style="background: #BBFABBA6;">**An "Access Token" is the _job description/role_, while a "JWT" (JSON Web Token) is the _format_ used to build it.**</mark>

```HTTP
GET /orders HTTP/1.1
Host: api.mycompany.com
Authorization: Bearer <in_memory_access_token_string>
```

The API Gateway intercepts this request. <mark style="background: #FFB86CA6;">Because this specific access token was issued as a **JWT (JSON Web Token)**,</mark> the token contains self-contained, cryptographically signed data. <mark style="background: #BBFABBA6;">The Gateway decodes this JWT signature</mark>. <mark style="background: #FFF3A3A6;">If the signature is valid and the timestamp has not expired,</mark> the Gateway forwards the request directly down to the internal `Order Service`.

#### Terminology matters:
- **Access Token:** This is the abstract OAuth2 term for the security badge passed in the header. It tells the system, _"This request is allowed to access data."_
- **JWT & Access Token Correlation:** This is the concrete technology used to format that badge. Instead of just being a random string, a JWT is a string divided into three sections (Header, Payload, Signature) that allows your API Gateway to validate it instantly without querying a central session database.
- **Refresh Token:** This is the abstract OAuth2 term for a long-lived credential <mark style="background: #ADCCFFA6;">used strictly to request a new Access Token when the old one expires</mark>. It is never sent to your resource APIs (like `/orders`).<mark style="background: #D2B3FFA6;"> Instead, it is securely sent only to your Identity Provider (Auth Server).</mark>
- **JWT & Refresh Token Correlation:** Unlike an Access Token, <mark style="background: #FFF3A3A6;">a Refresh Token **does not have to be a JWT—and often shouldn't be**.</mark>
	- Because an Access Token is short-lived (e.g., 15 minutes) and <mark style="background: #ADCCFFA6;">read by many services, it is formatted as a **JWT**</mark> so APIs can validate it instantly offline.
	- Because a<mark style="background: #FFB86CA6;"> Refresh Token is long-lived (e.g., 30 days) and must be easily revoked if a device is stolen</mark>, <mark style="background: #D2B3FFA6;">it is usually formatted as an **Opaque Token** (a random string). </mark> <mark style="background: #FFB8EBA6;">This forces the Auth Server to look it up in a central database to ensure it hasn't been blacklisted before handing out a new Access Token.</mark>
### Step 4: Handling Token Expiration (The Silent Refresh)
Eventually, the 15-minute lifespan of the access token ends. The API Gateway intercepts a request, detects the expired timestamp, and throws back an HTTP **`401 Unauthorized`** response code.

The SPA catches this `401` error inside its global network interceptor (like an Axios interceptor) and seamlessly runs a background fallback routine:
1. The SPA hits the background endpoint: `POST /auth/refresh`.
2. Because this call matches the path rule, the browser automatically appends the hidden `HttpOnly` refresh cookie to the request header.
3. The Auth Service verifies the cookie, generates a **brand-new 15-minute access token**, and returns it in the response body.
4. The SPA saves the new access token to its application memory variable and immediately retries the original `/orders` request. The end user never notices a interruption.

## 3. Clear Comparison Summary

|**Token Type**|**Stored Where**|**Lifespan**|**Primary Attack Shielded**|
|---|---|---|---|
|**Access Token**|**JS Application Memory** (Variables, State)|Short (10–15 Minutes)|**XSS Shielded:** If an attacker extracts your browser's local storage data, they find absolutely nothing.|
|**Refresh Token**|**`HttpOnly` Browser Cookie**|Long (Days or Weeks)|**CSRF/XSS Shielded:** JavaScript cannot access it due to `HttpOnly`. Malicious sites cannot leverage it due to `SameSite=Strict`.|

## 💡 Summary for your Notes

> - **Why do we separate tokens?** <mark style="background: #FFB8EBA6;">Putting everything in `localStorage` leaves you completely vulnerable to **script injection (XSS) asset theft**.</mark> <mark style="background: #FF5582A6;">Putting everything in cookies exposes your infrastructure to **cross-site session spoofing (CSRF)**.</mark>
> - **How does the hybrid pattern solve it?** <mark style="background: #BBFABBA6;">Short-lived access tokens stay in volatile JavaScript memory (immune to local storage theft)</mark>, <mark style="background: #FFF3A3A6;">while the long-lived keys needed to regenerate them are locked away in `HttpOnly` cookies that JavaScript cannot touch</mark>.
> - **What does the API Gateway do?** The<mark style="background: #D2B3FFA6;"> Gateway handles the heavy lifting of decrypting and validating the incoming memory token string on every call</mark>, ensuring that individual business microservices don't waste CPU cycles processing authentication rules.
> 	- **The API Gateway does NOT call the Auth Server on every request. It uses a pre-configured public key to validate the JWT instantly and completely offline**.
> 	- **How?** [[JWT Cryptographic Validation at API Gateway]]