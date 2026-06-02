# SPRING BATCH CORE ARCHITECTURE & BULK PROCESSING

When you replace legacy Mainframe JCL batch workflows, **Spring Batch** is your industry-standard target framework. As a Solution Architect, you use Spring Batch to design high-throughput, fault-tolerant, and stateful data pipelines that run on standard JVM container runtimes.

## 🏗️ 1. The Core Architecture Blueprint

Spring Batch is built on a clear runtime hierarchy. Every batch process is decoupled into distinct layers managed by a persistent metadata database.

```
 ┌─────────────────────────────────────────────────────────┐
 │                   JobLauncher                           │
 └────────────────────────┬────────────────────────────────┘
                          │ Triggers
                          ▼
 ┌─────────────────────────────────────────────────────────┐
 │                      Job                                │
 └────────────────────────┬────────────────────────────────┘
                          │ Consists of
                          ▼
 ┌─────────────────────────────────────────────────────────┐     ┌────────────────┐
 │                     Step (1 to N)                       │ ──► │  JobRepository │
 └────────────────────────┬────────────────────────────────┘     │   (Metadata DB)│
                          │ Can be either                          └────────────────┘
                          ▼
           ┌──────────────────────────────┐
           │     Execution Strategy       │
           └──────┬────────────────┬──────┘
                  │                │
                  ▼                ▼
         ┌────────────────┐ ┌──────────────┐
         │ Chunk-Oriented │ │   Tasklet    │
         └────────────────┘ └──────────────┘
```

- **`JobLauncher`:** The entry point interface that bootstraps and triggers a `Job` based on specific `JobParameters` (e.g., `accountingDate=2026-05-29`).
    
- **`Job`:** A configuration entity representing an entire end-to-end batch workflow. It acts as an explicit container for one or many sequential or conditional steps.
    
- **`Step`:** An independent, isolated phase of a batch execution. A step contains all the configuration required to perform actual processing.
    
- **`JobRepository`:** The persistent engine of Spring Batch. It maps execution states into physical tracking tables (e.g., `BATCH_JOB_EXECUTION`, `BATCH_STEP_EXECUTION_CONTEXT`). This gives the application native **stateful restartability** out of the box, tracking exactly which records were committed so failed jobs can resume right where they broke.
    

## ⚙️ 2. Execution Strategies: Chunk-Oriented vs. Tasklet

When designing a `Step`, you select your execution strategy based on the nature of the business task.

### A. Chunk-Oriented Processing (High-Volume Data Streaming)

This is the standard pattern used to replace core Mainframe record-processing steps. It reads, processes, and writes data in tightly managed transactional boundaries called **Chunks**.

```
  Loop until Data Source is empty:
 ┌─────────────────────────────────────────────────────────┐
 │ 1. ItemReader    ──► Reads 1 single item                 │
 └─────────────────────────────────────────────────────────┘
 │ 2. ItemProcessor ──► Transforms/Validates 1 single item │
 └─────────────────────────────────────────────────────────┘
  Iterate and accumulate items in memory until [ Chunk Size / Commit Interval ] is met.
                          │
                          ▼
 ┌─────────────────────────────────────────────────────────┐
 │ 3. ItemWriter    ──► Bulk Inserts/Updates the Chunk      │
 └─────────────────────────────────────────────────────────┘
  Transaction COMMITTED to DB | State saved to JobRepository
```

1. **`ItemReader`:** Streams records sequentially from a data source (e.g., `JdbcPagingItemReader` for databases, or a file reader parsing legacy schemas). It reads exactly **one item** at a time.
    
2. **`ItemProcessor`:** Contains your pure business logic layer. It receives a single item from the reader, applies transformations, executes validations, and returns the modified item. If the processor returns `null`, the item is filtered out and skipped.
    
3. **`ItemWriter`:** Receives a clustered list of items (the accumulated Chunk) and performs a bulk write operation (e.g., `JdbcBatchItemWriter` executing a single batched database statement).
    

> **The Architectural Benefit:** If you set a commit interval (Chunk Size) of `5,000`, Spring Batch handles exactly 5,000 read-and-process cycles in memory before opening a single database transaction, executing a batch write, and committing. This minimizes network overhead and prevents log saturation.

### B. Tasklet Processing (Single-Focused Task)

A `Tasklet` is an interface with a single method: `execute()`. It is designed for simple, non-streaming, transactional operations that occur before or after main data processing.

- **Common Use Cases:** Cleansing an input staging database table, sending an alert notification email, checking if an expected source file exists on a secure server, or calling an external initialization endpoint.
    

## ⚡ 3. Enterprise Bulk Processing & Performance Tuning

To match or exceed Mainframe batch speeds, you must move beyond basic single-threaded configurations using clear optimization patterns:

### A. Multi-Threaded Step Execution

By default, steps run in a single thread. You can optimize this by injecting a `TaskExecutor` into your chunk-oriented configuration. This instructs Spring Batch to spin up a managed thread pool where different threads handle separate chunks concurrently, scaling processing capacity across the underlying CPU cores.

### B. Parallel Steps

If your workflow dependency analysis shows that `Step_A` (processing trade accounts) and `Step_B` (processing consumer logs) are completely independent, you can configure your `Job` definition to execute these steps in parallel on separate threads, maximizing system utilization.

### C. Partitioning (Horizontal Scaling)

This is the pattern used to handle millions of transactions efficiently. Instead of a single application container processing a massive database table linearly, a **Master Step** queries the minimum and maximum primary keys. It then calculates distinct key ranges and assigns them to independent **Worker Steps**. These worker nodes run in parallel across distributed server clusters or container pods, slicing a massive database workload into independent, concurrent pipelines.

## 🎯 Architecture Panel Defense Script

> **Interviewer:** _"How does Spring Batch work, and how do you design a Spring Batch pipeline to process millions of subledger records within a strict time window?"_
> 
> **Your Script:**
> 
> *"Spring Batch operates on a structured architecture managed by a persistent **JobRepository**, which natively tracks processing states to guarantee out-of-the-box restartability.
> 
> To handle millions of financial records, I avoid simple Tasklets and implement a **Chunk-Oriented processing strategy**. I tune the commit interval, or chunk size, dynamically to balance JVM memory footprint against database logging overhead. For example, processing records in chunks of 5,000 allows us to bundle data transfers efficiently via a `JdbcBatchItemWriter`.
> 
> To meet tight processing windows, I move away from single-threaded constraints by implementing **Step Partitioning**. The master step calculates distinct data ranges based on index bounds and splits the workload across multiple parallel worker threads or distributed containers running concurrently.
> 
> Finally, I pair this with custom **Skip and Retry Policies** tied to an `ItemProcessListener`. If an isolated data error occurs, the pipeline isolates and routes that malformed payload to a database error table without triggering an expensive, system-wide transaction rollback, maintaining continuous, high-throughput execution."*