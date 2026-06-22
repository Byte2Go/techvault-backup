Now that the **AI Processor Worker** has pulled the raw email from SQS, <mark style="background: #D2B3FFA6;">we cannot just pass it straight to a Large Language Model.</mark>

Because Scan-IT operates a global logistics software (**Phoenix**) across 35+ countries, we are strictly bound by ==global data privacy laws like Singapore’s **PDPA** and Europe’s **GDPR**==. Shipping emails are messy—they frequently contain personal passport scans for customs clearance, private phone numbers, home addresses, or credit card info.

Here is exactly how the **Security and Sanitization Layer** acts as a compliance firewall before the AI ever sees the data.

## The Security Scrubbing Pipeline

We insert a dedicated security filter—such as **Amazon Comprehend PII** or **Google Cloud DLP (Data Loss Prevention)**—directly into the worker's processing flow.

```
[Raw Email JSON from SQS]
          │
          ▼
   [AI Processor Worker]
          │
          │ (1) Sends raw text payload
          ▼
[Amazon Comprehend PII] ──► (Scans for SSNs, Passports, Names, Cards)
          │
          │ (2) Returns masked, clean string
          ▼
[Sanitized Email Payload] ──► (Ready for the next step: RAG)
```

### 1. Real-Time PII Masking

The worker extracts the raw body text of the email and sends it via an ==API call to the compliance scanner==. The scanner reads the text, identifies sensitive entities, and completely redacts or masks them using ==standard placeholder tags.==

- **Raw Inbound Email Text:**
    > _"Urgent: Release container #49201 for client John Doe. My passport number is S1234567A and my phone is +65 9123 4567."_

- **Sanitized Output Text:**
    > _"Urgent: Release container #49201 for client `[NAME]`. My passport number is `[PASSPORT_NUMBER]` and my phone is `[PHONE_NUMBER]`."_

### 2. Crucial Distinction: What We Keep vs. What We Mask
As an architect, you must point out a critical balance here: **We only mask personal information, not operational logistics metadata.**

- We **do not** mask tracking IDs, container numbers, port codes (like SIN, RTM), or carrier names.
- Why? Because the downstream AI model _needs_ those logistics identifiers to correctly categorize the email and search for historical records.

## The Infrastructure Boundary (Data Isolation)
Beyond redacting the text, an architect must secure the underlying network where the data travels. You achieve this using two hard enterprise boundaries:

1. **VPC Isolation (No Public Internet):** The ==AI Processor Worker, the SQS queue, and the security scanner all live inside Scan-IT’s private **AWS VPC (Virtual Private Cloud)**==. We use **AWS PrivateLink** (private endpoints) so that the data payload travels across isolated, internal cloud networks. It never touches the public internet. => [AWS PrivateLink](https://aws.amazon.com/privatelink/) is a feature of Amazon Virtual Private Cloud (Amazon VPC) that provides private connectivity between VPCs and AWS services. Network traffic that uses PrivateLink doesn't travel over the public internet, which reduces the risk of external threats, such as exposure to brute force and distributed denial-of-service (DDoS) attacks.

2. **Zero Data Retention (ZDR) Contract:** Because we are using ===enterprise-tier foundation model APIs (like Anthropic Claude on AWS Bedrock or Gemini on Vertex AI)==, we invoke strict data privacy terms. Natively, these enterprise gateways guarantee that **our data is encrypted at rest/in transit, <mark style="background: #FFB86CA6;">is never logged or cached by the AI provider, and is strictly legally prohibited from being used to train public models</mark>.**

### 💡 Your 3 PM Soundbite for the Security Layer:

> _"The moment an email is consumed from SQS, it enters our Security and Sanitization Layer. To ensure compliance with global data privacy frameworks like GDPR and PDPA across Phoenix's global footprint, we pass the text through Amazon Comprehend PII to mask personal identifiers like passports and phone numbers, while preserving critical operational metadata like container IDs. Furthermore, by orchestrating this within a private VPC and using AWS Bedrock enterprise endpoints, we enforce a strict Zero Data Retention boundary—ensuring Scan-IT’s logistics data is never leaked or used for public model training."_