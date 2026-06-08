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
A production CI/CD pipeline automates <mark style="background: #ADCCFFA6;">build → test → scan → deploy with quality gates</mark> that prevent bad code from reaching production.

### Pipeline Stages for a Java Microservice

```
[Code Push / PR]
      ↓
[CI Pipeline — runs on every PR]
  1. Checkout + cache dependencies
  2. Compile (mvn compile)
  3. Unit Tests (mvn test) — must pass, coverage > 80%
  4. Code Quality (SonarQube scan) — quality gate must pass
  5. SAST — Static Application Security Testing (Checkmarx / Snyk)
  6. Build Docker image
  7. Image scan (Trivy / Snyk Container) — no critical CVEs
  8. Push to ECR / Artifactory (tagged with git SHA)

[Merge to main — triggers CD]
  9.  Deploy to Dev namespace (auto)
  10. Integration Tests (Testcontainers / real infra)
  11. Contract Tests (Pact verification)
  12. Deploy to Staging (auto)
  13. Smoke Tests
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

| Approach | Pros | Cons |
|---|---|---|
| **Polyrepo** (one repo per service) | Independent pipelines, clear ownership | Hard to do cross-service changes, many repos to manage |
| **Monorepo** (all services in one repo) | Atomic cross-service changes, single pipeline config | Build all or nothing without smart change detection |

**Monorepo with change detection (recommended):**
```yaml
# Only build services that changed
- name: Detect changed services
  id: changes
  run: |
    CHANGED=$(git diff --name-only HEAD~1 | grep -oP '^services/\K[^/]+' | sort -u)
    echo "services=$CHANGED" >> $GITHUB_OUTPUT
```

### Interview Q&A (40L SA Level)

**Q: Design a CI/CD pipeline for 20 microservices with a polyglot stack.**
A: I'd use a monorepo with path-based change detection — only the services that changed trigger their pipelines. Shared pipeline template (GitHub Actions reusable workflow or Jenkins shared library) parameterized per language (Java uses Maven, Python uses pip/pytest, Node uses npm). Each service pipeline: unit tests → SAST scan → Docker build → image scan → push to registry → deploy to dev → integration tests → staging → approval gate → canary to prod. Pact contract tests run in the provider's pipeline — provider can't deploy if it breaks any consumer contract.

**Q: How do you prevent a bad deployment from impacting production?**
A: Multiple gates. Quality gate in CI (SonarQube fails if coverage drops or code smells spike). Image scan rejects critical CVEs. Canary deployment — route 5% of traffic to new version, monitor error rate and latency for 10 minutes via CloudWatch/Prometheus alerts. If metrics degrade, automated rollback triggers (ArgoCD rollback or `kubectl rollout undo`). Post-deploy smoke tests fail fast. The rollback must be tested in staging too — it's useless if it doesn't work when you need it.

---

## Topic 5 · Deployment Patterns — Blue-Green & Canary

### In One Line
Blue-green gives instant rollback; canary reduces blast radius — choose based on how much risk you can accept per deployment.

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
**Best for:** High-risk releases, compliance-sensitive systems, when you need instant rollback.

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

**Best for:** Most production releases — lower cost than blue-green, gradual risk exposure.

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

## Topic 6 · Terraform — IaC Basics

### In One Line
Terraform declaratively defines cloud infrastructure as code — version-controlled, repeatable, reviewable, and destroyable.

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
A: Remote state in S3 with DynamoDB locking — prevents two engineers from running `terraform apply` simultaneously (which would corrupt state). State file is encrypted (S3 SSE). Separate state files per environment — staging and prod never share state. Terraform Cloud or Atlantis for plan/apply in CI — no one runs Terraform manually from their laptop in production.

---

## Topic 7 · GitOps — ArgoCD / Flux

### In One Line
GitOps makes Git the single source of truth for what runs in your cluster — the cluster continuously reconciles to match the desired state declared in Git.

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

### ArgoCD Application

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: order-service
  namespace: argocd
spec:
  project: default
  source:
    repoURL: https://github.com/company/k8s-manifests
    targetRevision: main
    path: services/order-service/overlays/production
  destination:
    server: https://kubernetes.default.svc
    namespace: production
  syncPolicy:
    automated:
      prune: true      # Delete resources removed from Git
      selfHeal: true   # Auto-fix manual cluster changes
```

### ArgoCD vs Flux

| Dimension | ArgoCD | Flux |
|---|---|---|
| UI | Yes — rich dashboard | No built-in UI |
| Multi-cluster | Yes | Yes |
| App of Apps | Yes | Kustomization chaining |
| Learning curve | Medium | Lower |
| **Use when** | Need UI, multi-cluster management | Simpler setup, GitOps-only |

### Interview Q&A
**Q: What is GitOps and why is it better than push-based CD?**
A: GitOps makes Git the single source of truth for cluster state. ArgoCD continuously pulls desired state from Git and reconciles the cluster to match. Advantages over push-based CD: no CD pipeline needs kubectl credentials (security), drift detection catches manual changes (operations), rollback is a git revert (auditable), and the cluster state is always visible in Git. Push-based CD is imperative — "deploy this now." GitOps is declarative — "cluster should always look like this."

---

## Topic 8 · Networking & Load Balancing on AWS

### In One Line
Understanding VPC design, ALB vs NLB, and CDN/DNS routing is table stakes for any SA designing on AWS.

### VPC Design — Standard Multi-Tier

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

**Security Groups = stateful firewall at instance level**  
**NACLs = stateless firewall at subnet level (rarely needed; SGs usually sufficient)**

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

| Policy | Use Case |
|---|---|
| **Simple** | Single record, no health checks |
| **Weighted** | A/B testing, canary at DNS level (e.g., 10% to new region) |
| **Latency-based** | Route to closest AWS region |
| **Failover** | Primary/secondary — auto-switch on health check failure |
| **Geolocation** | Route Indian users to Mumbai region |
| **Geoproximity** | Route based on geographic distance with bias |

### Interview Q&A
**Q: Design a VPC architecture for a multi-tier microservices application.**
A: Three-tier subnet structure in each AZ: public subnets for the load balancer and NAT gateway, private subnets for application workloads (ECS/EKS), and isolated database subnets for RDS and ElastiCache. No direct internet route to private or database subnets. Internet Gateway for public, NAT Gateway for private outbound. Security Groups: ALB accepts 443 from internet; app SG accepts 8080 only from ALB SG; DB SG accepts 5432 only from app SG. Replicated across two AZs minimum for HA.

---

## Topic 9 · FinOps — Cloud Cost Architecture

### In One Line
FinOps is the practice of making cloud cost a shared engineering responsibility — tagging, rightsizing, and purchasing strategy can cut bills by 40-60%.

### Cost Tagging Strategy
Every resource tagged with:
```
Environment: production | staging | dev
Team: order-team | payment-team | platform
Service: order-service | payment-service
CostCenter: CC-1234
Project: ecommerce-platform
```
→ Cost allocation reports per team, per service, per environment  
→ Teams own their cost; no surprises at month end

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
- Use AWS Compute Optimizer or CloudWatch metrics to identify over-provisioned instances
- Target: CPU utilization 60-70% average (not 20% = waste, not 95% = no headroom)
- Common find: `t3.xlarge` doing the work of a `t3.medium` → 50% cost reduction

### Cost Governance
- **AWS Budgets** — alert when spend exceeds threshold (e.g., team budget $5K/month)
- **Cost Anomaly Detection** — ML-based alert on unexpected spend spikes
- **S3 Lifecycle policies** — move old objects to Glacier automatically
- **Auto-stop in dev** — Lambda function stops dev RDS/EC2 instances at 8pm daily

### Interview Q&A
**Q: How would you architect a 60% cloud cost reduction without impacting production?**
A: Four levers. First, tagging and attribution — if teams don't see their costs, they don't optimize. Tag everything, give teams dashboards. Second, Reserved Instances for baseline compute — identify always-on services, buy 1-year RIs for ~35% saving. Third, Spot for stateless and batch — ECS Fargate Spot for non-critical services (70-90% cheaper), Spot for ML training jobs. Fourth, rightsizing — Compute Optimizer shows over-provisioned resources; right-size without guessing. Fifth, architectural: enable caching (CloudFront, ElastiCache), delete unused resources, S3 lifecycle to Glacier for old data.

---

## Day 4 Quick Reference

| Topic | Key Interview Answer |
|---|---|
| Well-Architected | 5 pillars: OpEx, Security, Reliability, Performance, Cost (+ Sustainability) |
| ECS vs EKS | ECS Fargate = simpler ops, AWS-native; EKS = portability, full k8s ecosystem |
| Kubernetes HPA | Scales pods on CPU/memory; pair with Cluster Autoscaler for nodes |
| Readiness vs Liveness | Readiness = traffic gate; Liveness = restart trigger; never make liveness hit external services |
| Blue-Green | Instant rollback, 2x infra cost; for high-risk releases |
| Canary | Gradual rollout, lower cost; for most releases; monitor metrics before 100% |
| GitOps | Git = source of truth; ArgoCD pulls + reconciles; rollback = git revert |
| ALB vs NLB | ALB for HTTP/routing (default); NLB for ultra-low latency or fixed IP |
| VPC design | Public (LB+NAT) → Private (app) → Isolated (DB); no internet route to private/DB |
| FinOps | Tag everything → Reserved for baseline → Spot for batch → rightsize → delete waste |

---

*Tags: #AWS #well-architected #ECS #EKS #kubernetes #HPA #CICD #GitOps #ArgoCD #terraform #blue-green #canary #VPC #ALB #NLB #CloudFront #FinOps*
