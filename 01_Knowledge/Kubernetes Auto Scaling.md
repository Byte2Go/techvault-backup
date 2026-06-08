To scale elastically during traffic surges, you must <mark style="background: #FFF3A3A6;">configure two completely independent automation planes</mark> that communicate via state changes.

| **Scaling Element**                 | **Target Layer**                                  | **Where It Is Configured**                                                                             | **Team Ownership Boundary**                                                                         |
| ----------------------------------- | ------------------------------------------------- | ------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------- |
| **Horizontal Pod Autoscaler (HPA)** | **Application Pods** _(Hierarchy Level 3)_        | Placed inside your microservice repo code directory as a standalone file: **`k8s/order-hpa.yml`**      | **App Development / DevOps Team** (You define when your specific code requires duplicates).         |
| **Cluster Autoscaler**              | **Physical Infrastructure** _(Hierarchy Level 2)_ | Configured globally ==outside your code repo via Cloud Console or Infrastructure-as-Code (Terraform)== | **Central Platform / Cloud Engineering Team** (Manages physical cloud VM node limits and AWS ASGs). |

### Manifest Configuration Spec (`k8s/order-hpa.yml`)
This file sits directly next to your `order-deployment.yml` and explicitly targets it.

```YAML
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: order-service-hpa
  namespace: production   # ◄── Target application's logical workspace boundary
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: order-service    # ◄── Binds directly to your app's deployment manifest
  minReplicas: 2                  # Continuous steady-state minimum footprint
  maxReplicas: 20   # Upper safety limit to prevent run-away compute bill spikes
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70 # ◄──Scaleout when container compute load hits 70%
```

### The Operational Hand-Off Flow
During a high-concurrency traffic event, the configuration files trigger a synchronized chain reaction across the application and infrastructure boundaries:
1. **The Core Trigger:** Massive user volume hits the network. The internal metrics monitor registers that average container CPU across your base instances has breached **70%**.
2. **The App Expansion:** The HPA engine catches the breach, checks your `order-hpa.yml` rules, and updates the active live deployment state to scale your instances up (e.g., from 2 to 10 instances).
3. **The Infrastructure Bottleneck:** The Master Node's `kube-scheduler` attempts to deploy the 8 new Pod structures. <mark style="background: #FFB8EBA6;">However, your active **Worker Node VMs** are completely maxed out on physical hardware resources. </mark> <mark style="background: #FF5582A6;">The new Pod definitions freeze in a **`Pending`** state.</mark>
4. **The Infrastructure Intervention:** The global **Cluster Autoscaler** system utility (running at the Platform Layer) catches the `Pending` status.<mark style="background: #ABF7F7A6;"> It recognizes that the cluster's physical compute engine has hit a hard capacity wall.</mark>
5. **The Resolution:** <mark style="background: #ADCCFFA6;">The Cluster Autoscaler invokes your cloud provider's API (e.g., AWS EC2 Auto Scaling Group). </mark> <mark style="background: #D2B3FFA6;">It dynamically forces a new physical VM node server to boot and join the cluster topology.</mark> Once registered, the scheduler finishes mapping your waiting application Pods to the fresh hardware, and the system absorbs the traffic load.