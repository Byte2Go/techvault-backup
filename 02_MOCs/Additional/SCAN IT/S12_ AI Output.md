You are thinking exactly like an architect. You cannot hand raw, conversational human text to a downstream software application like **Phoenix**; the code will break. You need the model to output a machine-readable data contract—specifically, a structured **JSON object** with a fixed schema.

To achieve this, modern LLMs (like Claude 3.5 Sonnet on Bedrock or Gemini 1.5 Pro on Vertex AI) support a feature called **Structured Outputs** or **JSON Mode**. When you activate this, the model is mathematically restricted from outputting conversational filler (like _"Sure, here is your summary:"_). It _only_ outputs clean JSON.

Here is exactly how you specify the output format, the required fields, and how your AI Worker uses them to make the routing decision.

## 1. Specifying the Fixed Schema

When the AI Worker calls the LLM, it passes a strict **System Prompt** along with the data. It defines the exact keys and data types expected.

JSON

```
{
  "email_category": "string (MUST be exactly one of: claim_summary, payment_summary, tracking_update)",
  "confidence_score": "float (a decimal between 0.00 and 1.00)",
  "summary_bullets": "array of strings (exactly 3 bullet points summarizing the core issues)",
  "requires_immediate_action": "boolean (true or false)"
}
```

## 2. What the Raw Model Response Looks Like

Because **JSON Mode** is enabled, the LLM responds with a clean block of data that your AI Worker can parse natively into code:

JSON

```
{
  "email_category": "payment_summary",
  "confidence_score": 0.94,
  "summary_bullets": [
    "Customer is disputing late fee invoice #INV-9921.",
    "Shipper claims payment was delayed due to a port clearance issue in Singapore.",
    "Requested a waiver based on historical SLA agreements."
  ],
  "requires_immediate_action": true
}
```

## 3. How the AI Worker Evaluates the Output (The Logic)

Once the worker receives this JSON, it acts as the **Decision Router**. It uses the `confidence_score` field to execute your business logic programmatically.

Python

```
import json

# 1. Parse the string response from the LLM into a Python Dictionary
ai_output = json.loads(llm_response_string)

# 2. Extract the variables
category = ai_output["email_category"]
confidence = ai_output["confidence_score"]
summary = ai_output["summary_bullets"]

# 3. Architectural Routing Decision (The Gatekeeper)
CONFIDENCE_THRESHOLD = 0.85

if confidence >= CONFIDENCE_THRESHOLD:
    # PATH A: AUTOMATED FLOW (High Confidence)
    # Write directly to Phoenix Oracle DB and push to the live dashboard
    phoenix_db.save_transaction(category=category, summary=summary, status="AUTOMATED")
    dashboard.update_inflow_metrics(category=category)
else:
    # PATH B: HUMAN-IN-THE-LOOP (Low Confidence)
    # Route to the exception queue for manual triage by Customer_GM
    phoenix_db.save_transaction(category=category, summary=summary, status="PENDING_REVIEW")
    hitl_queue.push_to_manager(reason="Low AI Confidence Score")
```

## 💡 How to Present This Structure in the Interview

If the panel asks, _"How do you ensure the LLM output doesn't break the Phoenix backend?"_

Give them this precise technical response:

> _"We enforce strict **Structured Outputs (JSON Mode)** at the API layer with Claude/Gemini. We pass a fixed JSON schema containing four mandatory keys: `email_category`, `confidence_score`, `summary_bullets`, and an urgency flag. Because the output is deterministic JSON, our AI Worker can natively parse the payload. It extracts the `confidence_score` and runs a simple conditional threshold check: anything $\ge 0.85$ is written straight to our production Oracle tables for the Phoenix dashboard; anything below $0.85$ is shunted to a dead-letter queue for Human-in-the-Loop validation by the Customer GM."_

This ties the model's behavior directly back to your business requirements and standard backend code engineering!