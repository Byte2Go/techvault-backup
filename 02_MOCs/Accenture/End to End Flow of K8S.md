This scenario represents the **industry-standard Single Page Application (SPA) + Microservices** routing layout.

When a user typed `www.myoffice.com` into a browser, the browser needed to fetch the React/Angular static assets (HTML, JS, CSS) first. Once loaded, that UI application executed async background network calls (via `fetch` or `axios`) back to the same domain paths (`/user`, `/products`, `/task`) to pull raw JSON data from the Kubernetes pods.

An Enterprise production deployment coordinates these movements across a multi-tiered architecture.

### 1. The Production Architecture Topology
To scale efficiently and prevent Cross-Origin Resource Sharing (CORS) errors, the infrastructure uses **Path-Based Routing**. The entire ecosystem is exposed behind a single public domain name (`www.myoffice.com`), splitting traffic at the cluster perimeter.

#### Tier 1: The Public Domain & Edge (DNS & Storage)
- **The Web Asset Storage (S3 / Cloud Storage + CDN):** The built React/Angular code consists of static client files. Instead of wasting Kubernetes Pod CPU/RAM hosting static files, these are deployed to an object storage bucket (like AWS S3) and distributed worldwide via a Content Delivery Network (like CloudFront or Cloudflare).
- **The Domain Name:** `www.myoffice.com` points its core root domain mapping directly to the CDN for instant UI load times, while its specific API path structures route down toward the infrastructure stack.

#### Tier 2: The Network Load Balancer (NLB - Layer 4)
- **The Gateway Entrypoint:** The **NLB** serves as the fixed, public, high-throughput static IP interface for the API backend. It handles millions of raw concurrent TCP connection requests at ultra-low latency, feeding those raw streams directly into the API Gateway.

#### Tier 3: The Enterprise API Gateway (Security & Governance Layer)
- **The Central Guardian:** Traffic hitting the NLB lands on the **API Gateway** (e.g., Broadcom Layer7, Apigee, AWS API Gateway). It provides centralized edge capabilities:
    - **Authentication/Authorization:** Validating JWT tokens or OAuth cookies _before_ traffic touches the container cluster.
    - **Rate Limiting:** Ensuring a script on the browser doesn't spam `/products` and crash the system.
    - **Threat Protection:** Blocking SQL Injections or malformed headers.

#### Tier 4: The Ingress Controller & Kubernetes Cluster Grid (Layer 7 Routing)
- **The Internal Mesh:** Once the API Gateway approves the request, it forwards it to the Kubernetes cluster's **Ingress Controller** (e.g., Nginx Ingress). The Ingress Controller reads the Layer 7 URI path and instantly forwards the packet down to the corresponding internal **Kubernetes ClusterIP Service**, which load balances the traffic across the target live **Application Pods**.

### 2. Tracing the Complete Traffic Lifecycles
#### Flow A: Loading the UI Pages (First Time Access)
1. The user inputs `www.myoffice.com` into the browser.
2. The request hits the global CDN edge. The CDN reads the root request and returns the static React/Angular `index.html` and bundled javascript scripts from storage.
3. The React/Angular application instantiates completely inside the user's local browser memory. No Kubernetes pods have been touched yet.

#### Flow B: Calling the Data APIs (Subsequent Interactions)
Once running inside the browser, the JavaScript application makes API data requests back to the server:

```
[ Browser SPA App ] 
       │
       ▼ (HTTP GET to www.myoffice.com/products)
[ Network Load Balancer (NLB) ]
       │ (Passes raw TCP connection stream down)
       ▼ 
[ Enterprise API Gateway ]
       │ 1. Verifies User's Auth Token
       │ 2. Confirms Rate-Limit compliance
       ▼ (Forwards clean sanitized request)
[ K8s Ingress Controller ]
       │ Evaluates URL path mapping rules:
       │  - If "/user"     ──> Go to User-Service
       │  - If "/products" ──> Go to Products-Service
       │  - If "/task"     ──> Go to Task-Service
       ▼
[ K8s ClusterIP Service: "products-service" ]
       │ Distributed Round-Robin Internal Routing
       ▼
[ Product Pod 1 ] or [ Product Pod 2 ] or [ Product Pod 3 ]
       │ Executes DB query and returns data map
       ▼
( JSON Payload travels back up the chain to the Browser UI )
```

### 3. Concrete Kubernetes Manifest Layout

To bind the cluster side together, the declarative configuration configures the paths cleanly. The Ingress manifest handles the mapping rules inside the cluster namespaces:

```YAML
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: office-application-router
  namespace: corporate-apps
  annotations:
    kubernetes.io/ingress.class: "nginx"
    nginx.ingress.kubernetes.io/ssl-redirect: "false" # SSL handled at API Gateway level
spec:
  rules:
  - host: www.myoffice.com
    http:
      paths:
      - path: /user
        pathType: Prefix
        backend:
          service:
            name: user-cluster-service
            port:
              number: 8081
      - path: /products
        pathType: Prefix
        backend:
          service:
            name: products-cluster-service
            port:
              number: 8082
      - path: /task
        pathType: Prefix
        backend:
          service:
            name: task-cluster-service
            port:
              number: 8083
```


---
When you introduce Kubernetes into an enterprise infrastructure stack, you purposefully split responsibilities between the **Enterprise API Gateway** and the **Kubernetes Ingress Controller** to prevent duplication and maximize performance.

Let's look at why this offloading happens, how the mapping shifts, and exactly what each layer owns in a production environment.

### 1. The Architectural Shift: Before vs. After Kubernetes

To see why you feel like you are seeing the same feature twice, look at how the architecture evolves when moving into a containerized cluster.

#### The Old Way (Non-Kubernetes / VM-Based)
Before Kubernetes, your microservices ran on fixed Virtual Machines (VMs) with stable, unchanging IP addresses (e.g., User Service was always at `10.0.1.55:8080`).
- **The Setup:** The **API Gateway** had to do _everything_. It handled security, rate limiting, **and** maintained the direct routing maps (e.g., `/user` $\rightarrow$ `10.0.1.55:8080`).

#### The New Way (With Kubernetes Clusters)
In Kubernetes, pods are highly volatile. They are constantly destroyed, rescheduled, scaled up from 2 to 20 instances, and assigned completely random internal IP addresses every single minute.
- **The Bottleneck:** An external API Gateway (like Broadcom Layer7 or Apigee sitting outside the cluster) cannot keep up with thousands of pods changing internal IPs every second. It doesn't have visibility into the internal Kubernetes network.
- **The Solution:** You **offload** the internal path routing to the **Ingress Controller**, because it sits _inside_ the cluster and listens directly to the Kubernetes control plane. It is always aware of live pod locations.
    

### 2. The Clean Separation of Concerns (The Production Blueprint)
Instead of one tool doing everything, you create a specialized pipeline where each layer focuses on what it does best.
#### Layer 1: The Enterprise API Gateway (The "Business Security" Boundary)
The API Gateway sits at the corporate edge. It is completely blind to internal Kubernetes pod IPs. It only knows the entry point of your cluster's Ingress Controller.

- **What it focuses on (Cross-Cutting Concerns):**
    - **Global Authentication:** Validating OAuth2 tokens, checking corporate single sign-on (SSO), and verifying API keys.
    - **Traffic Management:** Enforcing strict consumer rate limits (e.g., Bronze tier gets 100 requests/min; Gold gets 10,000 requests/min).
    - **Audit & Analytics:** Logging monetization metrics, tracking client billing usage, and running corporate Web Application Firewall (WAF) checks.
- **Its Routing Job:** It has a single, static route rule: _"If the token is valid, forward 100% of the traffic straight to the Kubernetes Ingress Controller."_

#### Layer 2: The Kubernetes Ingress Controller (The "Infrastructure Routing" Engine)
The Ingress Controller sits at the cluster edge. It doesn't care about your company's business tiers or billing plans; its only job is raw, high-speed internal traffic direction.

- **What it focuses on:**
    - **Path-Based Internal Routing:** Reading the Layer 7 URI (`/user`, `/products`, `/task`) and matching it to internal Kubernetes Services.
    - **Pod Load Balancing:** Evenly distributing TCP/HTTP packets across the 10 or 20 running pods of a specific service.
    - **Deployment Strategies:** Handling <mark style="background: #FFB86CA6;">Canary or Blue-Green traffic </mark>splits at the network layer.

### 3. How the URI Mapping Actually Looks in Code
Because of this offloading, you don't repeat the complex service routing maps inside your API Gateway.
#### Step 1: The Map Inside the External API Gateway
Your external API Gateway profile stays completely simple and uniform. It just maps your public API paths to the **Cluster Entry Point**:

|**External Public URI**|**Action / Policy Applied**|**Downstream Target (Forwarding Destination)**|
|---|---|---|
|`www.myoffice.com/user`|Check JWT Token + Rate Limit|`http://internal-cluster-nlb.local/user`|
|`www.myoffice.com/products`|Check JWT Token + Rate Limit|`http://internal-cluster-nlb.local/products`|
|`www.myoffice.com/task`|Check JWT Token + Rate Limit|`http://internal-cluster-nlb.local/task`|

#### Step 2: The Map Inside the Kubernetes Ingress Controller
Once the API Gateway passes the traffic through the Network Load Balancer (NLB), it hits your Nginx Ingress Controller manifest. This is where the fine-grained, internal container routing is executed:


```YAML
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: cluster-internal-router
  namespace: production
spec:
  ingressClassName: nginx
  rules:
  - host: www.myoffice.com
    http:
      paths:
      - path: /user
        pathType: Prefix
        backend:
          service:
            name: user-service # Maps directly to the dynamic User Pods
            port: { number: 8081 }
      - path: /products
        pathType: Prefix
        backend:
          service:
            name: products-service # Maps directly to the dynamic Product Pods
            port: { number: 8082 }
```
