From an architectural standpoint, <mark style="background: #ADCCFFA6;">Kubernetes acts as a declarative state machine.</mark> As a technical lead, your job is to understand how the platform's routing components interface with compute resources, and how to triage failures when the actual state deviates from the desired state.

### 1. Ingress Routing & Service Architecture
<mark style="background: #FFF3A3A6;">Traffic entering a Kubernetes cluster</mark> flows through a decoupled, multi-tiered networking model designed to isolate the application runtime from external network topologies.

```
[External Traffic] ──> [Azure Application Gateway / Ingress]
                                 │
                        (Decodes HTTP / Rules)
                                 ▼
                         [Cluster IP Service]
                                 │
                     (Layer 4 IPVS Load Balancing)
                                 ▼
                     [Pod A]  [Pod B]  [Pod C]
```

- **Ingress Controller (The Gatekeeper):** Positioned at the edge of the cluster, the Ingress Controller (e.g., NGINX Ingress, Azure Application Gateway Ingress Controller) acts as a Layer 7 reverse proxy. It terminates SSL/TLS, evaluates routing rules based on HTTP host headers or paths, and directs traffic inward.
- **Services (The Abstraction Layer):** Pods are highly transient and ephemereal; their IP addresses change constantly upon restart. A Kubernetes **Service** provides a persistent, static IP address and DNS name (`ClusterIP`) that acts as a stable entry point.
- **The Routing Mechanics:** The Service does not route traffic directly. Instead, the `kube-proxy` daemon running on every node programs local kernel firewall rules (using IPVS or iptables). This mechanism intercept traffic heading to the Service IP and load-balances it at Layer 4 directly across the healthy application Pod endpoints.
    

### 2. Configuration & Secret Governance

To build a secure, cloud-native application pipeline, application configurations must be entirely decoupled from the underlying containerized code.

- **ConfigMaps:** Injected as environment variables or mounted as read-only files inside the container. They store non-sensitive key-value configurations, such as JBoss subsystem profiles, database target hostnames, or log level parameters.
    
- **Secrets:** Structured identically to ConfigMaps but stored as Base64 encoded strings within the cluster database (`etcd`). These are reserved for cryptographic keys, database credentials, and Azure SSO client tokens.
    
- **Architectural Guardrail:** For production environments, Secrets should be mounted as **ephemeral volumes** rather than environment variables. If a container suffers a memory leak and generates a heap dump, any credentials stored in environment variables will be written to disk in plain text. Volume-mounted secrets reside strictly in the container's volatile memory and clear out instantly upon container termination.
    

### 3. Triage Framework for Pod Failure States

When the cluster control plane cannot achieve the desired declarative state defined in your deployment manifests, pods fall into distinct failure modes.

#### I. `CrashLoopBackOff` (Runtime / Configuration Failure)

The orchestrator schedules and starts the container successfully, but the root process inside terminates or crashes immediately after booting. Kubernetes then initiates an exponential restart back-off delay.

- **The Root Cause:** Malformed configurations inside a ConfigMap, missing credentials within a Secret, or an application initialization script throwing a fatal exception (e.g., JBoss failing to bind to a port).
    
- **Architectural Resolution:** Inspect previous container process failures using `kubectl logs <pod-name> --previous`. Ensure heavy application boots are guarded by a defensive `startupProbe` to prevent the platform from prematurely killing the pod while it initializes.
    

#### II. `Pending` (Scheduling Failure)

The pod definition has been accepted by the cluster database, but the control plane's `kube-scheduler` cannot find a suitable worker node to host the container.

- **The Root Cause:** The compute resources requested (`requests: memory / cpu`) within the deployment manifest exceed the total available, unallocated capacity of the active node pools. Alternatively, strict placement constraints like `nodeSelector` or `antiAffinity` rules cannot be satisfied by the current infrastructure topology.
    
- **Architectural Resolution:** Run `kubectl describe pod <pod-name>` to extract scheduling events. If resource starvation is confirmed, coordinate with the DevOps layer to trigger a horizontal node scale-out via the Cloud Cluster Autoscaler.
    

#### III. `Evicted` (Host Resource Preservation Failure)

A running, healthy pod is actively and forcibly terminated by the local node manager (`kubelet`) to protect the node's underlying operating system kernel.

- **The Root Cause:** The host node has breached its critical threshold for memory or ephemeral disk space. To prevent a kernel panic, the node evicts low-priority or resource-unbounded containers.
    
- **Architectural Resolution:** Mandate strict resource `limits` in all deployment templates. This ensures a runaway container with a memory leak is contained within its own cgroup allocation and cleanly executed via a localized `OOMKilled` event, preventing it from destabilizing neighboring workloads on the shared host.
    

### 💡 Accenture Interview Articulation

> _"When triaging a production outage on a Kubernetes cluster, I track the failure systematically based on where the declarative loop breaks down. If traffic drops entirely, I bypass the application tier and inspect the Layer 7 Ingress Controller and Layer 4 Service routing endpoints to check for network path blocks. If individual application components are failing, I categorize them by their pod state: I handle `CrashLoopBackOff` as an application configuration or probe initialization failure; I treat a `Pending` state as a capacity-planning and scheduling bottleneck requiring cluster autoscaling; and I view `Eviction` as a platform-protection response that requires us to enforce strict cgroup limits to isolate resource-intensive microservices."_