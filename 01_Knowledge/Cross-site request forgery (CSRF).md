## What is it?
CSRF tricks a user's browser into <mark style="background: #FFB8EBA6;">sending a forged request to a site where the user is already logged in</mark>. <mark style="background: #ADCCFFA6;">The server sees a valid session cookie and trusts the request</mark> — <mark style="background: #FFF3A3A6;">even though the user never intended to make it.</mark>

**Key trait:** It's a _blind_ attack. The attacker can trigger actions (transfer money, change a password) but cannot read the response. Useless for data theft; <mark style="background: #FFB86CA6;">dangerous for state changes.</mark>

---
## How a normal request works
1. You log into your bank → <mark style="background: #ABF7F7A6;">browser stores a session cookie.</mark>
2. You submit a transfer form → browser sends a `POST` <mark style="background: #ABF7F7A6;">with your cookie.</mark>
3. <mark style="background: #FFB86CA6;">Bank validates the cookie</mark> → transfer goes through. ✅
---
## How CSRF exploits this
1. <mark style="background: #ADCCFFA6;">Attacker builds a page</mark> <mark style="background: #FFB8EBA6;">with a hidden form pointed at your bank.</mark>
2. <mark style="background: #ADCCFFA6;">You visit the attacker's page</mark> <mark style="background: #D2B3FFA6;">while still logged into the bank.</mark>
3. The form auto-submits → <mark style="background: #FFB86CA6;">your browser sends the request _with your real bank cookie_.</mark>
4. <mark style="background: #FFB8EBA6;">Bank sees a valid cookie → transfer goes through.</mark> ❌
The attacker never needed your password. Your browser did the work.
---
## The Actionable Defense Matrix

| **Defense Tier**                                                        | **Where to Configure It**                                                               | **What Exactly to Set**                                                                                                                                                                                                                                                                                               | **Why It Works**                                                                                                                                                                                                                                                     |
| ----------------------------------------------------------------------- | --------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **Tier 1: SameSite Cookie Flags**<br><br>  <br>_(Infrastructure Layer)_ | **Edge Layer / CDN / Reverse Proxy**<br><br>(NGINX, Cloudflare, AWS CloudFront)         | **Instruct the browser by passing a command in the HTTP response header** when the user logs in:<br><br>`Set-Cookie: SessionID=xyz; SameSite=Lax; Secure; HttpOnly`                                                                                                                                                   | The browser reads this header command and **presets these security rules inside its local cookie storage**. Once preset, the ==browser strictly refuses to attach the session cookie if a request originates from an external site== (like a hidden form on Site B). |
| **Tier 2: Fetch Metadata Filters**<br><br><br>_(Network Layer)_         | **API Gateway / Global Reverse Proxy**<br><br>  <br><br>(Kong, Apigee, AWS API Gateway) | Write a global route filter to ==inspect incoming HTTP headers on all write paths==(`POST`, `PUT`, `DELETE`).<br><br>**Action:** If `Sec-Fetch-Site == "cross-site"`, drop the request immediately with an HTTP `403 Forbidden`.                                                                                      | Provides a zero-cost infrastructure check. The browser stamps the request origin automatically, and your gateway drops it before it ever hits your application logic.                                                                                                |
| **Tier 3: CSRF Tokens**<br><br>  <br>_(Application Layer)_              | **Application Server Framework**<br><br><br>(Spring Security, Django, Express)          | **Enable the built-in Stateless CSRF / Double-Submit Cookie configuration** provided by your language framework.<br><br>**Action:** Configure your framework's ==CSRF filter to run in stateless mode==. The framework will automatically cross-verify the cookie value against the custom HTTP request header value. | **Site B (Attacker)** cannot guess a random cryptographic string, and browser isolation rules (Same-Origin Policy) prevent their external script from reading or stealing the token from your legitimate pages.                                                      |

---
## Deep Dive: Tier 3 Token Management for Modern Stateless APIs
Modern Single Page Applications (SPAs) and stateless REST APIs use the **Double-Submit Cookie Pattern** because it requires **zero server-side storage** (no database, no Redis cache, no memory footprint).
### How the Stateless Token Pattern Works
1. **The Handshake:** When a user logs in, the Application Server generates a random, cryptographically secure string (the token). It writes this value into a dedicated cookie (e.g., `XSRF-TOKEN`) and sends it back to the client.
2. **The Client Action:** When your **Genuine Frontend (Site A)** wants to submit a `POST`, `PUT`, or `DELETE` API call, its JavaScript reads that `XSRF-TOKEN` cookie value and ==copies it into a custom HTTP request header=== (typically `X-XSRF-TOKEN`).
3. **The Server Validation:** When the request arrives at your App Server, the stateless framework middleware ==extracts the value from the **Cookie** and extracts the value from the **Header**==. If they match exactly, the request is allowed.

### Why the Attacker is Blocked (The Cryptographic Guarantee)
- If **Site B (Attacker)** tries to force a form post to Site A, the browser automatically sends Site A's cookies, but the attacker's script **cannot read or manipulate headers** on cross-origin requests.
- Because the ==attacker cannot read Site A's cookies (due to the browser's Same-Origin Policy)==, <mark style="background: #FFB8EBA6;">they cannot copy the token value into the custom HTTP header.</mark>
- The server sees a request with a cookie but a missing or mismatched header, and instantly rejects the transaction.
