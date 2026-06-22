An **Egress Proxy** (like Envoy or HAProxy) is a specialized server that ==acts as a gatekeeper for all **outbound** network traffic== leaving your private cloud environment.

Think of it as a<mark style="background: #FFB86CA6;"> security guard standing at the _exit_ door of your company's building</mark>, <mark style="background: #FFF3A3A6;">inspecting everyone trying to leave and checking where they are going.</mark>

## The Physical Problem: Why Your App Pod is Dangerous
In a standard cloud setup, your `Order-Service` application <mark style="background: #D2B3FFA6;">container needs to talk to the public internet</mark> to do legitimate work—like downloading a user's avatar image or calling the PayPal API.

<mark style="background: #FFB8EBA6;">Because it needs to make outbound calls, its network interface is wide open.</mark> If a hacker submits a malicious internal URL, your application code blindly executes the request. Since your app sits _inside_ your secure perimeter, it can easily chat with your internal payment servers or the AWS infrastructure metadata endpoint (`169.254.169.254`).

```
[ Hacker Input ] ──► (POST /avatar {"url": "http://169.254.169.254"})
                              │
                              ▼
                  ┌──────────────────────┐
                  │  Your Java App Pod   │
                  └──────────┬───────────┘
                             │
            (Blindly fires outbound HTTP call)
                             │
                             ▼
                [ AWS Metadata Endpoint ] ──►(Leaks AWS IAM Keys to Hacker! ❌)
```

## The Solution: Inserting the Egress Proxy
To fix this, you <mark style="background: #FFB86CA6;">strip your application pod of its ability to talk directly to the outside network.</mark> Instead, you force <mark style="background: #D2B3FFA6;">it to route **every single outbound request** through the Egress Proxy.</mark>

The Egress Proxy is configured with a strict **Blocklist** of <mark style="background: #CACFD9A6;">internal IP ranges (RFC 1918 subnets and cloud metadata endpoints)</mark>.


```
                  ┌──────────────────────┐
                  │  Your Java App Pod   │
                  └──────────┬───────────┘
                             │
           (Tries to fetch http://169.254.169.254)
                             │
                             ▼
                ┌──────────────────────┐
                │     EGRESS PROXY     │ ◄─── [Enforces Blocklist:169.254.*]
                └──────────┬───────────┘
                           │
              (Evaluates: "Target is BLOCKED")
                           │
                           ▼
                [ Connection Dropped! 🛑 ] ──► (Returns 403 Forbidden to App ✅)
```

## How It works in Production (The Rule Evaluation)
When the app tries to fetch a URL, the Egress Proxy runs a <mark style="background: #FFB86CA6;">two-step check before opening a network socket:</mark>
1. **DNS Resolution:** If the user passed a domain name (like `http://internal-payroll.company.local/`), the proxy resolves it to its actual physical IP address.
2. **IP Matching:** The proxy matches the destination IP against its security rules:


```
Is destination 169.254.169.254? ──► MATCH ──► DROP REQUEST (SSRF Blocked)
Is destination 10.0.15.22?      ──► MATCH ──► DROP REQUEST (Internal Network Shielded)
Is destination 142.250.190.46?  ──► GOOGLE ──► ALLOW REQUEST (Legitimate Internet)
```

By routing all outgoing traffic through this dedicated proxy container, your developers can write standard Java code without needing to constantly maintain massive IP blocklists inside the application logic itself.