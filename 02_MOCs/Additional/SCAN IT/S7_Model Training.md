When you consume models on **AWS Bedrock** via an API, you are using a **pre-trained model** (like Anthropic Claude 3.5 Sonnet). Because these models are already incredibly smart out of the box, you do not need to do massive "training" like data scientists do.

Instead, as an AI Architect, you use **two primary industry methods** to "train" the model on how to categorize your emails:

## Method 1: Prompt Engineering with Few-Shot Learning (The Default)

Instead of changing the model's actual code or parameters, you "train" it dynamically every time you send an API call by providing instructions and examples in the system prompt. This is called **Few-Shot Prompting**.

You write code in your **AI Worker** that sends a highly structured template to the Bedrock API:

Plaintext

```
System Prompt: 
You are the automated email routing engine for Scan-IT's Phoenix logistics platform. 
Your job is to read an inbound email and output a strict JSON category.

Available Categories:
- claim_summary: Used when a client disputes fees, reports damage, or requests compensation.
- payment_summary: Used for invoice questions, remittance advice, or payment updates.
- tracking_update: Used when asking about container status, port arrivals, or ETA.

Here are examples of how to categorize (Few-Shot Training):
Example 1: "Where is my container?" -> {"category": "tracking_update"}
Example 2: "I am disputing this $400 storage fee" -> {"category": "claim_summary"}
Example 3: "Please find attached the receipt for last week's invoice" -> {"category": "payment_summary"}

Now categorize the following email:
[USER EMAIL]: "{Sanitized Email Text}"
```

### Why this works:

LLMs excel at pattern matching. By passing 3 to 5 perfect examples inside the prompt text, you have effectively "trained" the model on your specific categorization business logic for that specific API call.

## Method 2: Custom Model Fine-Tuning (The "Architect" Level)

If your email categories are highly complex, use company-specific jargon, or change constantly, prompt engineering might not be accurate enough. This is where you perform **Fine-Tuning** inside AWS Bedrock.

You are not training a model from scratch. You are taking a base model (like Claude) and blending your specific data into its top layer.

```
[500 Historical Emails + Verified Categories] ──► Upload to AWS S3 (JSONL format)
                                                              │
                                                              ▼
[Base Claude 3.5 Model] ──────► [AWS Bedrock Fine-Tuning Job] ──────► [Your Custom Fine-Tuned Model]
```

### The 3-Step Fine-Tuning Pipeline:

1. **Prepare the Training Data:** Collect 500 to 1,000 historical logistics emails. Manually have your team verify the correct category for each. Convert this data into a special text file format (`.jsonl`) and upload it to an **Amazon S3 bucket**.
    
2. **Execute the Bedrock Job:** In the AWS Bedrock console or via an AWS SDK script, you trigger a "Model Customization Job." You point Bedrock to your S3 folder and say: _"Train this base model using this training dataset."_
    
3. **Deploy the Custom Model Endpoint:** AWS Bedrock runs the training in the background. It tweaks the model’s internal weights to highly align with your logistics terminology. When it finishes, it gives you a unique, private API endpoint (e.g., `provisioned-model-arn:scan-it-phoenix-v1`).
    

## Setting the Hyperparameters (Output Consistency)

Whether you choose Method 1 or Method 2, you must configure the **Hyperparameters** in your Bedrock API request to ensure the categorization is consistent and never "hallucinates."

When your AI Worker calls the Bedrock API, you will pass these strict structural parameters:

- **`Temperature = 0.0`**: This is the absolute most important parameter. Setting temperature to `0` removes all creativity from the model. It forces the model to be completely deterministic—meaning if you pass the exact same email twice, it will give you the exact same category every single time.
    
- **`Max Tokens = 100`**: Since a category is just a single word or a small JSON object, you cap the output length so the model doesn't start rambling or generating unnecessary conversational text.
    

### 💡 Your Final 3 PM Interview Soundbite:

> _"To train our model on email categorization via AWS Bedrock, we use a two-tiered architectural strategy. For Day 1, we implement **Few-Shot Learning** via advanced prompt engineering, injecting 3 to 5 highly specific logistics examples directly into the system prompt and setting the API `Temperature` parameter to `0.0` for maximum deterministic consistency. If our taxonomy expands or requires deeper domain-specific pattern recognition, we will transition to an **asynchronous Fine-Tuning pipeline**. We will store a curated dataset of 1,000 historically classified emails in Amazon S3 and execute a Bedrock customization job to deploy a highly specialized, private version of the model tailored exclusively to Scan-IT's operations."_

