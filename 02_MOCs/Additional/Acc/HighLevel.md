## 1. The Application & Container Layer

_This focuses on how code behaves when packaged into modern cloud-native deployment units._

- **Java & Spring Boot Lifecycle:** How Spring Boot microservices interact with their underlying platform (e.g., handling thread pools, database connection pools like HikariCP).
- **Docker Containerization:** Packaging Java applications efficiently, understanding multi-stage builds, and troubleshooting container lifecycle issues.
- **JVM vs. Container Memory Management:** Tuning JVM heap size flags (`-Xmx`, `-Xms`) dynamically alongside Docker/Kubernetes memory resource constraints to avoid **`OOMKilled` (Out of Memory)** errors.
- 

## ☸️ 2. The Orchestration & Cloud Infrastructure Layer

_This covers the platform itself and how infrastructure is managed deterministically via automation._

- **Kubernetes (K8s) Core Architecture:** Deep diving into Pod states (`CrashLoopBackOff`, `Pending`, `Evicted`), Services, Ingress routing, ConfigMaps, and Secrets.
- **Azure Cloud Platform:** Navigating Azure Kubernetes Service (AKS), Azure Application Gateway, Azure Key Vault, Managed Identities, and Azure Monitor.
- **Terraform (Infrastructure as Code):** Reading and reviewing Terraform configurations, understanding state files, managing environment drift, and ensuring proper tag governance for deployment tracking.

## 🌐 3. Networking & Deep Observability

_The tools and tracking mechanisms used to act as a "software detective" across distributed systems._

- **Kubernetes & Cloud Networking:** Investigating pod-to-pod communication barriers, CoreDNS resolution drops, and Azure Network Security Group (NSG) rule conflicts.
- **Distributed Tracing & OpenTelemetry:** Implementing and tracking unique transaction IDs (Correlation IDs) across multiple microservices using tools like Azure Application Insights or Jaeger to isolate systemic latency.
- **Log Aggregation & Metrics:** Navigating the ELK stack, Prometheus, or Grafana to read system health dashboards and set proactive alerts before a degradation impacts business operations.

## 📈 4. Senior Governance & Leadership Pillars

_The high-level managerial and architectural responsibilities expected of someone with over 7.5 years of experience._

- **Cloud Cost Optimization:** Identifying resource over-provisioning (e.g., shrinking bloated K8s requests/limits based on historical metrics), scheduling non-production resource shutdowns, and managing log lifecycle retention policies to lower the monthly Azure bill.
- **Advanced Incident Management:** Directing critical production incidents under pressure as a coordinator, minimizing MTTR (Mean Time to Resolution), and running blameless post-mortems/Root Cause Analyses (RCA).
- **Architectural Change Governance:** Reviewing developer-driven infrastructure changes safely, implementing zero-downtime deployment strategies (e.g., Canary or Blue-Green rollouts), and continuously managing technical debt.

This comprehensive map ensures you can walk into the Pune office showing fluency whether you are talking to a hard-core infrastructure engineer or an application developer.