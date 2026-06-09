# P3 · Day 4 — AWS · Kubernetes · CI/CD · GitOps · Networking · FinOps
**Pillar:** P3 — Cloud & DevOps  
**Role Priority:** SA 🔵 Core · Java 🟢 Supporting · AI 🟣 Supporting  
**Day in Plan:** Day 4 (Week 1)  
**Time:** ~3 hours study + 1 hour Q&A practice

---
## Topic 1 · AWS Well-Architected Framework
### In One Line
The AWS Well-Architected Framework's 5 pillars are the lens every cloud SA <mark style="background: #FFB86CA6;">uses to evaluate an architecture</mark> — know them cold because every AWS interview opens here.

### The 5 Pillars

| Pillar                     | Core Question                    | Key Practices                                                       |
| -------------------------- | -------------------------------- | ------------------------------------------------------------------- |
| **Operational Excellence** | Can we run and improve?          | ==IaC==, runbooks, ==observability==, small frequent changes        |
| **Security**               | Are we protected?                | Least privilege IAM, encryption at rest/transit, VPC isolation, WAF |
| **Reliability**            | Can we ==recover from failure==? | Multi-AZ, auto-scaling, circuit breakers, chaos engineering         |
| **Performance Efficiency** | Are we using resources well?     | Right-size compute, caching, CDN, read replicas                     |
| **Cost Optimization**      | Are we ==spending wisely==?      | Reserved instances, spot, rightsizing, delete unused resources      |

> 6th pillar added 2022: **Sustainability** — minimize carbon footprint, right-size, prefer managed services.

### AWS Well-Architected Review Process
1. Select workload in AWS Well-Architected Tool
2. Answer questions per pillar → identifies High/Medium/Low risks
3. Produce improvement plan
4. Review quarterly or on major changes

### Interview Q&A
**Q: Walk me through the AWS Well-Architected Framework.**
A: Five pillars — Operational Excellence (run and improve via IaC and observability), Security (least privilege, encrypt everything, VPC isolation), Reliability (design for failure — multi-AZ, auto-scaling, health checks), Performance Efficiency (right-size, cache, CDN), Cost Optimization (reserved capacity for steady-state, spot for batch, delete waste). I run a Well-Architected Review at the start of every major project and quarterly after — the AWS tool generates a risk report automatically.

---

## Topic 2 · ECS Fargate vs EKS — When to Use Each
### In One Line
<mark style="background: #ABF7F7A6;">ECS Fargate is serverless containers</mark> <mark style="background: #FFF3A3A6;">with no cluster management </mark>— <mark style="background: #BBFABBA6;">EKS is Kubernetes with full control and portability</mark> <mark style="background: #FFB8EBA6;">but operational overhead.</mark>

### Comparison

| Dimension                  | ECS Fargate                           | EKS (Kubernetes)                                  |
| -------------------------- | ------------------------------------- | ------------------------------------------------- |
| **Cluster management**     | None — AWS manages fully              | You manage ==control plane== (or pay for managed) |
| **Operational complexity** | Low                                   | High                                              |
| **AWS lock-in**            | High (ECS-native)                     | Low (k8s is portable)                             |
| **Ecosystem**              | AWS native (IAM, ALB, CloudWatch)     | k8s ecosystem (Helm, Istio, ArgoCD)               |
| **Cost**                   | Pay per task vCPU/memory              | EC2 node cost + ==control plane fee==             |
| **Workload fit**           | Simpler apps, fast start, small teams | Complex apps, service mesh, multi-cloud future    |
| **Auto-scaling**           | Application Auto Scaling              | HPA + Cluster Autoscaler                          |

### Decision Framework

```
Start here: Does your team have Kubernetes expertise?
  NO → ECS Fargate (lower ops burden, faster to ship)
  YES → Is multi-cloud portability or service mesh a requirement?
    YES → EKS
    NO → ECS Fargate still simpler; EKS only if ecosystem benefit is real
```

> **SA answer:** "I default to ECS Fargate for new teams or simpler workloads — you get managed containers without k8s overhead. I recommend EKS when the org has Kubernetes expertise, needs service mesh (Istio), or ==has multi-cloud ambitions.=="

### ECS Core Concepts
```
Cluster → Service → Task Definition → Task (running container)

Task Definition: image, CPU/memory, env vars, port mappings, IAM role
Service: desired count, load balancer, auto-scaling policy
```

---

## Topic 3 · Kubernetes Deep Dive

### In One Line
Kubernetes is the industry-standard <mark style="background: #FFB86CA6;">container orchestration platform</mark> — as an SA you must know deployments, services, HPA, namespaces, and how they map to architecture decisions.

[[Kubernetes Fundamental Architecture]]
[[Kubernetes Configuration]]
### Services — Exposing Pods
In Kubernetes, Pods are highly volatile—they crash, scale up, scale down, and get rescheduled constantly. Every single time a Pod is recreated, it receives a brand-new, random internal IP address.

If your `payment-service` tried to talk directly to an `order-service` Pod IP, the connection would break within minutes.

The **Service file** solves this by creating a <mark style="background: #D2B3FFA6;">**permanent, unchanging virtual IP and DNS name** (like `http://order-service`) inside the cluster</mark>. <mark style="background: #ADCCFFA6;">It acts as a static, internal load balancer that sits in front of your moving Pods.</mark>

| Service Type   | Use Case                                             |
| -------------- | ---------------------------------------------------- |
| `ClusterIP`    | ==Internal only — service-to-service communication== |
| `NodePort`     | Exposes on each node's IP:port — dev/testing         |
| `LoadBalancer` | ==Creates cloud LB (ALB on AWS) — external access==  |
| `ExternalName` | DNS alias to external service                        |

```yaml
# Inside order-service.yml
apiVersion: v1
kind: Service
metadata:
  name: order-service
spec:
  selector:
    app: order-service
  ports:
  - port: 80
    targetPort: 8080
  type: ClusterIP  # Internal — accessed via order-service.default.svc.cluster.local
```

### HPA — Horizontal Pod Autoscaler
[[Kubernetes Auto Scaling]]
[[Kubernetes Networking - User Traffic]]
> **SA note:** HPA scales pods. Cluster Autoscaler scales nodes (adds EC2 instances when pods can't be scheduled). Both needed in production.

### Namespace Strategy for Multi-Team/Multi-Tenant

```
Namespaces:
├── production/       → order-service, payment-service, inventory-service
├── staging/          → same services, lower resource limits
├── development/      → per-team or per-feature namespaces
├── monitoring/       → prometheus, grafana, jaeger
└── ingress-nginx/    → ingress controller
```

**Resource quotas per namespace:**
```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: production-quota
  namespace: production
spec:
  hard:
    requests.cpu: "10"
    requests.memory: "20Gi"
    limits.cpu: "20"
    limits.memory: "40Gi"
    pods: "50"
```

### Helm — Package Manager for k8s
[[Kubernetes - Helm Package Manager]]

**Chart structure:**
[[Kubernetes - ConfigMap]]
```
order-service/
├── Chart.yaml          # Chart metadata
├── values.yaml         # Default values
├── values-prod.yaml    # Prod overrides
└── templates/
    ├── deployment.yaml
    ├── service.yaml
    ├── hpa.yaml
    └── configmap.yaml
```

### Interview Q&A
**Q: How do you handle zero-downtime deployments in Kubernetes?**
A: <mark style="background: #ABF7F7A6;">Rolling update strategy </mark>in the Deployment spec -<mark style="background: #ADCCFFA6;">Kubernetes brings up new pods, waits for readiness probe to pass, then terminates old pods one by one.</mark> <mark style="background: #FFB8EBA6;">The readiness probe is critical — it gates traffic routing. </mark> <mark style="background: #D2B3FFA6;"> For riskier releases, use **blue-green** (deploy new version alongside old, switch traffic at ingress) or **canary** (route 10% to new, monitor, then 100%).</mark>

**Q: How do you design Kubernetes namespaces for a 20-service microservices system?**
A: I namespace <mark style="background: #FFB86CA6;">by environment first (production, staging, dev) and by concern (monitoring, ingress).</mark> Each environment namespace gets **ResourceQuotas** and **LimitRanges** to prevent one team's misconfigured service from starving others. <mark style="background: #D2B3FFA6;">Network policies restrict cross-namespace traffic — services can't communicate across environments.</mark> RBAC per namespace — dev team has full access to their dev namespace, read-only to staging, no direct access to production (CI/CD deploys to prod).

**Q: What is the difference between liveness and readiness probes?**
A: <mark style="background: #ADCCFFA6;">Readiness probe controls traffic routing — pod gets removed from the Service endpoints when readiness fails </mark>(stops receiving new requests but keeps running). <mark style="background: #FFB86CA6;">Liveness probe controls pod lifecycle — pod gets killed and restarted when liveness fails</mark>. <mark style="background: #ADCCFFA6;">Set readiness to fail during startup (app loading) and during overload. </mark> <mark style="background: #FFB86CA6;">Set liveness to detect deadlock or stuck state. </mark> <mark style="background: #BBFABBA6;">Never make liveness probe dependent on external services — if the DB is down, you don't want all pods killed.</mark>

---

## Topic 4 · CI/CD Pipeline Design

### In One Line
A production CI/CD pipeline automates <mark style="background: #ADCCFFA6;">build → test → scan → deploy with quality gates</mark> <mark style="background: #BBFABBA6;">that prevent bad code from reaching production.</mark>

### Pipeline Stages for a Java Microservice
- **Read:** [[Git- Code Push vs Pull Request (PR)]]
- **Read**: [[CI CD Pipeline- From a Developer's Laptop to Production]]
```
[Code Push / PR(Pull Request)]
      ↓
[CI Pipeline — runs on every PR]
  1. Checkout + cache dependencies
  2. Compile (mvn compile)
  3. Unit Tests (mvn test) — must pass, coverage > 80%
  4. Contract Tests (Pact verification)
  5. Code Quality (SonarQube scan) — quality gate must pass
  6. SAST — Static Application Security Testing (Checkmarx / Snyk)
  7. Build Docker image
  8. Image scan (Qualys/ Trivy / Snyk Container) — no critical CVEs
  9. Push to ECR / Artifactory (tagged with git SHA)

[Merge to main — triggers CD]
  9.  Deploy to Dev namespace (auto)
  10. Dev Smoke Tests
  11. Integration Tests (Testcontainers / real infra)
  12. Deploy to Staging (auto)
  13. Staging Smoke Tests
  14. Performance Tests (k6 / Gatling) — latency regression check
  15. Manual approval gate (for production)
  16. Deploy to Production (blue-green or canary)
  17. Post-deploy smoke test
  18. Rollback trigger if error rate > threshold
```

### GitHub Actions Example (Java Microservice)

```yaml
name: CI Pipeline
on:
  pull_request:
    branches: [main]

jobs:
  build-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Java 21
        uses: actions/setup-java@v4
        with:
          java-version: '21'
          distribution: 'temurin'
          cache: maven
      
      - name: Build and Test
        run: mvn clean verify -Pcoverage
      
      - name: SonarQube Scan
        env:
          SONAR_TOKEN: ${{ secrets.SONAR_TOKEN }}
        run: mvn sonar:sonar
      
      - name: Build Docker Image
        run: docker build -t order-service:${{ github.sha }} .
      
      - name: Scan Image (Trivy)
        uses: aquasecurity/trivy-action@master
        with:
          image-ref: order-service:${{ github.sha }}
          severity: 'CRITICAL,HIGH'
          exit-code: '1'  # Fail if critical CVEs found
      
      - name: Push to ECR
        run: |
          aws ecr get-login-password | docker login --username AWS --password-stdin $ECR_URL
          docker push $ECR_URL/order-service:${{ github.sha }}
```

### Pipeline for 20 Microservices — Monorepo vs Polyrepo
[[CI CD- Polyrepo vs. Monorepo]]

| Approach                                | Pros                                                 | Cons                                                   |
| --------------------------------------- | ---------------------------------------------------- | ------------------------------------------------------ |
| **Polyrepo** (one repo per service)     | Independent pipelines, clear ownership               | Hard to do cross-service changes, many repos to manage |
| **Monorepo** (all services in one repo) | Atomic cross-service changes, single pipeline config | Build all or nothing without smart change detection    |

### Interview Q&A

**Q: Design a CI/CD pipeline for 20 microservices with a polyglot stack.**
A: I'd use a monorepo with path-based change detection — ==only the services that changed trigger their pipelines==. Shared pipeline template (GitHub Actions reusable workflow or Jenkins shared library) parameterized per language (Java uses Maven, Python uses pip/pytest, Node uses npm). Each service pipeline: unit tests → SAST scan → Docker build → image scan → push to registry → deploy to dev → integration tests → staging → approval gate → canary to prod. Pact contract tests run in the provider's pipeline — provider can't deploy if it breaks any consumer contract.

**Q: How do you prevent a bad deployment from impacting production?**
A: Multiple gates.<mark style="background: #ABF7F7A6;"> Quality gate in CI (SonarQube fails if coverage drops or code smells spike)</mark>. <mark style="background: #ADCCFFA6;">Image scan rejects critical CVEs.</mark> <mark style="background: #D2B3FFA6;">Canary deployment — route 5% of traffic to new version, monitor error rate and latency for 10 minutes via CloudWatch/Prometheus alerts.</mark> If metrics degrade, automated rollback triggers (ArgoCD rollback or `kubectl rollout undo`). Post-deploy smoke tests fail fast. The rollback must be tested in staging too — it's useless if it doesn't work when you need it.

---

## Topic 5 · Deployment Patterns — Blue-Green & Canary
### In One Line
<mark style="background: #BBFABBA6;">Blue-green gives instant rollback; canary reduces blast radius</mark> — choose based on how much risk you can accept per deployment.

### Blue-Green Deployment
```
Load Balancer
    ├── Blue (current production — v1.0) ← 100% traffic
    └── Green (new version — v1.1)       ← 0% traffic

Steps:
1. Deploy v1.1 to Green (parallel environment)
2. Run smoke tests against Green (direct access, not via LB)
3. Switch LB: 100% traffic → Green
4. Monitor for 30 minutes
5. If OK → decommission Blue
6. If problem → switch LB back to Blue (instant rollback, <1 min)
```

**Cost:** Requires 2x infrastructure during deployment window.  
**Best for:** High-risk releases, compliance-sensitive systems, <mark style="background: #FFB86CA6;">when you need instant rollback.</mark>

### Canary Deployment

```
Load Balancer
    ├── Stable (v1.0) ← 90% traffic
    └── Canary (v1.1) ← 10% traffic

Steps:
1. Deploy v1.1 to canary pool (10% of pods)
2. Monitor error rate, latency, business metrics for N minutes
3. If stable → 25% → 50% → 100% (progressive rollout)
4. If degraded → route 0% to canary, keep stable at 100%
```

**In Kubernetes (Argo Rollouts):**
```yaml
apiVersion: argoproj.io/v1alpha1
kind: Rollout
spec:
  strategy:
    canary:
      steps:
      - setWeight: 10     # 10% to canary
      - pause: {duration: 10m}
      - setWeight: 25
      - pause: {duration: 10m}
      - analysis:         # Auto-check metrics before proceeding
          templates:
          - templateName: error-rate-check
      - setWeight: 100
```

**Best for:** Most production releases — <mark style="background: #D2B3FFA6;">lower cost than blue-green, gradual risk exposure.</mark>

### Feature Flags (LaunchDarkly / Unleash)
Decouple deployment from release:
```java
if (featureFlags.isEnabled("new-payment-flow", userId)) {
    return newPaymentService.process(request);
} else {
    return legacyPaymentService.process(request);
}
```
Deploy to 100% of servers but only enable for 1% of users → ring-based rollout without k8s complexity.

---

## Topic 6 · Terraform — IaC Basics [[Terraform (IaC)]]

### In One Line
Terraform <mark style="background: #FFB86CA6;">declaratively defines cloud infrastructure as code</mark> — version-controlled, repeatable, reviewable, and destroyable.

### Core Concepts

```hcl
# provider.tf
terraform {
  required_providers {
    aws = { source = "hashicorp/aws", version = "~> 5.0" }
  }
  backend "s3" {
    bucket = "mycompany-tf-state"
    key    = "order-service/terraform.tfstate"
    region = "ap-south-1"
    dynamodb_table = "terraform-locks"  # Prevents concurrent applies
  }
}

# main.tf
resource "aws_ecs_service" "order_service" {
  name            = "order-service"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.order.arn
  desired_count   = 3

  load_balancer {
    target_group_arn = aws_lb_target_group.order.arn
    container_name   = "order-service"
    container_port   = 8080
  }

  lifecycle {
    ignore_changes = [desired_count]  # Let auto-scaling manage count
  }
}

# variables.tf
variable "environment" {
  type    = string
  default = "production"
}
```

### Terraform Workflow 

```
terraform init      # Download providers, configure backend
terraform plan      # Show what will change (always review!)
terraform apply     # Apply changes
terraform destroy   # Tear down (with caution in prod)
```

**State management best practices:**
- Remote state in S3 + DynamoDB locking (never local state in team setting)
- Separate state files per environment (prod vs staging)
- State file = sensitive — enable S3 versioning + encryption

### Module Structure for Large Orgs

```
infrastructure/
├── modules/
│   ├── ecs-service/        # Reusable ECS service module
│   ├── rds-postgres/       # Reusable RDS module
│   └── vpc/                # Reusable VPC module
├── environments/
│   ├── production/
│   │   ├── main.tf         # Uses modules with prod vars
│   │   └── terraform.tfvars
│   └── staging/
│       ├── main.tf
│       └── terraform.tfvars
```

### Interview Q&A
**Q: How do you manage Terraform state in a team?**
A: <mark style="background: #D2B3FFA6;">Remote state in S3 with DynamoDB locking</mark> — prevents two engineers from running `terraform apply` simultaneously (which would corrupt state). <mark style="background: #ADCCFFA6;">State file is encrypted (S3 SSE).</mark>  <mark style="background: #FFF3A3A6;">Separate state files per environment — staging and prod never share state. </mark>Terraform Cloud or Atlantis for plan/apply in CI — no one runs Terraform manually from their laptop in production.

---

## Topic 7 · GitOps — ArgoCD: The Kubernetes Application Deployer [[ArgoCD (GitOps)]]
**Terraform** builds the foundation (the house), and **ArgoCD** manages the applications running inside it (the furniture).
### In One Line
<mark style="background: #FFB86CA6;">GitOps makes Git the single source of truth for what runs in your cluster </mark>— the cluster continuously reconciles to match the desired state declared in Git.

### How GitOps Works

```
Developer merges PR → Git repo updated (Helm chart / k8s manifests)
                          ↓
              ArgoCD watches Git repo (pull-based)
                          ↓
              ArgoCD compares: desired state (Git) vs actual state (cluster)
                          ↓
              If drift detected → ArgoCD syncs cluster to match Git
                          ↓
              Audit trail: every change to cluster is a Git commit
```

**Key properties:**
- **Pull-based** — ArgoCD pulls from Git (no CI push credentials in cluster)
- **Drift detection** — alerts or auto-heals when someone `kubectl apply`s directly
- **Rollback** = `git revert` → ArgoCD re-syncs → previous version deployed
- **Audit** — every deployment is a Git commit with author, timestamp, reason
### Interview Q&A
**Q: What is GitOps and why is it better than push-based CD?**
A: <mark style="background: #FFB86CA6;">GitOps makes Git the single source of truth for cluster state. </mark> <mark style="background: #ADCCFFA6;">ArgoCD continuously pulls desired state from Git and reconciles the cluster to match.</mark> Advantages over push-based CD: <mark style="background: #BBFABBA6;">no CD pipeline needs kubectl credentials (security), drift detection catches manual changes (operations), rollback is a git revert (auditable), and the cluster state is always visible in Git</mark>. Push-based CD is imperative — "deploy this now." GitOps is declarative — "cluster should always look like this."

---
## Topic 8 · Networking & Load Balancing on AWS
### In One Line
Understanding VPC design, ALB vs NLB, and CDN/DNS routing is table stakes for any SA designing on AWS.

### VPC Design — Standard Multi-Tier
#### Step1-: Decision Path: Public or Private Subnet?
1. **Does the resource need to be directly accessible** **from the public internet****?**
	- **YES** → Place it in a **Public Subnet** (with a route to an IGW).
	- **NO** → Go to step 2.
2. **Does the resource need to initiate** **outbound connections to the internet (e.g., for API calls, updates)****?**
	- **YES** → Place it in a **Private Subnet** and use a **NAT Gateway**.
	- **NO** → Place it in a **Private Subnet**.
```
VPC: 10.0.0.0/16 (ap-south-1)
├── Public Subnets (10.0.1.0/24, 10.0.2.0/24) — AZ-a, AZ-b
│   └── NAT Gateway, ALB, Bastion (if needed)
├── Private Subnets (10.0.10.0/24, 10.0.11.0/24) — AZ-a, AZ-b
│   └── ECS tasks / EKS nodes / EC2 (no direct internet)
└── Database Subnets (10.0.20.0/24, 10.0.21.0/24) — AZ-a, AZ-b
    └── RDS, ElastiCache (no route to internet)

Internet Gateway → Public Subnets
NAT Gateway → Private Subnets can reach internet (updates, APIs) but not inbound
```
- **VPC** = Your private network in AWS.
- **Public Subnet** has a route to an **Internet Gateway (IGW)**.
- **Private Subnet** has **NO** route to an IGW.
- **NAT Gateway** allows private instances to access the internet (outbound only).

_![](data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAeEAAAFvCAYAAAB98HOmAAAAAXNSR0IArs4c6QAAIABJREFUeF7tnQecFEX2x1/1pM1sIIOASgZzRL0znGA6wxnwDBhhQTCcggEjYFbQ01OUYEQ9FfU8PRPmvyIYzoBKFAUkw+Y0sev/qYae6x1md3tmu2c6/ObjfHBnq169+r6a/fWrej3DaOdj1qxZN/z666/lsiznNjY2drjnnnvuE7+qrKzMvfPOO68T/+/z+ZrwOjhgPeB9gb8D+DuAvwOp/x0QOnrttddOzs3N/bmxsXHqrFmz/s3Eiw0NDTNjsdhlkiQRY8pLeIAACIAACIAACBhMgHNOP/74I+Xl5b344IMPXsxuuumm10eOHHlq3759DR4K5kAABEAABEAABFoiIMvyUWzixImbpk2b1hWYQAAEQAAEQAAEMkeAc34du/baazdNmTIFIpw57hgJBEAABEAABOiZZ575hN15550//O1vf9sbPEAABEAABEAABDJH4OqrryZWV1c3RZKk2zI3LEYCARAAARAAARCACGMNgAAIgAAIgECWCCjb0S+99NJrf/7zn/+SJR8wLAhkjUBTUxNdf/31tHbtWnrqqaeotLRU8aWyspIuvvhi6t27t/L78ePH0wcffNDMzyeffJLOPvvs+GsvvfQSXXLJJfGfb7nlFrrhhhuSzk21L34/bNgwpY3qi/j/e++9l3Jzc5XXtXZbs5nJdmIs8VDnr85HzEU753vuuYduv/12pa3Ka9GiRSRe1/LO2gLAwCCQZQKyLE9l5eXl/MEHH8yyKxgeBLJDQBUvIbKqIAqhOPbYYxXhGD58uCLIWoERIvL666/TvHnzqF+/foqoaH/WirhWUNUZijFfeOGFuBCp7YUPl156aVyEV61aRaNGjSLx/uzYsaPy/2L7Siv+wmam24n5HnnkkQoTdWxx36P2IkG02bhxozKXN954Q5mD4FVWVqbwPPfcc3eZR3ZWAEYFgewRgAhnjz1GtggBVUROO+20eBYnRDJRNLQirPYRgrj//vu3KI7JppiYNWoFWLTXirDWj549eypZeWKmrGbLqr9mtxMZ+5QpU5RnRUWFMnchwOKhirA6p5aEVgi0uNBBNmyRNwHcyBoBVEdnDT0GtgqBxC1psQ2sFTvx+8RMWCvCYh6qAIqsuK2HNmsVwi4Ea/bs2YqYiW1vsQWuZs+JYtWSeGWynRDep59+mm6++WZav349vfvuu3T88ccr/qsXMtoLG3U7OnGnQVzAqDsJbTHD70HAqQRQmOXUyGJeKRHQbkknbvsmO+/Ubj9/++23KYmwutWtFSXhbLIt7EyKq3oeLnxpbdwVK1bQp59+2uzsN3E3Qf354IMP3mU7WlyotMQgpaChMQg4gABE2AFBxBTaT6C1zDZxu1gdTRVR7Zaxnkw42Rm0nURYZO3qebDKoiURVs+vtWfs4jw78ef2RxAWQMCeBFAdbc+4wWuDCahb0rW1tYrloqKi+JZwS5W/iQKUrGAqmZupZMJWOxOeOnUqTZ8+nS666CKlIK0lEU48E9Ze5GhFOHE3wOCwwhwIWJ4ACrMsHyI4mCkC2lt8tLcftSXC6vat3uroREFS55dsO1p7fjxgwIB4VfEpp5zS7NxanM2qVdRmthNFaHfeeSc98MAD8du5hP/Jitu0W9rvv/9+sy17cSGCM+FMrWyMY2UCEGErRwe+ZZSAKiRiUG3BkB4RFn0S7xPWVjlrJ9KSvZZua1IzZ2FDrT5Odk9xJtqJMRLPg1sSYdXHJ554Qpm+NutFdXRGlzYGszABVEdbODhwzbkEhGAvXLiw2YdyOHe2zWemivPhhx+O+4TdEnTMs0UCKMzC4gCBLBBI9olZWXAjK0PiE7Oygh2DWpQARNiigYFbIAACIAACzieA6mjnxxgzBAEQAAEQsCgBFGZZNDBwCwRAAARAwPkEIMLOjzFmCAIgAAIgYFECqI62aGDgFgiAAAiAgPMJoDDL+THGDEEABEAABCxKQBHhG2+88bft27f3ET7uu+++n4waNepT8f/z5s078vvvvz8Kr4MD1gPeF/g7YN2/A/vss8+nF1xwwSftfZ/CTut6ZxYfVl5ezmfPns0seqEAt0AABEAABEDAsQQgwo4NLSYGAiAAAiBgZQLl5eXzhAhPmT179hQrOwrfQAAEQAAEQMBpBMRONLahnRZVzAcEQAAEQMAWBCDCtggTnAQBEAABEHAigbFjx56P7WgnRhZzAgEQAAEQsAUBFGbZIkxwEgRAAARAwIkEIMJOjCrmBAIgAAIgYHkCqI62fIjgIAiAAAiAgFMJoDDLqZHFvEAABEAABCxPACJs+RDBQRAAARAAAacSQHW0UyOLeYEACIAACNiCAAqzbBEmOAkCIAACIOBEAhBhJ0YVcwIBEAABELA8AVOqo2+Zvei3qvqg8tWIeIAACKRHoKQgZ83t5cN2T6/3rr0eWHDdb/WharwvjQIKO64kUBAoXnPNiPsMe1+aUph1+QMf8yvP/YMrA4RJg4BRBB5+4TN65JqjDfts92lvlvMzDrrSKPdgBwRcSeDVrx+mW0827qt/IcKuXEaYtB0IQITtECX46DYCRouwKdXRyITdtiwxXzMIQITNoAqbINA+AkaLsPDG8MIsiHD7gozeICAIQISxDkDAegQgwtaLCTwCAVMIQIRNwQqjINAuAkaLsCnV0ciE2xVjdAYBhQBEGAsBBKxHwAQR5oZVX6q4IMLWWzjwyH4EIML2ixk8dj4BiLDOGD/6wB300H1TmrX+w9EjaMbMeVRcUtaild9Wr6CH759Gt9398C7tvv3qC3r9ledo4o130Iy7bqbTzjyf9j/4MJ0eESX69OIb/9dm/9b80T2wpmF1VQVNnXwlXXntrbT7ngOSmhB+DjvimGa+idd2670HnXLGufE+6nwGDtmbHpr9z1btiVi01U4Y1jPf1sZVfRe2/nrKH+O+JmMtWEwcP4omXH2zMlcR30Wff0QTrrk5HbSG93GKCFdXVdN146+nhR8vbMboiusup3HXjNuF22+r19DM+x+lm+6+iYpLilPm+vgDj1PP3j3pz2f8OaW+YtyJ5RNpxc8rlH4jLxhJ10+7nnJyAi3aCQZDdO+t99IpZ55M+x28X0rjtdS4Lf//8+p/lK7a+YnX1q9d34yndj4tsd7xnvvfvFtqp87z5WdfbpNNa/a+++o7+vLzL+mi8Rcr3NqyJ+b13y+/VeKwacMmeu35V2nCdZe3GhNDgtCKEaNF2LHV0eKPsXho/6C+8eoL9PvaX1v9I6tHhG+cNoNycnJTirXwZ8vmjaT2FeNcVX4OTbn7kVaFWI8opeJIWyKcTIhU0Zv+6LNxERYsv/nyc2U+S5d8R48+eEfSCxy97VQBFkw6de7a4sVSa/bE3B64+xa69LJr6InHHqBrJt+uXEiJOSXzT52XVqCTXYCkwtfItk4T4cuuHhcXKjPES2Xflogli5EqHLfcfXPcR2Fny+atrQqxGfNozX/hZ6IQCaG6fsINpBVQ9cJHMB+092BF8A44ZP9dLkz0ttMKvzrndOyJuR1yxCG04fcN8QuJluypMdnngH3iMUh2AWLke06PLaNFWIzpyOroZCLcUiarFSYBRGTCe+93EN1926Rm2Vtr/UVG9dnHCyhZth0MNtFdt06kAw85YpdMUox36fiJyu/VzDoVf+Y9+aiybt56/aVmvqpjvvjsbOX3QmgG772fMo54LVlWKvo8fN9UOuu8i5WsVrXRpWt3xYY2E9ZmxokZpXYh620n2E6ZfDldee0UZS7JdiKE3dbsiQuW+c8/RVded1uzi6Rk/qmx3PD7mngmrF4IJLOh581pdBsni7BgpYrNkH2H0l033aXgY4zR5ddOoHmz59Go8lHKv2pGLATjzsl30vhrJ1C3Ht2SZlIfvPW+Ikjice+j9yiiI7Kv808ZpbzWUnYr2jz24ON038x749m3EAHh14133kjVFVX0xitvNhMDkXmqGd3gvQbRP59+Ucmi1XHVjL6gqDCe8T33xry4yCfzK5n/2nWlipiadasXCmL8im0V8Uw4cTdBm1FqM3u97RLXdjr2lPfvfY/Q6eedQbvv2fyD2xLtCWEWbcWjvr4hzl2sgYfufpiumnxlWrskRrxHIcI6KSYTYfW1tkRPZGPHnXS6kjEnZl6J29GqsKkC2lK2LV6fNOECuuq6Kbtk4qrYtSTCrfkjtly1AisEU/itnb8qcGLLuKS0Y4vb0S2JWKL4Jfrb0kWG3nbakLaW+bdlTzAWD+2WuSqst9/0N7rlzr8rFxfqRc6oSyYoGbK6HS3aJl6I6FxupjRzsghrM7DishJlG1jNQlVhmHTbJHr8wVnxrV4hWqoQPj3zKYW52M7W2hLipM0ktUKqCneXrp132QZXbWzfup1mzJ6xi0hoxxYipm7/qiIsMjsh4FWV1XHhFv6JeV0y/mLlYkCbWYutVVXgE/1qKRNuTYASt6MT/U12kSH809sucYELH1X+2t+1Zk+waWk7OdGeOh9xrKBuR6sXD4kXIqa8+VoxarQIO7Y6OtmZ8F8vKFe2T8Wjtcwz2R9scYZaVVGxy5lwSVlZi2fIiXFUMzKRMYuHKshtiXBr/mi3WdULgPMuvqzZWafW/h79BrQowq2dibaWgbYkwokZaEvt9Ipwa/ZGnPSXZlm8ajPZmKpY//GY45pxUvtYZUvaaSKceCaszRhVQRIZkjY7e/GpF+N/7FsSp8QtYW27xAwrUSQS36Pq1q54fcCQAXFBbkuEtVuziRm+yKTFvLQ2RMarFZfEC4xkZ9rJtqJV/xNFONm8EzN90Vdvu0ShTWarLXuff/S5YibxrD7xAkF7sSH6JIpwtrekTRBhZ1ZHJ8uEE/8wt7b9q26HareGk4mwsNnSeWhrV2hacRAC0tZ2dGv+qOfMiSKsir3qhzjTFcLTUmFWa2fmWhFuKyNtiXN7Rbi1ccW8xHmweg4sfNBup6u1AdpsP9jUCBHOQBqRmKkmDpm4Jar9+bdVvynZ77irx9L0qdOVrWhVqLVFVMKmutWbKMLq9rQ67uFHH95s27klBFpxUP1QC7USM2FtYZZWhLUFZoki3JJf4sIjmQi3dgGRqUxY+HD75DuS7hYIjq1lwmJe4jxYW8CWzJ4200227Q0R1vGmtcItSqmIsPjDrGabYnrazFP7u3QzYbVgSCsQYhxV9BK3x1P1J5kItyS0rRVm6c2ElQsPTbW0EWfC6rJqqxCtpXFFf21ls+rTqWee32x7Wj0WSFzGVizOclomrC3Mar770bwaWivCop04Bz7htBOUP/CiMlY8tIVGbWXCiVXDyf6EJfvDrj2DTjwTVrdP1e1oNRPWFhmJs+7WRLglv1rK+FPJhPWe9eptp2a54oJIe27e1gWVKqLjrh5Hjz/4eLOzXPG7RHstVdJrz/KdJsKuqo5OzNDU81Pxh3nuzOnKbTbiIc5gR4+fpPzxbutMWGzvam9z0bbXVlAnXhRoRULNhNP1J1GEE8+EtZXYrW1H6z0TVi8gjK6OFnbbEuGWqqOff+qx+G1VejJuMVayiwecCeu4yk6xSXsyYXGLkhClf9z3SLzgKbGaVi1wSpYJa8+ERQbdUsVzYrtE0RGZsJoBlpQWK7dc7X/QfvHCLNFevY1G3VoXr7Ukwtoz4US/xHl3skw4lTNhvVXPetu1dKacuBRastdjtx7KrUnqLWl67SXLhJ12JiwYuqY6uvnV945bhJb/vIQmT51OS777Wrl3Vjy01dHaaueWqqNVkRO2WrsXOfGcWnvLj9ZGqv4kE+HE6mh1LPX17/+7eJd7e1sTIL33CSfLtJPd19tSRp4ownrsdevRq9l5sJalNuaJ9wonE+HWLkRS1J52N0cmvOM+4WRbltrKYnFrjniowqWe6yarjm5tKzrxPuHEturFgHj9iKMOp8aGxqTV0erFQGKWmWyrVq3a1o6V6L92IbUkQKncJ5yYabd0X6+2nTp3rS9qdpp40ZDMXmL22po9bfV2ogijOlrnnxUrbEfrdBXNEghY7QMrMh0gqxRlKReD+D7hTIff8uO1tiVteecNcDDbW9FiCiYUZs0TmfCU2bNnN/94qXYAgwi3A54FulpJiDKJw2oXIBDhTEbfPmNZQYiyQcsqFyAmiLAzq6OzsUgwJggYSQAibCRN2AIBYwhAhI3hCCsgYHkCEGHLhwgOupCA0SLs2OpoF64NTNlhBCDCDgsopuMIAkaLsIDiyOpoR0Qbk3A1AYiwq8OPyVuUAETYooGBWyBgNAGIsNFEYQ8E2k/AaBF27GdHtx81LIBAdglAhLPLH6ODQDICJoiw8dXRk/7xf1XBSCz1b+NGzEEABOIEcnye6ulX/LHEKCT3vH1FVTgWwvvSKKCw40oCfk+g+oYT/2HY+7K8vNx4ERb3CT9yzdHMlRHCpEHAIAJGv4+mvVnObz15Nt6XBsUHZtxJwOj3kWnV0RBhdy5QzNo4AhBh41jCEggYRcBoERZ+mVIdDRE2KuSw41YCEGG3Rh7ztjIBiLCVowPfQMBAAhBhA2HCFAgYRMBoETatOhqZsEERhxnXEoAIuzb0mLiFCZggwijMsnC84ZqLCUCEXRx8TN2yBCDClg0NHAMBYwlAhI3lCWsgYAQBo0UY1dFGRAU2QMAEAhBhE6DCJAi0k4DRIizcQXV0O4OC7iBgBgGIsBlUYRME2kcAItw+fugNArYhABG2TajgqIsIGC3CqI520eLBVO1FACJsr3jBW3cQMEGEUR3tjqWDWdqNAETYbhGDv24gABF2Q5QxRxAgIogwlgEIWI+A0SKM6mjrxRgegYBCACKMhQAC1iNgtAiLGbqqOnrZO2cNk6ScccRoeCwa7kLEJeuFGR6ZS4DJHq9/C3F6X5aDjw86Yf4ic8dLzzpEOD1u6AUCZhKACLeD7or3Rj1DknR6WY+DCwpK9yR/bikxBg1uB1JbduVcpnBTJdVXrqaKDV/Vkyy/NuC4eRdabTIQYatFBP6AAJHRIuya6ugVCy5aXFi6x9Cu/Y7Ph/DiraQSEIK8edW7DXWVv/40YMTTh1qJDETYStGALyCwg4AJIuz86miRAReW9TujW/8T87GQQCAZgU0r326oq1j1qpUyYogw1ioIWI8ARDjFmChnwN68Bf0OnlCADDhFeC5qLjLiVV89Wi9HG0dY5YwYIuyiBYip2oaA0SLs+OpokQWX7XboBWU9D7FNkOFodghUrP+SKn5f/KxVsmGIcHbWAUYFgdYIGC3CYixHV0evWDBqY++9z+sWyOuIlQUCrRIINW6ntUue3zRgxLzuVkAFEbZCFOADCDQnABFOcUUsffvs2MDDJ0rYik4RnAubiy3p5QtnyINPfMljhelDhK0QBfgAAuaKsOOro5e+PZIPOuI6rCMQ0EVg2ef30eATX2a6GpvcCCJsMmCYB4E0CBidCZeXlzu7OhoinMYqc3EXiLCLg4+pg4AOAhBhHZC0TSDCKQJzeXOIsMsXAKYPAm0QMFqEHV8dDRHGeyoVAhDhVGihLQi4j4DRIiwIOro6GiLsvjdJe2YMEW4PPfQFAecTgAinGGOIcIrAXN4cIuzyBYDpg0CGt6NRHY0lBwIaAhBhLAcQAIHWCBidCaM6GusNBCDCWAMgAAI6CUCEdYJSm2E7OkVgLm+OTNjlCwDTB4EMb0ejOhpLDgSQCWMNgAAI6CRgdCYshkV1tE74aOZ8AsiEnR9jzBAE2kMAIpwiPWxHpwjM5c0hwi5fAJg+CGR4OxrV0Rleck1NIbp68gxl1Afvnki5uQF6/uV36PzRt9DYS05v9tr9D82jl56+mwb0653UyxWr1tLZF02ma68aReeNPKHNmahjz3ryNaWtdrw2O7ukAUTYJYHGNEEgTQJGZ8JOqI6eSESziaguGVMrZsK33zuXFi7+gZ5/4g4qK+1A4udb73yc9tmrf1x0E9skm1uqIizEft4/31bGXb5yDR0x4lJ6bu7tugQ8zfVqu24QYduFDA6DQEYJQIR3xd1EROKr50R6eVeiGFtRhNXM9/MFT9DA/n3ovEtvpvc+XKTMTPva4YfuQ7dcP5oqKmt2aSN+p4rwiGMOpQUfLaYfflzZanarir0YQ/TXPhKzZFWc1ddrauuV5stWrKEjj9ifVqxcG7+IEPNRs/ZePbsqmb6abbdmp7UsP6PvKs1gEOFskce4IGAPAkaLsBOqo68ionuISCIiLnZ5tWJsRRHWZrB9enVXMtLX/zmDHpv7iiKOI08fHt9mPv3kY5ptX7/25kdxwRNLVmxHH3rQUGUb+9sflrea3aoiLPolZsDazFvNkoVY77/PQGX8xV//FM/SRRY/YeK9ys+q6AqbwofpD8+LZ/lt2bHiWw4ibMWowCcQsA4Bo0VYzMwJ1dEVRFS6M0xhrRgvfXtkrdW+T1jNbIXg7rF7D2WLeO4jt9Ad989VpnDGqX+iEadOULLijmXFzc59VQF/dMb1u/wu2XmzdukmZtTH/WmYks2Kh8jGEzPvUeecSIkXAeIMW7Ujfn/gfoPj/h1/7GEp2bHO2+p/nkCErRgV+AQC1iHgBhE+i4hOJKIDiEhUJBWKC4U0QhAhojeWvj3yDKuJcOIWb4eiAiWLVLNcsb285KdVzc5uE+cvMlmtAIrCrLZEWLWhzYin3TQunnmL7WztQ/xu0pWjdikkE22EjQ2btiqZ8sy5ryhZsZqZp2Injbia2gUibCpeGAcB2xMwWoStVB19ChGJv+QbiehVIlpIRKuJqFFH1LYTUZldMmHhp3ouLP5f3RoW27xia1o81Mrldes3t1gBnViYpVeEhX01m+3Tuxvdct1ounTC7fFMWMu7JZvqlnSXTqW0e5/uykVEY1OwWSasx46O2Ga0CUQ4o7gxGAjYjoAJIszTyTJbBXf5Ax/zR645OhW744noZiIaJ7LXFKMizoSFeIviLFucCYv5aQVXLZTSbheLLFQUZSWKYLIz4a6dy9qseNaKbjLBbOtMWPis3lKlFXFRUKY9X07VToqxNr05RNh0xBgABGxNwIki/CcieomIjiSin9OIju2qo8Uc1SxWFVBxq5K2QllbwZxKdbQq3sk4qmOq28Xa+4Tbqo5OFGHxsxDcV9/4qNm9zOnYSSPmpnWBCJuGFoZBwBEEjBZhK1RHi23nmWKHNs0I2e4+4TTniW4ZIAARzgBkDAECNiZgtAgLFNmsjj5m5/29+5kVEyveomTWXGG3/QQgwu1nCAsg4GQCThPh+4moVuxsmhU0iLBZZJ1pFyLszLhiViBgFAGjRTjb1dGfEtFtRPSJUYAS7UCEzSLrTLsQYWfGFbMCAaMImCDCWa2O3kBE+xPRFqMAQYTNIukOuxBhd8QZswSBdAk4SYTFLUxBIgqkC0NPP2TCeiihjUoAIoy1AAIg0BoBo0U4m9XRQnyFCKdyP3HKqwMinDIyV3eACLs6/Jg8CLRJwGgRFgNmszpafLgGRLjNsKNBpghAhDNFGuOAgD0JQIRTjBsy4RSBubw5RNjlCwDTB4E2CBgtwtmujkYmjCVvKQIQYUuFA86AgOUImCDCWa2Ohghbbom52yGIsLvjj9mDQFsEIMJtEUr4PbajUwTm8uYQYZcvAEwfBDK8HZ3N6mgxVWTCWPKWIgARtlQ44AwIWI6A0ZmwmCCqoy0XZjiULQIQ4WyRx7ggYA8CEOEU47T07bNjAw+fKDEmpdgTzd1GgHOZli+cIQ8+8SXx3dRZf6Txvdyt+mzGH4+sQ4IDIJBhAka/jxxfHb1iwaiNvfc+r1sgr2OGQ4Xh7EYg1Lid1i55ftOAEfO6W8F3iLAVogAfQKA5ARNE2NnV0SveG/VM2W6HXlDW8xCsJRBolUDF+i+p4vfFzw44bt6FVkAFEbZCFOADCECE27UGlr1z1jDJm7eg38ETCrAl3S6Uju4stqJXffVovRxtHDHohPmLrDBZiLAVogAfQMBcEXZ8dbTAJ7LhwrJ+Z3Trf2I+FhQIJCOwaeXbDXUVq161ShYsfIQIY62CgPUIGL0dLWbo6OpoNYQrFly0uLB0j6Fd+x2fj4zYegs7Wx6JDHjzqncb6ip//WnAiKcPzZYfycaFCFspGvAFBHYQgAi3YyWIjJgk6fSyHgcXFJTuSf7cUoIgtwOoTbsK4Q03VVJ95Wqq2PBVPcnya1bKgFWsEGGbLjC47WgCRouw46ujE1eDckYs5YwjRsNj0XAXIo57lxz9lkk2OSZ7vP4txOl9WQ4+bpUz4ERPIcKuW5iYsA0ImCDCzq6OtkFM4SIIJCUAEcbCAAHrEYAIWy8m8AgETCEAETYFK4yCQLsIGC3CrqiObhdxdAaBLBGACGcJPIYFgVYIGC3CYihXVEdjVYGA3QhAhO0WMfjrBgIQYTdEGXMEAdwnjDUAApYkYLQIu6462pJRhVMgkIQAMmEsCxCwHgETRBjV0dYLMzwCAXxiFtYACFiRAETYilGBTyBgAgFkwiZAhUkQaCcBo0UY1dHtDAi6g4BZBCDCZpGFXRBIn4DRIiw8QXV0+vFATxAwjQBE2DS0MAwCaROACKeNDh1BwF4EIML2ihe8dQcBo0UY1dHuWDeYpQ0JQIRtGDS47HgCJogwqqMdv2owQVsSgAjbMmxw2uEEIMIODzCmBwIqAYgw1gIIWI+A0SKM6mjrxRgegYBCACKMhQAC1iNgtAiLGaI62npxhkcgABHGGgABCxKACFswKHAJBMwggEzYDKqwCQLtI2C0CKM6un3xQG8QMI0ARNg0tDAMAmkTMEGEUR2ddjTQEQRMJAARNhEuTINAmgQgwmmCQzcQsBsBiLDdIgZ/3UDAaBFGdbQbVg3maEsCEGFbhg1OO5yA0SIscKE62uGLBtOzJwGIsD3jBq+dTQAi7Oz4YnYgECcAEcZiAAHrETBahFEdbb0YwyMQUAhAhLEQQMB6BEwQYVRHWy/M8AgEIMJYAyBgRQIQYStGBT6BgAkEkAmbABUmQaCdBIwWYVRHtzPnjj62AAAgAElEQVQg6A4CZhGACJtFFnZBIH0CRouw8ATV0enHAz1BwDQCEGHT0MIwCKRNACKcNjp0BAF7EYAI2yte8NYdBIwWYVRHu2PdYJY2JAARtmHQ4LLjCZggwqiOdvyqwQRtSQAibMuwwWmHE4AIOzzAmB4IqAQgwlgLIGA9AkaLMKqjrRdjeAQCCgGIMBYCCFiPgNEiLGaI6mjrxRkegQBEGGsABCxIACJswaDAJRAwgwAyYTOowiYItI+A0SKM6uj2xQO9QcA0AhBh09DCMAikTcAEEUZ1dNrRQEcQMJEARNhEuDANAmkSgAinCQ7dQMBuBCDCdosY/HUDAaNFGNXRblg1mKMtCUCEbRk2OO1wAkaLsMCF6miHLxpMz54EIML2jBu8djYBiLCz44vZgUCcAEQYiwEErEfAaBFGdbT1YgyPQEAhABHGQgAB6xEwQYRRHW29MMMjEIAIYw2AgBUJQIStGBX4BAImEEAmbAJUmASBdhIwWoRRHd3OgKA7CJhFACJsFlnYBYH0CRgtwsITVEenHw/0BAHTCECETUMLwyCQNgGIcNro0BEE7EUAImyveMFbdxAwWoRRHe2OdYNZ2pAARNiGQYPLjidgggijOtrxqwYTtCUBiLAtwwanHU4AIuzwAGN6IKASgAhbdy1wztnM6+Z3icVCXXySp0yW5U7EpDJGvJQTK/ZIUpnkkUoZ8WLOWBFxyufEc4hTgDj3c859ROThnDycuIdxxjj9LyFixDgxkolIZoxixFiUiCKMsTBjFGLEmohRPedUx7lczTmvkGO8kohXE0mVxOUKTrSdSayCM+/WCfeP3EJE3LpE7eOZ0SKM6mj7xB6euowARDh7AX/qoqdyGkoCezIP7cE49WFEvb0+b39i1EeWeTc5JpdIXhbx+/0Rf66PB3L93J/j9wRyfF5fjt/vD3glr89DXp+XPOJfr4ckr0Qej0SS+pQYMcaI7fy32Ww5EedcecoyJy7Lyr9yTKZYVDxjyjMqnuEYRSNRioSj0VBTOBIJRiLhYEQOByMs1BRm4VDEJ8dkv+SRKpnENvFYbE0syn9hEl/LiP0meehXX25o9cVTLg5mj7h9RjZahMXMUR1tn/jDUxcRgAhnJtiPTXp2KI9JexOThkoeaR8msaGxaKxXINdfnVeUKxcU5XrziwsK8goCUm5BDuXkBSgnP5AZ5wwahXOiUGOIgo0haqoPUkN9MNxQ3djQUN0Qbahr8kaC0WLJw37nMv9RlvkS4vJPXr/0Q/m95/5skAuOMQMRdkwoMREQaJ0ARNj4FfLIhGfKWK7vMMbZoZKH/YFzOsDn94SLSgqCxV065HYoK+hQWJxP+R3yjB/c4hYbahqprrqRarbVVFdtqw3WVTXkRMNRH2PSN9Fo7HOJpMWxQGjR5XdfWGHxqZjqntEijOpoU8MF4yCQPgGIcPrstD1nTnphb5L5CV6/97RoJHZoYUn+po49Sr2de5Z1KulcRB6vx5iBHGglFpOpaksNbf29YvO29ZWx+tqGbl6vd3EkEv03SXzBhPvP+96B0251SiaIMKqj3baIMF97EIAIpx+nmTc8X8KidJ7H5xvDOd+ja++ODT327NqlU4/S9I2ip0Jg2/pKWr96y6ata7cVyEQr5Wjsmajf++KVd4/c5gZEEGE3RBlzBAF8i1Jaa+CxSc925txzheTxTOzYvaRx98E9yzpCeNNiqafT9o1V8uof1m6s3FpTHJNjM8LR8N+v/vvF1Xr62rWN0SKM6mi7rgT47XgCyIRTC/Hjk148lTP+UJfdyqShwwbsFsjzp2YArdMm0NQQop++WLGpYlNVU1Smyybc/9cFaRuzeEejRVhMF9XRFg863HMnAYiw/rg/OumFkxnR6wcN31vq3LNMf0e0NJTApjVb6buPl8ZkWR4+4YHzPjbUuEWMQYQtEgi4AQJmE4AI6yc858b5y/Y+YsDArr076e+ElqYQ+H3lpqafFq38etx9fz3SlAGybNRoEXZddfQ7Z/1lmC/gH0ecDY+GQ12IcynLMcXwmSbAmOz1B7YQ4+9HQuHHT5j/r0WZdkHPeBBhPZR2tJk58QV+0iVH6++AlqYS+Pajnz75yxXDHRkQE0TYPdXRH5x/9jOMSafvduiwgrK+/SivrIyYBA029d1oQePi04caKyqo4pdV9PviRfWcy68d+9xLF1rNVYiw/ogIET7gT0MJmbB+Zma13Lx2G/33w59o/IxzmVljZNMuRDhN+h+OOmdxWd++QwecdHI+hDdNiA7sJgR5xVtvNlT88stPf5r3z0OtNEWIsP5oCBEWH/944LF7Ec6E9XMzuuXW9RX0zQc/Epc5RFgnXFdUR4sMuGO//mcMPPnUfJ1c0MxlBJa/+e+G7atWvmqljBgirH8RChE+8E970bKvf6HSrsU0YP89CNXR+vm1t2WoMUwrvv2VKjdX06CD+tI3H/4IEU4BqqOro8UZsD8nZ8FhV11dgAw4hVXhsqYiI/7ioQfrw8HgCKucEUOE9S9C9Uw41BSmNcs20NplG6hj9xLq1b8b4T5h/RxTbbl9QyWtW7mJtm+sot6DelCfQT0okOunt578GCKcAkxHi7DIgnsNO/yCXsMOSwEJmrqRwLpFX9C6RQuftUo2DBHWvwoTC7Mi4Sht+GUzbfxtKzXWNSlnxV16dSR8YpZ+pi213Lahkras207i7DevMJe6796ZevTtSj6/N94FIqyfs+Oroz84768b97vgwm75nXDrgv5l4c6WDdu20XfPPrPp2Odf7G4FAhBh/VForTq6trJe+ajF7RvFs4rKuhUrW9alXYoJnx3dOmPxdYlVW2upcku1stVcsala2WHo2L2UOvUspaLSgqQGIML61255ebmzq6PfPesvsSOvnyxhK1r/onBrS7El/em9d8vHz/+XJT7RHyKsfyXqvUUpEopQ5ZYaqt5Wu+O5vY78OT7qUFpAheJZkk/u/halBqqraqC6ynqqqayncDBCxR0LqbhTkfIs7dKBfAFfm4GBCLeJKN7A+SJ85mn8qBtv1k8ELV1N4JO77qDjX3ndErdWQIT1L0W9IpzMoiI6VfU7xKeqgeprGkl8rV9+US7lFeVRXmEO5RXkkPgu4dz8HOW7hO32fcJi3sGGkPJsaggq3yncKJ51QWqsbaSG2ibl6xsLOuTtuBBRnjsuStJ5QIT1U3N8dfS7EGH9qwEtCSJsz0XQHhFONmM5JivCJM6ThWApz50iFmwMkXiKM9BAjp/8uT7yi38DPvIFvEqmKH7n9XnI6/OSR/zr9ZDklcjjkUhSnxIjxhiJW6vEv4kPzrlyq4/4V5Y5CZ/EU3y9oByVKRqNUSwSo2gkStFIjMQ5uMj0I6EohUMRCgfDFG6KUCgYVn6XkxfY8cwPUK547rywEOe64oJD+GXUAyKcGklHF2ZBhFNbDG5vDRG25wowWoT1UBCV2OIphE9s24pnXAjDO4RRCKQQylhUJnG+qgioeMqyIrBCXIXIkhBc/r9RFU0WAs0YSUKkJfHvDgEXQi6+A9kjRH2n0AvBF8KvXgCILXbxFD+LamXxzOQDIpwabYhwarzQ2sEEIML2DG42RNiepDLjNURYP2fHV0cjE9a/GNCSsB1t00UAEbZW4CDC+uOBwiz9rNDSBQSQCdszyBBha8UNIqw/HhBh/azQ0gUEIML2DDJE2Fpxgwjrjweqo/WzQksXEIAI2zPIEGFrxQ0inFo8UJiVGi+0djABiLA9gwsRtlbcIMKpxQMinBovtHYwAYiwPYMLEbZW3CDC+uOB6mj9rNDSBQQgwvYMMkTYWnGDCOuPBwqz9LNCSxcQgAjbM8gQYWvFDSKsPx4QYf2s0mq5cs1aOv+GyXTwXkPp/kkTKTcQIPW1qy8YReeceELc7j/ffocuvvkWGn3G6fG26mvJBv/4ySdo2L777PKrxD7Dhw2jZ+66g0o7dGhzDsK3dxcupCvPO7fNtk5sABG2Z1QhwtaKG0RYfzxQHa2fVVotVcFdsnIlqaKZTISbQiG6dvoMmvvqa7R3//703D13U/8+veNjVtbU0IU33ky9u3eLC3Qyh+6aM5cWff9DXHRVu2s3bmpTiNUxhLDfOGZ0WvO1e6c2RLiQiMqJaEYm5okvcNBPGSKsn1UmWkKEU6OMwqzUeKXUWivCaka6vapayY61mbDa7thhh9IHixY3+50YUI8IC/E9+pJL42LfkqNan0Sbp+64nU770zHxiwDxmpqNf79suWJTPFT/V/y2ptk4QvinPfZ4fFzthcB7C79QsnvxUC8uKqqrm/W3kvi3IMJCfG8koolEFCOi3JQWQZqNIcL6wUGE9bPKREuIcGqUIcKp8UqptSp4A/r0ofkLFiiCd8DgwbuIsNhCfvDZeTRn6hSa88oryhjq9rVeEU7MgpM5qmbG5510krKVLfq8/uFHSubdsaRYybbVTFibsasiLWxOHjOaxk29XWknLiTUDF4r5t07d6Yzhw+nO2bNor/fcL3iiprJa/uLjFvvxUNK4NNsnCDCqvheLT5Of6cATyaih9I0n1I3iLB+XBBh/awy0RIirJ8yqqP1s0qrpSpkY0eeSd8tW05iW1gIz1X33BvPdlVhVIVXiKIQZO2WtJ5MOFGEE8+GtWfI2mxYzVATRVi9MFD9ED+/8Nbbyrb24y/Pp41bt9Lk0aNp3LTb6f1Fi5TsecyZZ9KY26bQQzdcHz+v1vqhZthifuq2ubCl3UJPC7RBnXaKcNHOzFcVX/UraCqIqKNBQ7VpBiLcJqJ4A4iwflaZaAkR1k8ZhVn6WaXVUptNqhlw57JS2lpRGRfhxDPiZGfGekQ4UTRVh7WZ5oDd+ygZ6ZaKCkXk/7t0aVzwE0VY3WbWTlwVbLWfuLiY9fIrJP59/cOPafhhw+i5N/+j2Fa3nYXwTrt8At36yKPxDF9sc4sLESHWYhyrnEPvFOFXiegUIvIlCfpnRPTHna/fRkRTdv7/VM3/G/L6wcddxL9672nVBcPtE5EhflrBzknDzqCZcx9J6z2KTsYTgAjrZwoR1s8qrZaJgqoVNrF9K6qjk4mdGExb1axHhFva1tW+Luxqz421wt1WJqwFoN1m71BYEM+ARQFasmw3NydH2bZWs/2mYFC5GNirfz/lDFybOacF2qBObWTClURUZtBQbZpBJtwmImTC+hFltCVEWD9uVEfrZ5VWy5ayXCFWQoSPO/ywpFXP6hauuoWsR4SFg9ozXlFdnVidXVZcHD+PVsdWs2K9Z8LirFo81LPgWy8bt8vZsLi40Aq8NitWz7rVi49UbqFKKwgpdMKZcAqwLNQU29EWCgYRQYRTiwcKs1LjlVLrZFvLqsAKEe7TvbuSmapZsWpc7ScKosQZsl4RFv2T3Vusta/NvM8aMUIpGFPFPlEY1UroxMxcO05i38QLB3FeLLaxxTY8Ixa/VUrN0IWIW+WWKFRHp7S8LdMYImyZUCiOQIRTiwdEODVeaG0QAStVRatTwn3CBgU3w2bMFuGHH3+QZvzjvmazOm/kKLr1+mmUk5PT5my/+e5rWr/hdzrtz6e32DYYDNK0e29Vfq/XbpsDZ6kBRFg/eFRH62eFlgYRULN6kSFbKQsW08MnZhkU5AybyYQIf/PtV/TQfTOppLiEqqqr6KrrxlPPHru1KZi//raaxk8cS+MuGQ8RzvC6MGO4aW+W81tPni1uWTTkgcIsQzDCiFMIQITtGclMi7CgJLLbM84/hV597g06cL+D6PX/vEZXXT9BAThowBCaOWMWlZSUKmL96cJPlNcnXnEdXTnuatJm1kcefpQi7rk5uUomXFdfp7R94+3X43b22H1P5bVk/cRFgSr0y1b8rLRTfdL6Kf5fHUv0MfOBTFg/XYiwflZo6QICEGF7BjkbIqzNcPcesg89OHM6TbvpLgWgNkveuGlDs0xYiPdrb8xXMmj1dyeOOInKL7pMEeFvf/i2mYCr2fZPy35stZ8YV9ic/fRjpGbtVVWV8bGPP/bEjG13Q4T1v49QHa2fFVq6gABE2J5BzrYIq2e92mxYPTNOFGGVsDarFRmyKsKqmIqzZmHv8SdnKqKcLBvW9nv+5XmUeE6d2F/8LC4A1G11s6INEU6NLAqzUuOF1g4mABG2Z3CzLcIiWxVb00IEr71qMt3/0N0KSG22q54Jq0ItBHTUXy9SsuYD9z+4TRFe8vMPynZ3Yj+xva1ujavRU8VYZMWJBWXqVrkq6mZEHCKcGlWIcGq80NrBBCDC9gxuNkRYeyb8xZefx7eA1bPdZCKcuCXcFGzSJcIP3v0wzXtxx6enCWHX9hMirD7UgjFxBv3QvTs+oS4xk85EhCHC+imjOlo/K7R0AQGIsD2DnGkRTryd6N0P3o6LXWV1ZTwrTpYJi21o9cz2088/jme36na02FYWhVV77t632dmy9qxX20+bTWuzYmGjtLgUZ8IGL2lUR6cI9N0zT+NH3Xhzir3Q3K0EIML2jHwmRLi1+4S1GajY7u1U1pEYY82qntUzWyGaV0++kkQls9p2t5696Lq/3Uj3/f2uZtXR2mpmbQW0tp9W6NXqaLUKW0RTu1WN6uj2r2+IcIoMIcIpAnN5c4iwPReA2SJsTyrZ8xrb0frZozpaPyu0dAEBiLA9gwwRtlbcIMKpxQOFWanxQmsHE4AI2zO4EGFrxQ0inFo8IMKp8UJrBxOACNszuBBha8UNIqw/HqiO1s8KLV1AACJszyBDhK0VN4iw/ng4/2Mrz/pL7MjrJ0tMkvRTQUtXEuCyTJ/ee7d8/Px/eawA4PIHPuaPXHO0YR8Ub3RVpxUYqT5AhK0UDXyVYSrRcLwIf3DeXzfud8GF3fI7dUqFC9q6kEDDtm303bPPbDr2+Re7W2H6EGH9UYAI62eViZbIhPVTdnx19Afnn/1Mr2GHX9Br2GH6qaClKwmsW/QFrVu08Nljn3vpQisAgAjrjwJEWD+rTLSECKdG2dGFWe+c9Zdh/pycBYdddXUBtqRTWxhuai22or946MH6cDA44oT5/1pkhblDhPVHASKsn1UmWkKEU6PsaBEWKEQ23LFf/zMGnnxqfmpo0NotBJa/+e+G7atWvmqVLFhwhwjrX30QYf2sMtESIqyfsuOro1UUH446Z3FZ375DB5x0cj4yYv0LxOktRQa84q03Gyp++eWnP83756FWmi9EWH80IML6WWWiJURYP2XHF2ZpUYiMmDHp9N0OHVZQ1rcf5ZWVEQRZ/2JxSkshvI0VFVTxyyr6ffGies7l16yUAaucIcL6VxxEWD+rTLSECOun7CoRFljEGbEv4B9HnA2PhkNdiHNX3rv03NLldP7ggfpXipNaMiZ7/YEtxPj7kVD4caucAScihgjrX3T/+sf7H+9/zNCj9PdASzMJfPvRT5/85YrhR5s5RrZsG32rn+Oro7MVKBuMy4nIsHtQbTBf27kIEdYfsjk3zl+29xEDBnbtjVsR9VMzp+Xmtdvox89XrBh911mOvMo3WoRFFBxfmGXOUrO9VYiwxUMIEdYfoEcnvXAyI3r9oOF7S517lunviJaGEti6voK+fn+JzIlOmzD93DcNNW4RYxBhiwTCAW5AhC0eRIhwagF6fNKLp3LGH+qyW5k0dNiA3QJ5/tQMoHXaBEKNYVr65aqqzeu215NMV4yb/td/p23M4h2NFmHXVEdbPK7ZcA8inA3qKYwJEU4B1s6mj016tjPnniskj2dix+4ljbsP7lnWsUdp6obQQxeB7Rsq6bel6yu2b6zKk2OxGYzF/nHZ9Au26ups00YmiDA3/FwwhT8eEILsLUSwzx57XSOn8D7SZc/oPx66Bs1So5k3PF/ConSex+cbwznfo2vvjg099uzapRMEud0R2bahkjas3rxl89rt+YyxX2ORyBzupefH33NeVbuN28CA0e8j11VH2yDGmXIRIpwp0mmOAxFOE1xCt5mTXtibZH6C1+89LRqJHVpYkr+pY49Sb+eeZZ1KOheRx2uJ7+swZrIGW4lFY1S1tZa2rq/YvG19RbS+urGn1+tZHI1EXyeJvTN++rlLDB7S8uaMFmFUR1s+5KY5CBE2Da0xhiHCxnDUWnlkwjNlLNd3GOPsUMnD/sA5HeDze8JFJQXB4i4dcjuUFXQoLM6n/A55xg9ucYsNNY1UV91ANRX1NdVbappqq+pzIuGonzH2jRzjn3PGF/OmyBeXP3phhcWnYqp7RouwcBbV0aaGzLLGIcKWDc0OxyDCmQnQY5OeHcpj0t7EpKGSR9qHSWxoLBrrFcj1V+cV5coFRbne/OKCgryCgJSbn0M5+QHlabdHsCFE4tnUEKTG+pDcUF1fX1/bFG2sbZJCTeFij9ezjsv8Jzkm/0Bc/ol55CWXTb/gJ7vN02x/IcJmE3aPfYiwxWMNEc5egJ666KmchpLAnsxDezBOfRhRb6/P258Y9ZFl3k2OySWSl0X8fn/En+vjgVw/9+f4PYEcn9eX4/f7A17J6/OQ1+clj/jX6yHJK5HHI5GkPiVGjDFiO/9NnC3nnLjMSfwry5zkmKw8Y+LfqEzRaIxikRhFI1GKRmIUDkXlSDAcDgUj0XAwHAs1hVm4KcLC4bBPjnKf5JGqJIltIk5ropHoSk60ljNaw2P0a35VaPXFT18czB5x+4xstAijOto+sTfaU4iw0UQNtgcRNhiogeY452zmdfO7xGKhLj7JI25M7ihz6siIl3JixR5JKpM8UikjXswZKyJO+Zx4DnEKEOd+zrmPiDyck4cT9zDOGKf/FckyYpyL/4jFGKMYEcUYYxFiLEyMQoxYkBg1MM5rObFqOSZXxmS5ghGv5sQqicsVkiRti8ixCo8nsGX8fWdtYWIIPNpNwAQRRnV0u6NiTwMQYYvHDSJs8QAZ7x4TWa/IjokIgmk8X0MsQoQNwQgjO9/kht+eBrLGEYAIG8cSlkDAKAJGizCqo42KjP3sIBO2eMwgwhYPENxzJQGjRVhARHW0K5eSst2FTNjCsYcIWzg4cM21BCDCrg294ROHCBuO1FiDEGFjecIaCBhBwGgRRnW0EVGxpw2IsMXjBhG2eIDgnisJmCDCqI525UraUX2J7WgLBx8ibOHgwDXXEoAIuzb0hk8cImw4UmMNQoSN5QlrIGAEAaNFGNXRRkTFnjYgwhaPG0TY4gGCe64kYLQIC4iojnblUsJ2tNXDDhG2eoTgnxsJQITdGHVz5oxM2ByuhlmFCBuGEoZAwDACRoswqqMNC43tDEGELR4yiLDFAwT3XEnABBFGdbQrVxKqoy0fdoiw5UMEB11IACLswqCbNGVkwiaBNcosRNgokrADAsYRMFqEUR1tXGzsZgkibPGIQYQtHiC450oCRouwgIjqaFcuJVRHWz3sEGGrRwj+uZEARNiNUTdnzsiEzeFqmFWIsGEoYQgEDCNgtAijOtqw0NjOEETY4iGDCFs8QHDPlQRMEGFUR7tyJaE62vJhhwhbPkRw0IUE7CLCHxPRUW3F55FrjqbLHxBN8cg0AbDPNPG0xvvkkWuOPjqtnkk63f7mmI85sTbfl0aNBzsg4EQCjPgnt5w8x7D3pSnV0SmAx5ZoCrAMbgr2BgOFORAAARBIh4Dh1dEpOAEhSAGWwU3B3mCgMAcCIAAC6RCACKdDzf59IML2jyFmAAIgYHMCplRHp8AEQpACLIObgr3BQGEOBEAABFIlUF5ebnx1dApOQAhSgGVwU7A3GCjMgQAIgECqBCDCqRJzTnuIsHNiiZmAAAjYlACqo20aOAPchggbABEmQAAEQKC9BFCY1V6C9uwPEbZn3OA1CICAwwhAhB0WUJ3TgQjrBIVmIAACIGAWAVRHm0XW+nYhwtaPETwEARBwOAEUZjk8wK1MDyLs3thj5iAAAhYhABG2SCCy4AZEOAvQMSQIgAAIaAmgOtq96wEi7N7YY+YgAAIWIoDCLAsFI4OuQIQzCBtDgQAIgEBLBCDC7lwbEGF3xh2zBgEQsBABVEdbKBgZdgUinGHgGA4EQAAEEgmUl5d/x7KIBUKQPfhgnz32GBkEQAAEFALl5eVLIMLuXAwQYXfGHbMGARCwCIFx48YdJcvySHbRRRfl+P3+9Yyx8m7dur0+ZcoUOUM+QggyBDrJMGCfPfYYGQRAwMUEzjrrLA8ReebPnx8WGJRMeOzYsadyzq8iooNnz55doPIpLy+vIKJS8XMsFit74oknKnem0Ea8zsvLy4U9s+yLVN8IP51oR3ARRXngs2NLCBzAwei/b1hXxuqFI3hyztdJklQry/L9c+bM+U9chLN0UYJsLEvgiQjss8ceI4MACLiYQHl5ed7s2bMbVQQ4E3bnYoAIuzPumDUIgIDFCECELRaQDLkDEc4QaAwDAiAAAq0RgAi7c31AhN0Zd8waBEDAYgQgwhYLSIbcgQhnCDSGAQEQAAFkwlgDiQQgwlgTIAACIGABAsiELRCELLgAEc4CdAwJAiAAAokEIMLuXBMQYXfGHbMGARCwGAGIsMUCkiF3IMIZAo1hQAAEQABnwlgDOBPGGgABEAABCxJAJmzBoGTAJWTCGYCMIUAABECgLQIQ4bYIOfP3EGFnxhWzAgEQsBkBiLDNAmaQuxBhg0DCDAiAAAi0hwBEuD307NN3IhHdQUQ3ENFDmi9wEN+cdQ8R3UxEM+wzHXgKAiAAAs4gABF2RhzbmkUhEYmv64sSkfj2jjIiEl8jmUtE3p0/17VlBL8HARAAARAwlgBE2FieVrZ2NxFdQ0R+jZPiS6UfIKLJVnYcvoEACICAUwlAhJ0a2V3nJbLhbUQU0PwqRESdiAhZsHvWAWYKAiBgIQIQYQsFIwOuaLNhZMEZAI4hQAAEQKA1AhBhd60PbTaMLNhdscdsQQAELEgAImzBoJjsksiGRbW0qIbGWbDJsGEeBEAABJAJ23ANrJ5FHYIe6uT1UAnj1CEapUImUS7jFOBEPk7kkcS8OHFZolEo8/sAABV1SURBVChxCnNOQZ9EDTGZ6j1ENbEYVTM/VQy8tNmZr8iGnyKii3EWbMOFAZdBAAQcRQCZcBbDuWoW7Rnz0hDiNFDm1M8j+fpzYr2IR7sSY5xJOfWSNy8keQtiHl8+SVKBl3lzPEzyykSKBO+85VdmXI4wHgt7uByS5FjQE4s2eOVInSTH6r1clpnk8VcRSZs5l9dyuWkV47SWM/pNjtLqwQNoJTtauX0JDxAAARAAgQwSgAhnCPZvT1FOMEJHMkaHE/McRowOYlJO1J/fqyGneKA/p2hQF19eD/LldiNvTmeSPDmGeSbHghQLVVA0tJ2iwa0UadoUCdavaYg2rI2GGzf4YqGKIiblbuKMfuLRxm84px89nL4fMJaWG+YEDIEACIAACOxCACJs4qL4eS71ZUQne30dzo5Fag8O5PfZnNfxYJ7faVin3OIhPo+/xMTRUzHNKVy/lkL1v1KwZkVDU9WS+nDdKn80Uh+QPL7vYtGmT0imRQGiz/ccSzWpWEZbEAABEACBlglAhE1YHcvm0oUeb4cJshwaUtjlD/VF3Y/vnNfxEEOzWxPc3sVkLFxNTdU/U1PV98GGbV81hWqXFzFv/ko5XPs6Y/TBwDH0USb8wBggAAIg4FQCEGEDI7tsNl0jeXMnB4r689I9zu1U2PVPBlq3hqnGiv9S/bZF4fotH9dEGjfkcTn6BhG92UGmf3cfq3wkZquPVQ9TkRyg7rJEXWWZOkkeKmVExZxTEWeULxHlECe/zMlLjBgjkhlRhBiFOKcmIqrnjGokTtXKR28y2i5Haavko80JBWhtuYLfgwAIgEDWCUCEDQjBsjl0uuQr/EduhyE5nQZcVppTPMQAq9Y3EQ1uo/qtn1PN+jc3N1X92JmY73WSwy/4OX0QZjSEMRrEJe8gj7dgX068L48GuxBxj8ffIegNlMY8/jLmDZSJbfkcj69Akjy5xDwBYpKPiElCg4lzTsSjJMsR4rEgydFGkqP1FA1Xh2OhbY3R4LZYNFztiUXq8hljTYyk9bIcXkGcVhPRSslDy0Ih+nnv8VRlfaLwEARAwG0EIMLtjPjyJ3yPenyF53Td65aSgi5/aKc1+3aPReqobtMHVPP7vyqDtasK/Xk963OK+nn8Rf2L/Hm7kVJ0lteNPL4Opk0yFqkVRWcUadxAobpfKoM1K4Lhut+8keDGYmKezXI09IXE6EvG6IsBo+kr0xyBYRAAARDQSQAirBNUYjNR7Rxhhe/llu47qMf+93VSsjc8LEsgXL+GGquXNNZvWbglWPldIBqpKSSSF3Di71KM3ho8ljZZ1nk4BgIg4FgC2RThKUQknrZ8rHiqYGFR9+EDuu51k/haQDxsRiAaqqD6bQsb6zYuqGqs+KaTx9fhx2iwYlZNkF469Eqqtdl04C4IgIBNCWRLhMWepPg+W0+2uK2aQz1DMvWRPNSTydSdM+rKOHViEpXKxEol8hRzYkWMeB4nnsOI+4i4l4tPyeCcFXU/rqr7fnda5R6jbGF0zLh1mz+m6rXzKxorv8tnkvcJOdL08KByWumYCWIiIAACliSQLREWXya/nYjyzaYito2bYnSwxGl/zmkfIhpCTBrEJG/MEyitC+T14L68Hl5vTmfJE+jk9wXKcjyB4lzJW0CSN1+5rYhJO4qFmOQlomwhM5sU7AsC4sNMKlfPq61c81IBMXooEpZvR1EX1gYIgIBZBLKpKJuJaDcSt58Y/Fg5l/4Y43Q0kwLDuRwe5s3ptD7QYWBDfukBOXmle3fzF+yZI3nzDB4V5pxEQBR5bf35/q11mz9lsUhj+eCx9LqT5oe5gAAIWINANkX4RyI6iYjWGYFi2Ww6zpvb5RI5UjfC4y+mwi5/lPI7H16UV3bgjlte8ACBNAjUb11Im767oTESbZo8ZAw9nIYJdAEBEACBFglkU4TfJqLpROl/6tKSmVTi9dFor6/wSo+/tKi412lFhd2OVT5/GQ8QMIpAuGEdrf3i0oZopOqywaNpnlF2YQcEQAAEsinCDxDRxp1CrEZCbE/3IKLFbYVm6Ry61uMJ3JLX8ZBQWd9LOuYWD22rC34PAmkTaKr6ntYtHt8YDoV74ow4bYzoCAIgkEAgmyJ8HhGJ54kan5YQ0SAiEh+FOI2IfkiM2E+zaV9/TunzOQW7d+o89PpOgYI9EFQQyAiBTd/f2lC74e2pA8fQ/RkZEIOAAAg4nkA2RVjsGYuvyhtARKJISzzE5z1+S0R+IgoSkdiyvp2Ivhe/XDabDmMe/zudB11VVNLnbMcHBxO0FoGGrQvp96+ven/QGBphLc/gDQiAgF0JZFOEBbOpRLQ/EU3QFGi9REQjNUAVMe7bkx5+6/b8eV2GXLtbh55/titv+G1jAo0V39C6xeM+HTSGjrLxNOA6CICAhQhkW4QFClGcVUhE5Rou4tt4mt1DlOOn+lUvH1bd8+CHe1qIH1xxEYFNP9y2umb9W/MHjaHJLpo2pgoCIGAiASuIsJieRETyznkmzYRn/40Kzj7/zhFF3Y8zEUfqpm9/cC7t0bsHnXf6Ca121tsudQ927bFi9VqaMn0WPXLX9VRWsusXJjQFQ3T1bTNo1rzX4p2fe+T2NucgGmdyHkawMMpGsPpnWvPFxaFoTB6y11jlG5rwAAEQAIF2E7CKCKsTSXYmrBRoLZtDj3QedNWE0j1GtXvSRhrQK0p62xnhW2siXFFVQ+dNuJkOP2gfuuXq0cpw6mviZ/F6a49MzsMIFkbYCNWtprVfXFIrRxquGlROTxthEzZAAARAQBCwmgi3WB29bDYdKXlz/7PnMW8UePzW+chmrSgt/PoHeuRJkcgTvfjvBbTP4P700qy76ZsfltL5l9+ivK5mnKLtEadeqrw2dtTp9ODUicr/iwy1uqaeXnpjAX04/zF6+Y33qUfXznTr/Y8rv5927bi4eAqxPXvsZPph6Uo67qhh9PyjdyhthMi+98mi+GvabPj5196hz778ThkvNycQfxeI139duyFuW/ys+pzqPF57+6O4rUSBF/Oe98pbyvjf/rg8zkA48vm/n6D99xqoMBh15knxCwLB+JgjDmrzAsGMt3Td5g9pw7c3ii8zvnzQGJptxhiwCQIg4F4CVhPhVu8TXj6HbvLkdrmm1yGPlfrze1kiaokiLIRVKyZCQEWGqW0nxPPKm++nh++4lnr16KqIjmg36bJR8f8XfdRtYzFRVbQmTL5XEfaOpcWK2KrZq7C/YfNWpd26DZuTbker9v5wyH6tbj0LoRT2hKgLARf/Lx565zHylOH0xD//TVMnjVV8ue3+WXTOX46jU487koS4i8eB+wyOMxiwZ2/ldfXiIFHEb7rnUbrzhglJt9bNWgQ8FqKN39+2sXH7olgk1FA+ZBy9a9ZYsAsCIOBeAlYT4TYjsWw2XUESe6hT/8vqyvpeUtRmB5MbJIqwVry02aW2XWI2qmaHd02+nG68+xFSRTJRNEVWefmN99KUSWNpe2V1M6HUbkGL3yU7E1btJWaZapatZuTaDFngS3Uet/xtNE2a9ve4n8KfJUtX0fiLzqJ7H32GLj3nVBLCq31oM2Qh3KqIi2z5o8+/jmfoJodTMV/12/Py1uX/CHMenemP0bQ9x1JNJsbFGCAAAu4jYDsRFiFSPrDDmzeVEx1T3PuMUEnvM8t8eeKDtjL/SBRhdatVCFlr4qVu9aoei+3kJ2bcQrf/fW58KzZRNBNFWN3OVm2o28bi59ZEOFkmrBVB0T+xcEvdBk+8mEg2D5FBz3x6vrKF/NV3P9PRhx9Iby74Pzr71BH0wKzn4lmtsKVeAIgxtdvyt02fpYi12I7P8Fb0CyveOfRUxjzvydHQU94gvd/vSgplfmVhRBAAATcQsKUIq4FZMZcO5pzOYZ7AuZK3iAq6HB4t6HJU17zS/STxNYSZeKQrwtrzV9XPRNFtS4S1gq+da2uFWS2dCWtFWGwHa8+NW7uYSDYP4Yuw9/OK1bRlW6WSAT87/y3Kz8tRfhbb2olb3trx1QuYrduraMXqNRnfig7WLKO6zZ9sr9/8USTcuK6EMe/bsWhovlxMrw0dSeFMrCuMAQIg4A4CthZhbYhE4RZj9EdiviOJ8YMkT67sz989FOgw0Jdb1K/Il9/L68vrTr6cLkRM3BFlzCMdEdaeCYttWfU8V92OVreLWxPhxDNhIZTzXnlbOcdtaTtazLi16ug+u3VTzpS1ItzYFGxWTd3S2bZ2Huq5tDgL7tWzq3I2LLaV//HES3TFpWcrBVZaEc7LzVEyb/FQC8bUorMzTjomo1vRiasiFqmj2g3vVNesf6MpWLe6SJJ8L3C5cfbAS+kbY1YQrIAACLiZgGNEODGIPz9Jg6Wo8jnU/cnjPZKRNJh4rBNRLDDgxG8WENHROz8es13x1yvCarVxsupotbJZFSM9IixET1sdrW5Fi9dVoRUTU4urEieZuBWsvU9Y7a9WWF924Zn0zkcL4wIttqBbm4co5ko8z07MzrX3Kgvfp147ll58/b34vc3Jzq/bFSgDOkeDW6hq7St1VWteJi7HFhIF7xt4KX1sgGmYAAEQcCkBR4own0LSsm50iidQdDbJ0eMlfyEr7HSE+H7hwryyAyhTW9UuXVOGTLutDxwxZJB2GKlc82JNxcrZnCj6AcmN1/e/hH5thzl0BQEQcCkBR4nwL49R54iXRktSzmXe3E6+4t5nFhV1Pz7XGyhzaXjtOW31Hmpxq1dbHx6S7RluW/FIXeWvL/iJh8cPHE1PZtsfjA8CIGAvAo4R4eVz6RLOvHcWdDwk3Gnglb0ChXvaKxLw1rYEgjVLacM31zZGQlumDxpNt9l2InAcBEAg4wQcIcLLZ9PNUqD4bz0P+ntZbvHQjEPEgCAgx5pozWfnV4ca1949eDTdByIgAAIgoIeA7UVYuU1Jyv247zH/yfP4d/2yAj0Q0AYEjCAQadpMv350isy88pABFyvflY0HCIAACLRKwPYivHwuXVfce+RtXYZc1+yrDxF3EMgGgc0/3lVTve61+waNobuyMT7GBAEQsBcB+4vwHJpW1n/sLR37jbEXeXjrSAJVa14Mbfl5+txBY+hyR04QkwIBEDCUgO1F+OfZdEpu4e5P7n7kfJRAG7o0YCwdAhu+uWZb7Zb/mzp4DD2aTn/0AQEQcBcB24uwCNeqZ0oWFfcZeSiyYXctXqvNtnbju7T5h2m/B33hQftcQA1W8w/+gAAIWI+AI0R46Vzq7fXm/ye/y1Gl3feZ2t16mOGR0wlsW/F4rOrXZyrlWOSsQeX0qdPni/mBAAgYQ8ARIixQ/DyXSj3M93fJW3hS171uKC3seowxhGAFBFogwHmMqte8TBW/PNlIkn8hC20Z33c0/QJgIAACIKCXgGNEWJ3wsjl0uuQrnOL1l+1W1vfC4g49T9bLAu1AoE0CcrSe6rd8RtXr39zaWPF1J6+v+M1wuOqhIWPoozY7owEIgAAIJBBwnAir8xMFW75Ah2t4LHhwYbdj6zv0PLlTXtmBWAAgkBKBUN0v1FT1U11jxTe1jZXf58TCFQGJeT+Kyk1vSozeHngpbUzJIBqDAAiAgIaAY0VYneMvc6lvhOgsyZN/PpG8e36nwyi/02G5eaX7kj+/NxaDWwhwmbgcJlkOE48FSY42UixaT3KkjmKRGoqFqijStKUx1LCuLtq4LhYObsvl0cYCJnlWyHL0e8bpO4nTVwPG0uduQYZ5ggAImE/A8SKsRbhkJu0R8NMxUm63kTxcty/nsQJfwe51uR0GsdySwR38+bv7fXk9yRsoTZu8+KMealhLSgZV/XOwqfK7UKRxY07XoTcEOux2Stp20VE/ge2r5tRuXzmraEcPxolYjDEWI2IRYizMmNTEiTUyxmqJeDWX5Qoux7YQi21inDbLROslidZF19FvQ6dSWP/IaAkCIAACqRFwlQgnovlhDvX0c9qXGA3lRIMkyT+Ec74HUazA4yuq8/iKGiRfUdDjK4hI3gJZkgLEPH7BzEvEfXIs5JcjdSwWrpYioSq/HKnM43LUI3ny1xPx7+RozWdcoq8lRh4u+6b783t36brX5N65JfukFiW01kWgas3L1dtXzpI5j3zGo423eppoRU2A5AM2UYxNIVmXETQCARAAgQwScLUIt8R5+RNUyGPUzeulbmGZOkucSkiiAi5TrkcIKifOiSKMqJEzqiGZKqIybSYP/b7XGNrSkt2lc+gyyZNza27xILljv7HdcUbd/pUei9RS1Zp/bqv67SUfl8PfRMPBe4aMow/bbxkWQAAEQMB8AhBh8xnvMsLSOTTB48292usvLSzZ/ZwORT1OCnh8hVnwxL5DigrlqrUvb2rYtrirxKRnZDk2Z1A5fWHfGcFzEAABNxKACGcx6kvn0Ik+f1F5NFx/cn7ZflVFPU4sy+98BHkD+ATOxLDI0QZq2LaIaje+t71h26IC5gks45GauXlEL+42miqzGEYMDQIgAAJpE4AIp43OuI5i+zsm06k+T8FZMg8d68vtGizo/Me8vI4H5YgqbslbYNxgNrEktpmbqpZQQ8U3wYatC+vCDWuLJU/uZ7Fow2vMS28NupjW2GQqcBMEQAAEWiQAEbbg4lg2m44kiY6UPAXHybHgAb5ASWOgeCjll+5fEijqT4HCPcjjL7Gg5+m5JL6HN1z/G4XqVsmNld9VhmqWeqLhmhzmyflWjtR/IDH6rP+e9Ck7mqLpjYBeIAACIGBNAhBha8almVernqT9ZZn258x3gOTNGyZHG/syj4/7cns25hTuyfyFfQsCBX1yfbndyZfXzZKZczS4jSJNmyjStJFC9b/WhmtXN4Xq10iRpk2FxKQmSfKviEVrxZnuEnFP7sAxtMQGoYGLIAACINAuAhDhduHLXucfH6XdPH4aSET9JaK+JAUGMSb15TzSnUhiXn9x0JPThXw5XQK+vC65InP2+DqQKACTxNObT5InjyRPDjFPgJTbryQvkeQlxjzi/tqdkxOl4DIRjxGXo8oHXigfeiE+8CLWROKsVnkqH3pRS7FwDcXCFdFw0+bGWNPmaCRU6ZUjtfkkeWuJe34nCi/ncuwXRvQLMVrJfbR80IVUkT2SGBkEQAAEskcAIpw99qaNvPZ5Kmlooh4sRt0lD3WRSeoiSb6uxKTORFIZJ17MiAq5zAuI8VwiOUBc9nPOfYy4hxOXiHNlbTBGnHPGd3zYhRQjxiJEUogx1kTEGjlj9YxYDSdeJXHaLvPoVjkW3swZbeUybfb7aCOrpw39rqSQaROGYRAAARCwKQGIsE0DB7dBAARAAATsTwAibP8YYgYgAAIgAAI2JQARtmng4DYIgAAIgID9Cfw/UmnL3Zmym/YAAAAASUVORK5CYII=)_

#### Step 2: Network Security & Access
**Security Groups = stateful firewall at instance level** = Personal bodyguard for each server (follows you around)
**NACLs = stateless firewall at subnet level (rarely needed; SGs usually sufficient)** Building security at the entrance (checks everyone entering/leaving the **subnet**)

| **Property**           | **Security Group (SG)**                                | **Network ACL (NACL)**                                    |
| ---------------------- | ------------------------------------------------------ | --------------------------------------------------------- |
| **Operates At**        | **Instance level** (EC2, ELB, RDS)                     | **Subnet level**                                          |
| **Stateful/Stateless** | **Stateful** (Return traffic is automatically allowed) | **Stateless** (Return traffic must be explicitly allowed) |
| **Rule Types**         | **ALLOW rules only**                                   | **ALLOW and DENY rules**                                  |
| **Evaluation Order**   | Evaluate all rules before deciding                     | Process rules in number order (lowest first)              |
| **Default Behavior**   | **Default DENY all inbou****nd**, ALLOW all outbound   | **Default ALLOW all inbound and outbound**                |
| **Use Case**           | Primary firewall for instances, fine-grained control   | Subnet-wide firewall, **block specific IP ranges**        |
| **Exam Trigger**       | **"Instance-level firewall,"** "Stateful"              | **"Block specific IP,"** "Subnet-level firewall"          |

### ALB vs NLB

| Dimension | ALB (Application Load Balancer) | NLB (Network Load Balancer) |
|---|---|---|
| Layer | Layer 7 (HTTP/HTTPS) | Layer 4 (TCP/UDP) |
| Routing | Path-based, host-based, header-based | IP:Port only |
| WebSocket | Yes | Yes |
| gRPC | Yes | Yes |
| Static IP | No (DNS name) | Yes (per AZ) |
| Latency | ~1ms+ | <1ms (ultra-low) |
| Use case | Web apps, microservices, API Gateway | Real-time, gaming, IoT, fixed IP requirement |

> **Default choice = ALB.** Use NLB only for ultra-low latency or fixed IP requirement (whitelisting by partners).

### CDN — CloudFront

```
User → CloudFront Edge (150+ PoPs globally)
  → Cache HIT → return cached response (0ms to origin)
  → Cache MISS → fetch from origin (ALB / S3) → cache + return
```

**What to cache:** Static assets (JS, CSS, images), API responses with Cache-Control headers, pre-rendered pages  
**What NOT to cache:** Authenticated responses, user-specific data (unless using signed URLs)

### Route 53 Routing Policies

| Policy            | Use Case                                                       |
| ----------------- | -------------------------------------------------------------- |
| **Simple**        | Single record, no health checks                                |
| **Weighted**      | A/B testing, ==canary at DNS level== (e.g., 10% to new region) |
| **Latency-based** | Route to closest AWS region                                    |
| **Failover**      | Primary/secondary — auto-switch on health check failure        |
| **Geolocation**   | Route Indian users to Mumbai region                            |
| **Geoproximity**  | Route based on geographic distance with bias                   |

### Interview Q&A
**Q: Design a VPC architecture for a multi-tier microservices application.**
A: Three-tier subnet structure in each AZ: public subnets for the load balancer and NAT gateway, private subnets for application workloads (ECS/EKS), and isolated database subnets for RDS and ElastiCache. No direct internet route to private or database subnets. Internet Gateway for public, NAT Gateway for private outbound. <mark style="background: #FFB86CA6;">Security Groups: ALB accepts 443 from internet; app SG accepts 8080 only from ALB SG; DB SG accepts 5432 only from app SG</mark>. Replicated across two AZs minimum for HA.

---

## Topic 9 · FinOps — Cloud Cost Architecture

### In One Line
FinOps is the practice of <mark style="background: #ADCCFFA6;">making cloud cost a shared engineering responsibility</mark> — tagging, rightsizing, and purchasing strategy can cut bills by 40-60%.
### Cost Tagging Strategy
Every resource tagged with:
```
Environment: production | staging | dev
Team: order-team | payment-team | platform
Service: order-service | payment-service
CostCenter: CC-1234
Project: ecommerce-platform
```
→ Cost allocation reports <mark style="background: #D2B3FFA6;">per team, per service, per environment</mark>  
→ <mark style="background: #ABF7F7A6;">Teams own their cost; no surprises at month end</mark>

### Purchase Model Strategy

| Model | When to Use | Savings vs On-Demand |
|---|---|---|
| **On-Demand** | Unpredictable/bursty, new workloads | Baseline |
| **Reserved Instances (1yr)** | Steady-state baseline load | ~30-40% |
| **Reserved Instances (3yr)** | Committed, stable workloads | ~50-60% |
| **Savings Plans** | Flexible compute commitment | ~20-40% |
| **Spot Instances** | Fault-tolerant, batch, stateless | ~70-90% |

**Hybrid strategy:**
```
Baseline load (always running) → Reserved Instances (1-year commitment)
Variable load (scales up) → On-Demand or Spot (via ASG mixed instances)
Batch jobs, ML training → Spot (accept interruption, save 70-90%)
```
### Rightsizing
- Use <mark style="background: #FFB86CA6;">AWS Compute Optimizer</mark> or <mark style="background: #ADCCFFA6;">CloudWatch metrics</mark> to identify over-provisioned instances
- Target: CPU utilization 60-70% average (not 20% = waste, not 95% = no headroom)
- Common find: `t3.xlarge` doing the work of a `t3.medium` → 50% cost reduction

### Cost Governance
- **AWS Budgets** — <mark style="background: #BBFABBA6;">alert when spend exceeds threshold</mark> (e.g., team budget $5K/month)
- **Cost Anomaly Detection** — <mark style="background: #ADCCFFA6;">ML-based alert</mark> on unexpected spend spikes
- **S3 Lifecycle policies** — <mark style="background: #D2B3FFA6;">move old objects to Glacier </mark>automatically
- **Auto-stop in dev** — <mark style="background: #ABF7F7A6;">Lambda function stops dev RDS/EC2 instances at 8pm daily</mark>

### Interview Q&A
**Q: How would you architect a 60% cloud cost reduction without impacting production?**
A: 
- <mark style="background: #ADCCFFA6;">First, tagging and attribution — if teams don't see their costs, they don't optimize. </mark> <mark style="background: #BBFABBA6;">Tag everything, give teams dashboards.</mark> 
- Second, Reserved Instances for baseline compute — identify always-on services, buy 1-year RIs for ~35% saving. 
- <mark style="background: #D2B3FFA6;">Third, Spot for stateless and batch </mark>— <mark style="background: #D2B3FFA6;">**ECS Fargate Spot** for non-critical services</mark> (70-90% cheaper), Spot for ML training jobs. 
- Fourth, rightsizing —<mark style="background: #FFB86CA6;"> Compute Optimizer shows over-provisioned resources; right-size without guessing</mark>. 
- Fifth, architectural: enable caching (CloudFront, ElastiCache), delete unused resources, <mark style="background: #ADCCFFA6;">S3 lifecycle to Glacier for old data</mark>.
---

## Day 4 Quick Reference

| Topic                 | Key Interview Answer                                                                                |
| --------------------- | --------------------------------------------------------------------------------------------------- |
| Well-Architected      | 5 pillars: OpEx, Security, Reliability, Performance, Cost (+ Sustainability)                        |
| ECS vs EKS            | ECS Fargate = simpler ops, AWS-native; EKS = portability, full k8s ecosystem                        |
| Kubernetes HPA        | Scales pods on CPU/memory; ==pair with Cluster Autoscaler for nodes==                               |
| Readiness vs Liveness | Readiness = traffic gate; Liveness = restart trigger; ==never make liveness hit external services== |
| Blue-Green            | Instant rollback, 2x infra cost; for high-risk releases                                             |
| Canary                | Gradual rollout, lower cost; for most releases; monitor metrics before 100%                         |
| GitOps                | Git = source of truth; ArgoCD pulls + reconciles; rollback = git revert                             |
| ALB vs NLB            | ==ALB for HTTP/routing (default)==; NLB for ultra-low latency or fixed IP                           |
| VPC design            | Public (LB+NAT) → Private (app) → Isolated (DB); no internet route to private/DB                    |
| FinOps                | Tag everything → Reserved for baseline → Spot for batch → rightsize → delete waste                  |

---

*Tags: #AWS #well-architected #ECS #EKS #kubernetes #HPA #CICD #GitOps #ArgoCD #terraform #blue-green #canary #VPC #ALB #NLB #CloudFront #FinOps*
