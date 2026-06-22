## 1. Grounding the Problem Statement in Global Logistics

### The Scan-IT Phoenix Problem Statement:

> _"Operating across 35+ countries, global logistics teams using Phoenix face a deluge of high-volume, unstructured operational emails (e.g., claims, payment delays, urgent cargo tracking updates). ==Manually triaging these emails into Phoenix workflow queues creates massive operational friction==, delays container release times, and spikes administrative costs. We need a secure, event-driven ==AI Automation Pipeline natively embedded into the Phoenix framework== to auto-categorize, scrub, and summarize these global communications instantly."_


- **The Ingestion:** Event-driven. MS Graph API hooks into Outlook $\rightarrow$ alerts AWS API Gateway $\rightarrow$ triggers a short Lambda function $\rightarrow$ grabs the full email payload $\rightarrow$ drops it safely into an **Amazon SQS Queue** as a buffer.
- **The Security:** The **AI Worker** pulls the email from SQS inside a private, secure network (VPC). It runs it through Amazon Comprehend to mask names/passports (PII) before any AI sees it, keeping Scan-IT 100% compliant with global laws.
- **The Memory (RAG):** If it's a brand new thread, it's a **Cold Start**—the AI processes it fresh. The system then embeds and saves that text into a **Vector DB (Amazon OpenSearch)**. If it's an existing thread, the Vector DB pulls the last 3 interactions so the AI has context.
- **The Inference:** The Worker bundles the email + context into a template and hands it to **Anthropic Claude 3.5 Sonnet** via AWS Bedrock (with an enterprise contract ensuring our data is never used for training). Claude fills out a strict JSON form with the **Category**, **Summary**, and **Confidence Score**.
- **The Safety Net (HITL):** If Claude's confidence score is high ( $\ge 85\%$ ), it auto-updates the Phoenix Oracle DB and pushes to the EMAN dashboard. If it's low ( $< 85\%$ ), it safely routes it to a manual queue for the `Customer_GM` to review.

## 2. The Tech Stack: Leveraging Scan-IT's AWS + Oracle Footprint

Since Scan-IT already uses a **hybrid cloud model with AWS and Oracle**, you must pick tools that align seamlessly with their current IT infrastructure. Present this exact architecture:

| **Architectural Layer**  | **Chosen Tool / Service**                                     | **Architectural "Why" & Phoenix Integration**                                                                                                                                        |
| ------------------------ | ------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **Ingestion**            | **[[MS Graph API]] + AWS Lambda**                             | Securely hooks into the corporate Outlook/Exchange servers. Lambda scale-to-zero compute ensures minimal idle costs.                                                                 |
| **Data Orchestration**   | **AWS Step Functions**                                        | Handles the business logic. If an email classification confidence is low, ==Step Functions safely routes the payload to the Phoenix **Human-in-the-Loop (HITL)** UI.==               |
| **AI Processing (LLM)**  | **Anthropic Claude 3.5 Sonnet** (via AWS Bedrock)             | Claude has a massive context window and ==excels at complex reasoning==, making it ideal for reading long, multi-turn global shipping and logistics email threads.                   |
| **Vector DB (RAG)**      | **Amazon OpenSearch Serverless** (or Oracle AI Vector Search) | Stores vector embeddings of historical shipping tickets and manifest data. This allows the AI to reference past transaction context instantly.                                       |
| **Operational Database** | **Oracle Database / Autonomous**                              | Since Phoenix relies on Oracle, ==the final structured metadata (Category, Summary, Customer ID)== is written directly back to Oracle tables to update Phoenix records in real-time. |
| **Analytical Dashboard** | **AWS QuickSight or embedded Oracle APEX**                    | Pulls from the operational DB to show real-time inflow/outflow metrics directly inside the ==Phoenix administrative dashboard.==                                                     |

## 3. How the RAG Framework works within Logistics

When a customer emails about a delayed shipment, the AI shouldn't just summarize the text. It needs to know _what_ that customer shipped previously.
1. **Ingestion:** A customer sends an email: _"Container tracking ID #49201 is stuck at port."_
2. **Vector Search:** The system converts the text into a vector embedding and queries the Vector DB to retrieve past tracking issues, historical claims, or client-specific SLAs for that account.
3. **Prompt Augmentation:** The system bundles the **Current Email** + **Historical Logistics Context** + **Current System Manifests**.
4. **Contextual Summary:** Claude 3.5 processes it and outputs: _"Category: Claim / Cargo Delay. Summary: Client is disputing port storage fees for Container #49201 due to a customs hold. Historical Context shows this happened twice last month with the same carrier."_

## 4. The Phoenix Dashboard: Inflow vs. Outflow

Because Scan-IT provides software to make lives simple, the dashboard needs to cleanly display logistics throughput by category. You will track:

### **Inflow Metrics (What is hitting the global logistics queues)**
- **Volume by Operational Category:** Visualized via real-time charts separating incoming mail into `claim_summary`, `payment_summary`, `freight_quote`, or `customs_delay`.
- **Global Origin Inflow:** Geo-maps tracking email volume spikes across different shipping regions (e.g., APAC, Europe, Americas).

### **Outflow Metrics (How the Phoenix AI is executing automated tasks)**
- **Straight-Through Processing (STP) Rate:** The percentage of logistics emails handled entirely by the AI without human intervention.
- **HITL Escalation Rate (The Safety Net):** Emails failing confidence thresholds that get pushed to the manual `Customer_GM / HIT_GM` queue within Phoenix for human validation.
- **SLA Reduction Trackers:** Time saved processing documents compared to manual back-office data entry.

## 5. Enterprise Security & Privacy for Global Shipping

Operating in 35+ countries means navigating strict data sovereignty laws (like Europe's GDPR or Singapore's PDPA).

- **Zero-Data-Retention Compliance:** Because we deploy via **AWS Bedrock**, we invoke enterprise data isolation. The ==logistics data is encrypted via Customer-Managed Keys (KMS)==, and Anthropic/AWS are legally restricted from using Scan-IT's global data to train public models.
- **Data Sanitization Layer:** Before sending raw emails to the LLM, an enterprise PII scrubbing filter (like ==_Amazon Comprehend_==) sanitizes sensitive shipping information, masking personal passport numbers, commercial credit cards, or private home addresses while preserving critical metadata like tracking IDs.
