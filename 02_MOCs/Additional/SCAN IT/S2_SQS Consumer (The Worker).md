The emails are now sitting safely inside the **Amazon SQS Queue** as independent, raw JSON messages, waiting to be processed.

The very next step is pulling that message out of the queue using a dedicated worker. Here is how that specific handoff works.

## The SQS Consumer (The Worker)

We introduce a new component called the **AI Processor Worker** (this can be another AWS Lambda function or a lightweight container running on AWS ECS Fargate).

```
[Amazon SQS Queue] 
       │
       │ (1) Polling Trigger
       ▼
[AI Processor Worker] ──► (Next step: Security Scrubbing)
```

### 1. Polling the Message

The SQS queue doesn't actively "push" the data to the AI. Instead, our **AI Processor Worker** constantly watches (polls) the queue.

- When a message is available, the worker pulls it down.
- **The Visibility Timeout:** The moment the worker pulls an email, SQS temporarily "hides" that email from the rest of the system for a few minutes. This guarantees that if multiple workers are running, two workers never process the exact same email at the same time.

### 2. Why decouple here? (The Architect's Choice)

If the interviewer asks, _"Why didn't you just let the first Ingestion Lambda send the email straight to the AI?"_

Your answer is **Rate Limiting and Cost**:

- Large Language Models (like Anthropic Claude or Gemini) have strict API rate limits (e.g., you can only send them a certain number of words or requests per minute).
- Global shipping traffic is unpredictable. If 500 emails hit Scan-IT's inbox in one single minute during a port crisis, our SQS queue acts as a buffer. The ==AI Processor Worker can pull them out at a controlled, steady pace== (e.g., 50 emails per minute), ensuring we never crash or get blocked by the AI provider.