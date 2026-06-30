# How API Gateway is used to connect to the servers in microservice architecture.
In a microservice architecture, an **API Gateway** <mark style="background: #FFB86CA6;">acts as the single point of entry for all client requests</mark> (such as <mark style="background: #FFF3A3A6;">web browsers, mobile apps, or third-party integrations</mark>). Instead of a client trying to talk directly to dozens of independent, scattered microservices, it sends every request to the API Gateway, which handles the complex routing logic behind the scenes.

Here is the high-level architectural blueprint of how an API Gateway connects clients to your internal servers.

## 1. The Core Routing Flow: The Reverse Proxy Pattern
At its heart, an API Gateway operates as ==a sophisticated **Reverse Proxy**==. It abstracts the internal network layout from the outside world.

```
                  ┌────────────────────────────────────────┐
                  │              API GATEWAY               │
                  │                                        │
 Client Request   │  Inspects Path:                        │    Routed Pipe
─────────────────►│  /api/v1/orders  ──► [Route Rules] ────┼──────────┐
                  │                                        │          │
                  └────────────────────────────────────────┘          ▼
                                                        ┌───────────────────┐
                                                        │   Order Service   │
                                                        │ (Internal Server) │
                                                        └───────────────────┘
```

1. **The Client Call:** The client makes a clean, standard HTTP request to<mark style="background: #FFB86CA6;"> a single domain name</mark> (e.g., `https://api.yourcompany.com/api/v1/orders`).
2. **Path Inspection:** The API Gateway intercepts this request and <mark style="background: #ABF7F7A6;">examines the path prefix</mark> (`/orders`) or header metadata.
3. **Internal Forwarding:** The gateway checks its internal configuration map, <mark style="background: #ADCCFFA6;">discovers which physical server or cluster handles order management</mark>, and transparently forwards the request across the internal private network to that specific backend service.
## 2. Dynamic Connection: Integration with Service Discovery
In modern cloud environments, <mark style="background: #FFB8EBA6;">microservice servers are continuously scaling up, scaling down, or restarting with brand-new, unpredictable IP addresses.</mark> An API Gateway cannot rely on hardcoded server locations. ==It connects to them dynamically using a **Service Registry**== (native Kubernetes DNS).

```
                               ┌───────────────────────────┐
                               │   SERVICE REGISTRY        │
                               │  (Map: Order Service =    │
                               │   10.0.1.5, 10.0.1.6)     │
                               └─────────────▲─────────────┘
                                             │ 2. Pulls active IPs
                                             │
 1. Request to /orders         ┌─────────────┴─────────────┐
──────────────────────────────►│        API GATEWAY        │
                               └─────────────┬─────────────┘
                                             │
                                             ├──────── ────┐
                                             │ 3. Forward (Load Balanced)
                                             ▼             ▼
                               ┌─────────────────┐┌───────────────┐
                               │  Order Service  ││ Order Service │
                               │    Instance 1   ││  Instance 2   │
                               │  (10.0.1.5)     ││ (10.0.1.6)    │
                               └─────────────────┘└───────────────┘
```

- **The Sync:** <mark style="background: #ADCCFFA6;">When an internal server instance starts up</mark>, it <mark style="background: #FFB86CA6;">registers its current IP address with the Service Registry.</mark>
- **The Lookup:** When a request hits the API Gateway, <mark style="background: #D2B3FFA6;">the gateway queries the registry in real-time</mark>: _"Where are the healthy instances of the Order Service right now?"_
- **Client-Side Load Balancing:** The <mark style="background: #BBFABBA6;">registry returns the available IP addresses</mark>, and the API Gateway automatically distributes the incoming traffic across those backend servers using algorithms like <mark style="background: #ABF7F7A6;">Round Robin or Least Connections</mark>.

## 3. The Gateway "Guard" Layer: What Happens Before Forwarding?
Connecting to a server isn't just about moving data packets; it's about protecting the backend servers from being overwhelmed or compromised. Before the gateway passes a request to an internal server, it executes a series of crucial filter checks:
- **Authentication & Authorization:** The<mark style="background: #FFB86CA6;"> gateway inspects the client's JWT token or API key</mark>. If the token is invalid, the gateway rejects the request immediately, ensuring unauthenticated traffic never wastes the CPU resources of your internal microservices.
- **Rate Limiting & Throttling:** It <mark style="background: #ADCCFFA6;">tracks how many requests a specific client is making per second</mark>. If a mobile app goes rogue or a bad actor attempts a DDoS attack, the gateway throttles them at the door, protecting backend servers from crashing.
- **Protocol Translation (BFF / ==Edge Transformation==):** A client might talk to the gateway using standard REST/JSON over internet-friendly HTTP/2, but <mark style="background: #FFB86CA6;">your ultra-fast internal microservices might communicate using binary **gRPC** or Protocol Buffers. The API Gateway handles this translation on the fly.</mark>

## Summary Blueprint: Choosing Your Gateway Tool
When implementing this architecture, you don't build an API Gateway from scratch. You select an established enterprise tool depending on your technology stack:
- **Cloud-Managed Gateways (AWS API Gateway, Azure API Management):** Fully managed, serverless options provided by cloud platforms that handle scaling automatically without manual server management.