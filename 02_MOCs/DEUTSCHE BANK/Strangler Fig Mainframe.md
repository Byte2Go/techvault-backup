This is a classic architecture panel question. The interviewers want to see if you actually know how a Mainframe operates in the real world, or if you are just throwing out cloud buzzwords like "API Gateway."

You are completely right: a traditional Mainframe batch feed cannot natively talk to a standard HTTP REST API Gateway. Mainframes process files via sequential JCL jobs, not web requests.

To apply the **Strangler Fig Pattern** to a legacy-fed environment, you don't change the Mainframe; you intercept the data **before** it reaches the Mainframe, or you use a **Message Broker** as your "Ingestion Layer Bridge."

Here are the three real-world architectural patterns for how a Mainframe feed goes through a phased parallel run.

## 🏗️ Pattern 1: Intercepting at the Source (Upstream Decoupling)

Instead of letting an external system (like a retail banking platform or a third-party vendor) dump a flat file directly onto the Mainframe's local storage (DASD) via FTP, you change the ingestion entry point.

```
                  [ Upstream System / File Producer ]
                                  │
                                  ▼
                     ┌──────────────────────────┐
                     │    API Gateway / Kafka   │  <-- New Ingestion Layer
                     └────────────┬─────────────┘
                                  │
         ┌────────────────────────┴────────────────────────┐
         ▼                                                 ▼
┌──────────────────┐                              ┌──────────────────┐
│ AWS S3 / Oracle  │                              │ Mainframe FTP /  │
│  (Target Cloud)  │                              │ Secure Landing   │
└──────────────────┘                              └──────────────────┘
```

- **How it works:** You direct the upstream sender to push the transaction file to a secure modern landing zone (like AWS S3 or an API Gateway file-upload endpoint).
    
- **The Fork:** A lightweight routing service or cloud function instantly duplicates that file. It forwards one copy to your new Java/Cloud environment, and simultaneously drops the other copy into the Mainframe’s traditional landing directory via automated SFTP.
    
- **The Result:** Both systems get the exact same feed at the same time without the Mainframe ever knowing a cloud environment exists.
    

## ✉️ Pattern 2: The Message Broker Bridge (IBM MQ / Kafka)

Most modern banking Mainframes use **IBM MQ** to communicate asynchronously with the outside world. This is your primary integration channel for a Strangler Fig pattern.

```
       [ Legacy Mainframe Ingestion Feed / Nightly Processing ]
                                  │
                                  ▼
                       ┌────────────────────┐
                       │    IBM MQ Series   │
                       └──────────┬─────────┘
                                  │
         ┌────────────────────────┴────────────────────────┐
         ▼                                                 ▼
┌──────────────────┐                              ┌──────────────────┐
│ IBM MQ Listener  │                              │  Kafka Connect   │
│  (COBOL Batch)   │                              │ (Java/Spring App)│
└──────────────────┘                              └──────────────────┘
```

- **How it works:** When the initial Mainframe JCL feed processes its input, instead of writing output directly to an isolated, local flat file, it drops the transaction messages onto an **IBM MQ queue**.
    
- **The Fork:** You attach a **Kafka Connect IBM MQ Source Connector** to that queue. This connector automatically streams every single message written by the Mainframe out to an enterprise Kafka topic in real time.
    
- **The Result:** Your new Spring Boot or Spring Batch applications consume the data live from Kafka, executing parallel "shadow processing" in lockstep with the Mainframe batch.
    

## 📊 Pattern 3: Database-Level Change Data Capture (CDC)

If the legacy Mainframe system cannot be modified to send files elsewhere or write to queues, you intercept the data at the database storage layer using **Change Data Capture (CDC)**.

```
┌──────────────────────────────────────────────────────────────────┐
│                        MAINFRAME RUNTIME                         │
│                                                                  │
│  [ Legacy JCL Feed ] ──► Writes to ──► [ Mainframe DB2 Database] │
└──────────────────────────────────────────────────────────────────┴
                                                 │
                                                 │ Reads Database Logs
                                                 ▼
                                      ┌────────────────────┐
                                      │  CDC Engine (IBM)  │
                                      └──────────┬─────────┘
                                                 │ Streams Deltas
                                                 ▼
                                      ┌────────────────────┐
                                      │    Apache Kafka    │
                                      └──────────┬─────────┘
                                                 │
                                                 ▼
                                      ┌────────────────────┐
                                      │ Spring Boot / Batch│
                                      └────────────────────┘
```

- **How it works:** The Mainframe receives its traditional file feed through its existing legacy channels and processes it normally, updating its local DB2 database tables.
    
- **The Fork:** A non-intrusive CDC tool (like IBM InfoSphere DataStage or Debezium) sits outside the application layer and reads the DB2 transaction logs directly. The microsecond a row is inserted or updated by the Mainframe JCL, the CDC tool captures that delta change and publishes it as an event to Kafka.
    
- **The Result:** Your Java Spring Boot application consumes these change events from Kafka and runs its own calculations or writes to Oracle, achieving parallel dual-running without altering a single line of Mainframe JCL code.
    

## 🎯 Architecture Panel Defense Script

> **Interviewer:** _"You mentioned an API Gateway for a Strangler Fig migration, but our feeds are entirely Mainframe batch-file based. How can a Mainframe batch feed pass through an API Gateway?"_
> 
> **Your Script:**
> 
> *"That is an excellent point, and to clarify, for a heavy backend batch architecture, a standard HTTP API Gateway is indeed the wrong tool for the direct feed. For file and queue-driven workloads, my ingestion layer bridge relies on **Upstream Interception** and **Change Data Capture (CDC)**.
> 
> Instead of modifying the legacy Mainframe code, we introduce an asynchronous event broker, like **Apache Kafka paired with IBM MQ**, to act as our data hub.
> 
> If we cannot change where the upstream files land, we position a **CDC engine** on the Mainframe DB2 database logs. The legacy JCL processes its file feed exactly as it does today. The moment it commits a financial transaction to DB2, our CDC agent captures that log delta asynchronously and streams it via Kafka to our cloud landing zone. This enables our modern Spring Batch application to process the identical transaction dataset in shadow mode. We achieve a flawless, real-time parallel run without introducing network latency or altering the core Mainframe infrastructure."*