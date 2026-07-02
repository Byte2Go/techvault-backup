## The Core Problem of the Migration
In a monolithic database, **Service A** and **Service B** are hard-linked at the data layer by database **Foreign Keys (FK)**. The <mark style="background: #ABF7F7A6;">database engine automatically prevents data corruption by rejecting any invalid data writes</mark>.

<mark style="background: #FFB86CA6;">When moving to a Database-per-Service model, these databases will live on completely separate physical servers across a network.</mark> <mark style="background: #FFB8EBA6;">Because a database cannot enforce a Foreign Key constraint across a network</mark>, ==**you must migrate the responsibility of data validation from the Database Engine up to the Application Code.**==

## The Golden Rule of Database Migration

> **Never separate your physical infrastructure at the same time you change your application logic.** If you drop database rules and move to separate servers simultaneously, any network failure or application bug will result in immediate, catastrophic data corruption. You must divorce the data **logically** before you divorce it **physically**.

## Step 1: Logical Schema Isolation (The Boundary Phase)
The first step isolates the data structures while keeping them inside the exact same physical database cluster.


```
               SHARED DATABASE SERVER (SINGLE INSTANCE)
       ┌───────────────────────────────────────────────────────┐
       │  ┌─────────────────────────┐   ┌───────────────────┐  │
       │  │       SCHEMA A          │   │     SCHEMA B      │  │
       │  │ (Tables for Service A)  │   │(Tables for Serv B)│  │
       │  └───────────▲─────────────┘   └─────────▲─────────┘  │
       └──────────────┼───────────────────────────┼────────────┘
                      │                           │
              [ DB Credentials A ]        [ DB Credentials B ]
                      │                           │
              ┌───────┴───────┐           ┌───────┴───────┐
              │   SERVICE A   │           │   SERVICE B   │
              └───────────────┘           └───────────────┘
```

- **Action:** Group related tables into separate logical boundaries (**Schema A** and **Schema B**) inside the same database engine instance.
- **Enforcement:** Restrict connection credentials. Configure **Service B**'s database user so it is strictly locked into **Schema B**. It loses direct write permissions to **Schema A**.
- **Current Status of the Rule:** ==The physical **Database Foreign Key (FK)** constraint between the schemas remains **fully active** and enforced== by the database engine.

## Step 2: Dual-Mode Reads & Application Guard (The Safety Net Phase)
This is the phase where you train the application layer to handle data validation while using the database engine as a fallback shield.

### 1. Write Path (The Application Guard)
You rewrite the code for **Service B**. Before it executes a write operation to its own schema, it must now perform ==a network API call to **Service A** to verify if the corresponding record exists.==

### 2. Read Path (The Dual-Mode Test)
To verify that this new application network check is stable, you configure **Dual-Mode Reads**. When validating data, the application checks _both_ avenues simultaneously:
- **Path 1:** It executes the new network API call to the other service.
- **Path 2:** It utilizes direct database read access (sighting) to query the other schema's table directly on the local server.
- The application compares both results in the logging system to identify latency or discrepancies.

### 3. Data Protection (The Safety Net)
**The Database Foreign Key constraint is NOT deleted yet.** It acts as a shield. If your new network API code contains a bug and mistakenly approves a write for data that does not exist, the <mark style="background: #FFB86CA6;">underlying database Foreign Key will catch the error at the execution level and violently block the transaction</mark>. Your data remains completely uncorrupted.

```
 1. Mutation Request ──► [ Service B Application Code ]
                                     │
                                     ▼
                     Runs Dual-Validation on READS
                     ├──► Check 1: Direct DB Query (Sight)
                     └──► Check 2: Network API Call to Service A
                                     │
       If BOTH match and validate ───┴──► 2. Execute WRITE to DB
                                                    │
                 [ SAFETY NET ACTIVE ] ─────────────┼──► If API logic failed, 
                                                    ▼    Database FK blocks the write here!
                                            [ Database Shield ]
```

## Step 3: Constraint Removal (The Promotion Phase)
<mark style="background: #BBFABBA6;">Once your production logs show a 100% accuracy match between your application network validation checks and the database direct checks</mark> over millions of transactions, the software code is officially trusted.
- **Action:** Execute an `ALTER TABLE ... DROP CONSTRAINT` command on the database server to delete the physical Foreign Key rule.
- **Result:** The database engine safety guard is gone. The application code is now the primary line of defense protecting data integrity.

## Step 4: Physical Separation (The Infrastructure Phase)
Because the application code has successfully operated without a database-enforced Foreign Key for an extended testing period, the services are fully decoupled.

```
        DATABASE SERVER A                        DATABASE SERVER B
 ┌──────────────────────────────┐         ┌──────────────────────────────┐
 │          SCHEMA A            │         │          SCHEMA B            │
 │   (Tables for Service A)     │         │   (Tables for Service B)     │
 └──────────────▲───────────────┘         └──────────────▲───────────────┘
                │                                        │
        ┌───────┴───────┐  3. Network API Call   ┌───────┴───────┐
        │   SERVICE A   │◄───────────────────────┤   SERVICE B   │
        └───────────────┘                        └───────────────┘
```

- **Action:** Physically migrate **Schema B** off the shared database instance and onto its own completely isolated, dedicated database server instance. Update the connection strings in **Service B**.
- **Result:** Cross-database foreign keys are now structurally impossible. However, the system moves to this target state with **zero downtime or data corruption** because the application layer was already fully trained to handle validation.

## Core Takeaways to Remember
- **The Role of the FK in Step 2:** It acts as an automated fallback safety net while testing new network validation logic against live production traffic.
- **The Risk of Early Removal:** Dropping the constraint before testing the network logic allows unvalidated or orphaned rows to slip past your code, corrupting the data store.
- **The Trigger for Server Separation:** Infrastructure separation should only occur after the database constraints have been dropped and your application logs prove the code successfully maintains consistency on its own.