### The Core Problem: SPAs are "Public Clients"
In traditional backend apps, the server can safely hide a <mark style="background: #FFB86CA6;">permanent password (a Client Secret)</mark> <mark style="background: #ADCCFFA6;">in its code to prove its identity to the Auth Server.</mark>

<mark style="background: #FFB8EBA6;">A React/Angular SPA cannot hide secrets.</mark> <mark style="background: #D2B3FFA6;">Because a browser SPA downloads all its JavaScript files directly to the user's computer</mark>, anyone can open the browser console, inspect the code, and steal a permanent password. In security terms, this makes an SPA a **Public Client**.

<mark style="background: #FFB8EBA6;">Without a permanent password, the Auth Server needs a way to verify that the app asking for tokens</mark> is your genuine app, and not a hacker's script intercepting the traffic.

### The Solution: The Dynamic, <mark style="background: #FFF3A3A6;">One-Time Secret Pattern</mark>
Instead of a permanent password, <mark style="background: #ADCCFFA6;">PKCE forces your UI to dynamically generate a temporary, **one-time-use secret**</mark> for every single login attempt.

#### 1. What is SHA-256 in Plain English?
- <mark style="background: #ABF7F7A6;">There are **no public keys or private keys** used anywhere in PKCE.</mark>
- SHA-256 is simply a **one-way digital grinder**. If you put a secret phrase like `"SecretKey123"` into it, it spits out a completely unreadable string of random characters (`"HashXYZ"`).
- **The One-Way Rule:** Anyone can look at the random string `"HashXYZ"`, but **it is impossible to reverse it** to figure out that the original phrase was `"SecretKey123"`. The only way to verify it is to guess the original phrase, run it through the grinder, and see if the outputs match.

#### 2. Who is Protecting Who?
- **The `state` parameter** <mark style="background: #FFF3A3A6;">protects the **Frontend UI**</mark> from being tricked into running a bad login link created by a hacker (Login CSRF).
- **The `PKCE` protocol** <mark style="background: #FFF3A3A6;">protects the **Auth Server**</mark> from handing out real tokens to a hacker who stole the login code.

## The Three-Phase Flow

```
[ Step 1: Login Started ]
UI Memory: Secret Phrase ("SecretKey123") ──► Run SHA256 ──► The Lock ("HashXYZ")
                                                                   │
                                     Sent to Auth Server ──────────┘

[ Step 3: Swapping the Code ]
UI Memory: Sends Secret Phrase ("SecretKey123") ─────► [ Auth Server Checks ]                                          Does SHA256("SecretKey123") == "HashXYZ"?
                                              If YES ──► Hand Over Tokens!
```

### Step 1: Making the "Lock" (The Outbound Challenge)
When a user clicks "Login," <mark style="background: #FFB86CA6;">your real UI application creates a random secret phrase</mark> out of thin air inside its private JavaScript memory:
- **`code_verifier` (The Key):** `"SecretKey123"`
- **`code_challenge` (The Lock):** The UI runs `"SecretKey123"` through SHA-256 to get `"HashXYZ"`.

The UI redirects the browser to the Auth Server, passing **only the lock** in the URL link:

```HTTP
GET /authorize?code_challenge=HashXYZ
```

The Auth Server writes down `"HashXYZ"` on its internal notepad next to your session. **Crucially, the server does not know that the original secret phrase is `"SecretKey123"`.**

### Step 2: The Authorization Code (The Attack Vector)
The user logs in. The Auth Server validates them, but <mark style="background: #FFB86CA6;">it doesn't send the final tokens back yet.</mark> Instead, it redirects the user back to your UI with <mark style="background: #FFB8EBA6;">a short-lived, temporary authorization string</mark> attached to the URL query parameters: `?code=ABC123`.
#### The Stolen Code Scenario:
If a bad app or a malicious extension hiding on your device slips in, it can **steal that temporary code from the redirect URL**. The hacker immediately tries to bypass your UI and use this stolen code to get your real account tokens:

```HTTP
POST /token
grant_type=authorization_code
&code=ABC123
```

But the Auth Server stops them right there: _"Hold on. This login code is locked. To use it, you must give me the original secret phrase (`code_verifier`) that matches the hash (`HashXYZ`) I have on my notepad."_

Because the <mark style="background: #ADCCFFA6;">SHA-256 meat grinder only works **one way**, the hacker can look at the hash `"HashXYZ"` all day, but **they can never guess or calculate** that the original secret phrase was `"SecretKey123"`.</mark> The hacker is rejected immediately.

### Step 3: Opening the Vault (The Real UI Wins)
Your genuine UI application—which still has the secret phrase `"SecretKey123"` sitting safely inside its private JavaScript memory—<mark style="background: #BBFABBA6;">bypasses the public browser URL bar and creates a direct, secure background connection to swap the temporary code for tokens</mark>:

```HTTP
POST /token HTTP/1.1
Host: auth.company.com
Content-Type: application/x-www-form-urlencoded

grant_type=authorization_code
&code=ABC123
&code_verifier=SecretKey123
```

The Auth Server takes `"SecretKey123"`, runs it through SHA-256 locally, and gets `"HashXYZ"`. It checks its notepad.

The values match perfectly. The server says: _"This proves you are the exact same app instance that started the login in Step 1, because no outside hacker could know this original secret phrase."_ The server safely hands over the **Access Token** and **Refresh Token**.