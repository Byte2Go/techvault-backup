In a modern enterprise architecture, **each microservice has its own dedicated deployment and service files.** 
They live directly inside the **App's Code Repository** in a folder usually named `/k8s` or `/deploy`.
### The Microservice Repository File Tree:
```
order-service-repo/  (Your App Code Repository)
├── src/
│   └── main/
│       └── resources/
│           └── application.yml  ◄──[Owned by Developer] Inside the jar artifact.
└── k8s/    ◄── [Collaborative / DevOps] Standard text files.
    ├── order-deployment.yml ◄── Defines how to run the container (replicas,CPU).
    └── order-service.yml ◄── Defines how to route network traffic to containers.
```

- **`application.yml`** $\rightarrow$ **Owned by Developers.** Packaged directly inside your compiled code artifact. It tells your framework how to behave.
- **`order-deployment.yml` & `order-service.yml`** $\rightarrow$ **Owned by the App Team (DevOps/Developers together).** These are plain text files that sit right next to your code. <mark style="background: #ADCCFFA6;">When your pipeline runs, it reads these files to update the infrastructure.</mark>

## 2. Deployment File vs. Service File: The One-to-One Rule
You need **both** files for **every single app**. They serve entirely different purposes:
### order-deployment.yml (The Application Process File)
- **What it does:** It tells the Control Plane <mark style="background: #D2B3FFA6;">how to physically pull your compiled code image</mark>, how many instances (`replicas`) to spin up, and <mark style="background: #FFF3A3A6;">what hardware limits to give them</mark>.
- **Analogy:** This is the blueprint for building the <mark style="background: #FFB86CA6;">physical factory instances</mark>.
### order-service.yml (The Network Routing File)
- **What it does:** It sets up a permanent <mark style="background: #FFB8EBA6;">internal network domain name</mark> (like `http://order-service`). <mark style="background: #FFF3A3A6;">Because Pods are constantly dying and getting recreated with new IP addresses,</mark> other microservices (like `payment-service`) point to this Service file instead of hunting for raw Pod IPs.
- **Analogy:** This is the <mark style="background: #ABF7F7A6;">permanent receptionist desk that routes incoming phone calls</mark> to whoever is currently working in the factory.
## 3. Connecting the Health API to K8s Probes
Earlier, we configured `application.yml` to expose `/actuator/health/readiness`. But **how** does Kubernetes actually know to check that URL?

You have to <mark style="background: #FFB86CA6;">explicitly link them inside your **`order-deployment.yml`** file under a configuration block called **Probes**. </mark> <mark style="background: #D2B3FFA6;">This is where you tell the Kubernetes worker node agent (`kubelet`) to start pinging your app's internal endpoints.</mark>

Here is exactly how the `application.yml` setup connects directly to the `order-deployment.yml` setup at runtime:

```YAML
# Inside order-deployment.yml
spec:
  template:
    spec:
      containers:
      - name: order-service
        image: company/order-service:1.2.3
        
        # LINKING THE HEALTH API TO K8S HERE:
        readinessProbe:
          httpGet:
            path: /actuator/health/readiness #◄── K8s hits this exposed path  
            port: 8080         #     by your application.yml configuration!
          initialDelaySeconds: 15   # Wait 15s for your Spring app to boot first
          periodSeconds: 5     # Ping it every 5s after that
```

### The Operational Flow:
1. Your Spring/Node app boots up inside a Pod container.
2. The **`kubelet`** agent on the Worker Node reads your `order-deployment.yml` file, notices the `readinessProbe` block, and begins sending a background HTTP request to `http://localhost:8080/actuator/health/readiness` every 5 seconds.
3. <mark style="background: #BBFABBA6;">If your code returns a `200 OK`, the `kubelet` tells the cluster: _"The app is fully ready."_</mark>
4. <mark style="background: #FFB86CA6;">The cluster then opens up your **`order-service.yml`** network line and allows live user traffic to reach that Pod.</mark>

---
### ## The Three Production Probes
Kubernetes uses **three distinct types of probes** inside your `order-deployment.yml` file. Each probe has a completely different job, runs at a different stage of the container's life, and forces the cluster to make a different architectural decision if it fails.

| **Probe Type**                                           | **The Main Question It Asks**                                             | **What Happens If It Fails?**                                       | **Real-World Use Case**                                                                                                     |
| -------------------------------------------------------- | ------------------------------------------------------------------------- | ------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------- |
| **1. Startup Probe**<br><br>_(The Shield)_               | _"Is the application process finished initializing yet?"_                 | **K8s kills the container** and restarts it.                        | ==Prevents slow-starting apps from getting killed prematurely==  by the liveness probe before they even finish booting.     |
| **2. Readiness Probe**<br><br>_(The Traffic Gatekeeper)_ | _"==Is the app ready to process live customer requests==?"_               | **K8s keeps the container running but cuts off web traffic** to it. | ==Prevents users from getting `500 Internal Server Errors`== during a heavy database migration or high-load crunch.         |
| **3. Liveness Probe**<br><br>_(The Executioner)_         | _"Is the ==app still healthy==, or is it permanently frozen/deadlocked?"_ | **K8s instantly kills the container** and boots a fresh one.        | Automatically ==self-heals applications== that suffer from deadlocks or internal thread lockups without human intervention. |
