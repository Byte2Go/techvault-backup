The ingestion layer is designed as a secure, decoupled, event-driven architecture that bridges Microsoft Exchange with the Scan-IT AWS ecosystem without relying on legacy polling protocols.

```
[Outlook Server] ──(Webhook Event)──► [AWS API Gateway] ──► [AWS Lambda]
                                                               │
 [Amazon SQS Queue] ◄──(Pushes Full JSON)── [MS Graph API] ◄───┘
```

### 1. Webhook Registration & Handshake

We expose a secure **AWS API Gateway URL** (`[https://gateway.aws.scanit.com](https://gateway.aws.scanit.com)`) to serve as our public webhook listener. A one-time registration and cryptographic handshake are established between Microsoft Graph API and AWS to establish mutual trust.

### 2. Event Trigger & Lambda Activation

The exact millisecond a global logistics email arrives in the monitored Outlook inbox, Microsoft Exchange fires a lightweight HTTP POST notification to our API Gateway. This notification contains only basic event metadata—specifically the `subscriptionId` and the unique `message_id`. API Gateway immediately invokes an ephemeral **AWS Lambda Ingestion Function**.

### 3. Token Acquisition & Secure Pull

Because the initial notification does not contain the actual email body, the Lambda function executes a secure back-channel call.

- First, Lambda authenticates with **Azure Active Directory (Azure AD)** via **OAuth 2.0** client credentials to obtain a temporary, high-security Access Token.
- Second, armed with this token, Lambda makes a direct HTTPS `GET` request back to the **MS Graph API URL** using the extracted `message_id`.

### 4. Payload Isolation in SQS
Microsoft Graph API responds to Lambda with the complete, rich JSON payload containing the sender, timestamps, attachments, and raw email body text. Finally, Lambda takes this full payload and drops it into an **Amazon SQS Queue** for downstream AI processing, successfully decoupling the ingestion layer from the core AI engine.

### 💡 Why this wording wins the interview:

By framing it this way, you prove to the panel that you understand **enterprise security** (OAuth 2.0, Azure AD trust), <mark style="background: #D2B3FFA6;">**cost optimization** (ephemeral Lambda instead of 24/7 running servers)</mark>, and **system resilience** (decoupling via SQS)