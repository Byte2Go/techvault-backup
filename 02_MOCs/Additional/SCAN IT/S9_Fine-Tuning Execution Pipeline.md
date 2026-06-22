When you need a permanent change to the model's inner brain, you move from prompt engineering to **Fine-Tuning**.

Here is the exact step-by-step execution blueprint for how you would take Scan-IT's historical 10,000 emails and permanently "bake" that knowledge into a model like **Claude 3.5** (via AWS Bedrock) or **Gemini 1.5** (via Vertex AI).

## The 4-Step Fine-Tuning Execution Pipeline

```
[10k Raw Emails] ──► [1. Data Prep (JSONL)] ──► [2. Cloud Upload] ──► [3. Training Job (LoRA)] ──► [4. Evaluation & Baseline Model-2]
```

### Step 1: Data Preparation & Formatting (The Most Crucial Step)

You cannot just upload raw `.eml` files or text documents into a training engine. You must convert your 10,000 historical emails into a strictly structured format called **JSONL (JSON Lines)**. Each line in this file represents a single training conversation.

For a classification and summarization model, you must format every single record to show the model the **Input** it will receive and the exact **Expected Output**:

JSON

```
{"system": "You are the Phoenix Logistics Agent. Classify and summarize the email.", "user": "Container 49201 is stuck at the terminal again due to custom holds.", "assistant": "{\"category\": \"claim_summary\", \"summary\": [\"Container 49201 delayed at terminal.\", \"Reason: Customs hold.\"]}"}
```

> **Architect Note:** You will split your 10,000 records into two groups:
> 
> - **Training Set (80% / 8,000 records):** What the model actively learns from.
>     
> - **Validation Set (20% / 2,000 records):** What the system uses to test the model during training to make sure it's actually getting smarter.
>     

### Step 2: Uploading to Cloud Infrastructure

You upload your finalized `.jsonl` files into an enterprise-controlled cloud storage bucket:

- **AWS Stack:** Upload to an **Amazon S3** bucket.
    
- **Google Cloud Stack:** Upload to a **Google Cloud Storage (GCS)** bucket.
    
- _Security Check:_ Ensure this bucket is locked down via IAM roles so no external party can access Scan-IT's proprietary emails.
    

### Step 3: Triggering the Fine-Tuning Job (PEFT / LoRA)

You don't write custom neural network code from scratch. You log into your cloud console (AWS Bedrock or Google Vertex AI) and initiate a **Parameter-Efficient Fine-Tuning (PEFT)** job, usually using a technique called **LoRA (Low-Rank Adaptation)**.

- **How it works:** Instead of altering all billions of parameters in the base model (which costs millions of dollars), LoRA freezes the original model and attaches a small, highly specialized "layer" of parameters on top. This new layer learns the specific vocabulary, patterns, and output formatting of Scan-IT's logistics data.
    
- **Hyperparameters you set:**
    
    - **Epochs:** How many times the model reads the entire dataset (typically 3–5 times).
        
    - **Learning Rate:** How drastically the model changes its weights when it makes a mistake.
        

### Step 4: Evaluation and Baselining (Creating "Model-2")

As the training job runs, the cloud platform continuously tests the model against your 2,000 validation records. It compares the model's guesses against your ground-truth expected outputs.

- **The Metrics:** The system tracks **Loss** (how wrong the model is). You want to see the loss curve drop smoothly and flatten out.
    
- **The Baseline:** Once the training job finishes successfully, the cloud provider compiles a brand new, custom cryptographic endpoint for you. This is your **Model-2 (The Baseline Model)**.
    

## How the AI Worker Uses "Model-2" Post Go-Live

Once Model-2 is deployed, the day-to-day workflow becomes incredibly efficient:

1. An email arrives in SQS.
    
2. The **AI Worker** pulls it and routes it to your custom **Model-2 endpoint**.
    
3. Because the routing rules, logistics categories, and output formats are now permanently hardwired into Model-2's brain, you no longer need to pass large examples in the prompt.
    
4. Model-2 instantly returns a fast, highly accurate, deterministic JSON response tailored perfectly to the Phoenix software.
    

### 💡 Your 3 PM Interview Soundbite for Fine-Tuning:

> _"When Few-Shot prompting becomes too costly or hits context limitations, we transition to a Parameter-Efficient Fine-Tuning (PEFT/LoRA) strategy. We clean and transform our 10,000 historical logistics emails into a structured JSONL format, mapping user inputs to our explicit ground-truth JSON outputs. We split this into an 80/20 train-validation matrix and execute a fine-tuning job natively within AWS Bedrock or Vertex AI. The output is a highly optimized, domain-specific baseline—Model-2—which minimizes inference latency and guarantees structural consistency without inflating token costs."_