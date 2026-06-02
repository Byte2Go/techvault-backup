### Phase 1: Discovery and Assessment (The Inventory)
Before moving any data, you must <mark style="background: #FFB86CA6;">map the current state to prevent breaking hidden application dependencies.</mark>
- **The Mechanism:** Deploy **AWS Application Discovery Service**  inside the on-premises data center.
- **The Architect's Focus:** You use these tools to discover host configurations, running processes, and network mapping. This establishes the <mark style="background: #FFB86CA6;">application dependency graph </mark>(e.g., finding out that the monolith makes un-documented calls to a legacy mainframe or local file share).
- **Cost Optimization Target:** You analyze the <mark style="background: #FFB86CA6;">actual CPU/Memory utilization data to right-size your target AWS resources</mark>, ensuring you don’t provision expensive over-allocated cloud resources based on raw on-prem capacity.

### Phase 2: Choosing the Migration Strategy (The 7 Rs)
For an enterprise monolith, you generally execute a hybrid approach combining **Rehost (Lift-and-Shift)** and **Replatform (Lift-Tinker-and-Shift)**.
- **The Database Layer (Replatform):** Do not move a relational database onto a raw cloud VM if you can avoid it. You <mark style="background: #FFB86CA6;">replatform the data tier to **AWS RDS</mark> (Relational Database Service)** or Aurora. This instantly<mark style="background: #BBFABBA6;"> offloads patching, backups, and high-availability configuration to AWS.</mark>
- **The Compute Layer (Rehost or Refactor to Container):** 
	* _Option A (Pure Rehost):_ Move the <mark style="background: #ABF7F7A6;">virtual machine as-is straight to an **Amazon EC2** instance using **AWS Application Migration Service (MGN)**</mark>.
    - _Option B (Container Refactor):_ Package the <mark style="background: #D2B3FFA6;">monolithic application into a **Docker** image and deploy it on  **Amazon EKS (Elastic Kubernetes Service)**</mark> to achieve container orchestration and immutability right away.

### Phase 3: Data Migration and Synchronization
The biggest risk <mark style="background: #FFB8EBA6;">during cutover is data loss or extended downtime</mark> due to massive database sizes.

```
[On-Prem Database] ──(AWS Schema Conversion Tool)──> [AWS RDS Database]
         │                                                    ▲
         └──(Continuous Replication via AWS DMS)──────────────┘
```

- **The Execution Pipeline:** 
	1. **AWS SCT (Schema Conversion Tool):** If you are changing database engines (e.g., migrating from an on-prem commercial database to open-source PostgreSQL on RDS), use <mark style="background: #ADCCFFA6;">SCT to convert schemas, views, and stored procedures</mark>. 
	2. **AWS DMS (Database Migration Service):** <mark style="background: #ABF7F7A6;">Run a full data load from the on-prem database to AWS RDS, followed by **Change Data Capture (CDC)** mode</mark>. DMS continuously streams active on-prem database transactions to AWS over a secure connection, keeping the cloud database completely in sync with live production.
    

### Phase 4: Traffic Routing and Cutover
Once data replication lag drops to near zero, you <mark style="background: #FFB86CA6;">execute the production cutover using a zero-downtime routing strategy</mark>.

- **The Traffic Control (Amazon Route 53):** You configure <mark style="background: #ADCCFFA6;">**Amazon Route 53** using a **Weighted Routing Policy**.</mark>
- **The Execution:** You shift <mark style="background: #D2B3FFA6;">5% of DNS traffic over to the newly deployed AWS stack, keeping 95% on-prem.</mark> You monitor cloud logs (**Amazon CloudWatch**) and application metrics. If tracing reveals anomalies, Route 53 switches 100% of traffic back to the on-prem data center instantly. If the cloud environment is stable, you step up the weights sequentially (25% -> 50% -> 100%) until the migration is finalized.

### 💡 Accenture Interview Articulation

When the interviewer asks how you handle a cloud migration, summarize it using this system-level language:

> _"When migrating an on-premises monolith to the cloud, I follow a strict four-phase framework centered on minimizing downtime and managing dependency risk. I leverage **AWS Application Discovery Service** to map network and system dependencies first. For the migration strategy, I prefer to separate the tiers: rehosting the monolithic compute layer into **Docker containers on Amazon EKS or ECS**, while replatforming the data storage layer directly to **Amazon RDS**. I utilize **AWS Database Migration Service with Change Data Capture** to maintain live, real-time synchronization between on-prem and cloud. Finally, I coordinate a zero-downtime cutover using **Amazon Route 53 weighted routing**, allowing us to execute a controlled canary deployment of live traffic and maintain an instant fallback pathway if anomalies are detected."_