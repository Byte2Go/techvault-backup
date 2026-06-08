It is simply the **initial cryptographic handshake** that happens at the very beginning of the login process to ensure that the server **hands those Access and Refresh tokens** to your _legitimate_ SPA, and not to a hacker's script intercepting the traffic.

## The Problem PKCE Solves
In a standard web server application, the backend can safely store a <mark style="background: #ADCCFFA6;">**secret password (a Client Secret)** to prove its identity to the Auth Server during login.</mark>

<mark style="background: #FFB8EBA6;">A React SPA cannot hold **secrets**. Because a browser SPA downloads all its JavaScript files directly to the user's computer</mark>, <mark style="background: #FF5582A6;">anyone can open the browser console, inspect the code, and steal a Client Secret. </mark> This makes an SPA what OAuth calls a **Public Client**.

<mark style="background: #ADCCFFA6;">Without a **secret password**, how does the Auth Server know that the application asking for the tokens is actually your genuine React app</mark>? <mark style="background: #BBFABBA6;">That is where PKCE comes in.</mark>

## How PKCE Works (The One-Time Secret Pattern)
The person who starts the login process must prove<mark style="background: #BBFABBA6;"> they know the **original secret word** before the server will hand over the security tokens.</mark>

Instead of using a permanent secret password, PKCE forces your React SPA to dynamically generate a **temporary, one-time use secret password** for every single login attempt.

It does this using a simple, three-step cryptographic handshake:
### Step 1: The Code Challenge (The Lock)
When a user clicks "Login," <mark style="background: #D2B3FFA6;">your React app generates a random string of characters</mark> out of thin air. This string is called the **Code Verifier**.
- The app immediately <mark style="background: #D2B3FFA6;">runs this string through a SHA-256</mark> cryptographic hash function to scramble it. This scrambled version is called the **Code Challenge**.
- The React app redirects the user to the Auth Server to log in, and <mark style="background: #D2B3FFA6;">it passes along this **Code Challenge** (the lock).</mark> <mark style="background: #FFF3A3A6;">The Auth Server saves this lock in its memory.</mark>

### Step 2: The ==Authorization Code== (The Temporary Authorization)
The user enters their credentials. The Auth Server validates them, but it doesn't send the tokens back to the browser immediately.
- Instead, it <mark style="background: #FFB86CA6;">redirects the user back to your React app with a short-lived, temporary authorization string</mark> attached to the URL query parameters (e.g., `?code=xyz123`).

### Step 3: The Code Verifier (The Key)
Your React SPA reads that code from the URL. Now it needs to swap that code for the actual Access and Refresh Tokens.
- The SPA sends a backend API request to the Auth Server's token endpoint. <mark style="background: #D2B3FFA6;">It sends the `code=xyz123` </mark> **plus**  ==the original, unscrambled **Code Verifier** string== it created in Step 1 (the key).    
- The <mark style="background: #ADCCFFA6;">Auth Server hashes this key using the exact same SHA-256 function.</mark> <mark style="background: #BBFABBA6;">If the result matches the **Code Challenge** (the lock) it saved in Step 1, it proves that the application asking for the tokens right now is the _exact same_ application</mark> that initiated the login process a few moments ago.
- The Auth Server securely dispenses your **Access Token and Refresh Token.**

## Summary
> **What is PKCE?** PKCE is a security extension to the standard OAuth 2.0 login flow designed explicitly for public clients like SPAs and Mobile Apps that cannot safely store a static password (Client Secret). It eliminates the risk of interception attacks by forcing the frontend application to generate a dynamic, one-time cryptographic lock and key for every login handshake, ensuring tokens are only delivered to the authentic application instance.