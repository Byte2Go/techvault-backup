Executing real-time or nightly data reconciliation between **Mainframe DB2** and **Target Oracle databases** during a dual-run migration is a critical component of financial system governance. Financial subledgers have zero tolerance for mathematical deviation; a single rounded penny can cause compliance issues for Germany-region auditing structures.

As a Solution Architect, you design a highly scalable, automated **Reconciliation Pipeline** separate from both data layers. This approach handles millions of daily records without impacting operational batch processing windows.

## 🏗️ The 3-Tier Reconciliation Architecture

Rather than performing slow, resource-heavy database connections across your network, you structure reconciliation using asynchronous chunk processing and hashing patterns.

### Tier 1: Asynchronous Log Extraction

- **The Mainframe Side:** At the completion of the Mainframe batch run, or via ongoing Change Data Capture logs, transactions are pulled from DB2. Instead of streaming raw tables over the network, you use high-speed database utilities to extract a snapshot of the day's entries into an optimized CSV format.
    
- **The Java/Oracle Side:** Similarly, your Spring Batch worker services finish their processing run and generate an equivalent transaction file extracted directly from Oracle.
    
- **The Landing Zone:** Both extraction files are dropped asynchronously into a secure, shared cloud landing directory, such as an AWS S3 bucket or an enterprise file cluster.
    

### Tier 2: The Reconciliation Engine (Spring Batch)

You deploy a dedicated **Spring Batch Reconciliation Service**. This engine acts as an independent validator, processing data using a **Streaming Hash/Key Comparison Pattern**:

```
 ┌─────────────────────────────────────────────────────────┐
 │               Spring Batch Recon Engine                 │
 └────────────────────────────┬────────────────────────────┘
                              │ Streams Both Files By:
                              ▼
 ┌─────────────────────────────────────────────────────────┐
 │     Key Index Component: Account_ID + Transaction_ID    │
 └────────────────────────────┬────────────────────────────┘
                              │ Generates & Compares
                              ▼
                ┌───────────────────────────┐
                │ MD5 / SHA-256 Record Hash │
                └─────────────┬─────────────┘
                              │
               ┌──────────────┴──────────────┐
               ▼ Match                       ▼ Mismatch / Break
      ┌─────────────────┐           ┌──────────────────┐
      │ Mark reconciled │           │ Route to DB      │
      │  in metadata    │           │ Exception Table  │
      └─────────────────┘           └──────────────────┘
```

1. **Composite Key Indexing:** The `ItemReader` opens both streams simultaneously, sorting records by a unique business composite key (e.g., `Account_ID` + `Transaction_ID`).
    
2. **Deterministic Hashing:** For every record, the engine builds a string string containing all core financial variables (`Amount`, `Currency_Code`, `Value_Date`, `Booking_Status`). It computes a fast cryptographic hash (like MD5 or SHA-256) of that string.
    
3. **Hash Verification:** The processor evaluates whether `Mainframe_Hash == Oracle_Hash`.
    
    - **If it matches:** The records are identical. The pipeline passes without action.
        
    - **If it breaks (Mismatch):** The record is isolated.
        

### Tier 3: Break Identification & Exception Handling

- **Missing Records (Orphans):** If a key exists in DB2 but not in Oracle, the reconciliation logs an **Omission Break**.
    
- **Value Deviations (Variances):** If the key exists in both but hashes mismatch, it logs a **Value Break** showing the exact column divergence (e.g., DB2 Balance = `1500.50`, Oracle Balance = `1500.51`).
    
- **The Reporting Table:** All breaks are written to a dedicated relational database Exception Table, feeding an operational dashboard accessible by the business and engineering teams.
    

## ⚡ Engineering Optimizations for High-Volume Ledger Audits

Running database comparisons on millions of rows can easily degrade network performance if poorly configured. You use specific engineering practices to keep execution lean:

### A. Two-Phase Reconciliation (Aggregates First)

To avoid scanning millions of rows every single night, implement a two-phase check:

- **Phase 1 (The Balance Sheet Check):** Run a high-speed aggregation query on both DB2 and Oracle to compare master sums grouped by localized region or accounting book (e.g., `SELECT System_Code, SUM(Amount) FROM Ledger GROUP BY System_Code`).
    
- **Phase 2 (The Deep Dive):** If the total sum balances align perfectly to the penny, you can bypass individual row validations. You only trigger the line-by-line streaming hash comparison if Phase One flags a variance in a specific account segment, saving massive compute cycles.
    

### B. Managing Floating Point Discrepancies

The most common cause of false-positive breaks during dual-runs is structural type mapping mismatches. If the Mainframe stores data in packed decimals (`COMP-3`) and the Java application processes it using standard primitives, minor precision variations occur. You prevent this by ensuring the reconciliation engine normalizes all values to `java.math.BigDecimal` scales before performing hash generation.

## 🎯 Architecture Panel Defense Script

> **Interviewer:** _"When running a parallel dual-run architecture with data in both DB2 and Oracle, how do you mathematically prove that the two systems are perfectly synchronized? Walk me through your reconciliation mechanism."_
> 
> **Your Script:**
> 
> *"To handle reconciliation without risking database lockups or network timeouts, I avoid heavy, direct synchronous database joins between DB2 and Oracle. I implement a decoupled, asynchronous **Two-Phase Reconciliation Framework** managed by a dedicated Spring Batch validator.
> 
> In Phase One, we execute high-speed aggregate sum queries across both databases at the end of the batch cycle. If the total balances match perfectly by ledger category, the run is verified.
> 
> If a variance is detected, Phase Two triggers an automated line-by-line **Streaming Hash Comparison**. We stream data from both systems into an isolated landing zone, sorting the datasets by unique composite business keys. The reconciliation engine generates deterministic cryptographic hashes of the financial fields for each record and matches them.
> 
> Any mismatches or missing entries are captured as Value or Omission breaks and written directly to an operations dashboard for analysis. This approach ensures that our shadow Java ecosystem remains accurate down to the penny across an entire month-end close before we begin decommissioning the legacy mainframe structures."*