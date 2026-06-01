<mark style="background: #ABF7F7A6;">While database isolation levels define how concurrent transactions are hidden from _each other_</mark>, <mark style="background: #FFB86CA6;">**Transaction Propagation** defines how transactions are shared _between your own Java methods_.</mark>

<mark style="background: #FFB8EBA6;">When a transactional Java method invokes another transactional method within your application</mark>, <mark style="background: #FFF3A3A6;">propagation strategies dictate whether the inner method should join the existing database transaction, spin up a completely independent boundary, or reject execution entirely.</mark>

### 1. The Unified Example Engine: The Order Processor & Loyalty Points
To ensure absolute structural clarity, we will track these strategies using a single chronological corporate asset scenario.

We have a primary service method: `OrderService.checkout()`. This method performs core business data manipulation (charging a customer and saving an order record). Inside its execution track, it calls an auxiliary service method: `LoyaltyService.awardPoints()`, which increments a user’s promotional reward balance.

### Strategy 1: `Propagation.REQUIRED` (The Enterprise Default)

#### The Mechanics & Lifecycle Context
This is Spring's default strategy. It states: _"<mark style="background: #FFB86CA6;">If an active transaction already exists on the executing thread, I will join it natively.</mark> If no transaction exists, I will open a brand-new one for myself."_

- **The Step-by-Step Scenario:**
    1. A user clicks buy. `OrderService.checkout()` is invoked. Spring opens a database connection and starts **Transaction 1**.
    2. The code updates stock levels and saves the order.
    3. `checkout()` internally invokes `LoyaltyService.awardPoints()`, <mark style="background: #FFB86CA6;">which is configured as `REQUIRED`.</mark>
    4. _The Engine Action:_ Spring detects that **Transaction 1** is already active on the thread. Instead of creating a new connection, <mark style="background: #FFB86CA6;">it merges `awardPoints()` directly into **Transaction 1**</mark>.
    5. Suddenly, the loyalty points database insert crashes due to a unique constraint violation.
    6. **The Result:** Because both methods share the exact same transaction boundary, the entire operation fails. **Transaction 1 is rolled back completely.** The loyalty points are not awarded, and the customer's order record is erased from the database.
- **Best Used For:** <mark style="background: #BBFABBA6;">95% of all standard corporate workflows where all database writes must stand or fall together as a singular, atomic unit of work.</mark>

### Strategy 2: `Propagation.REQUIRES_NEW` (The Isolated Branch)

#### The Mechanics & Lifecycle Context
This strategy states: _"<mark style="background: #ADCCFFA6;">I must run inside my own independent transaction boundary</mark>. If a transaction is already running, suspend it, open a completely separate connection for me, and resume the original transaction once I finish."_ [[Proxy Interception Constraint]]

- **The Step-by-Step Scenario:**
    1. `OrderService.checkout()` begins execution and opens **Transaction 1**.
    2. The code saves the order record successfully.
    3. `checkout()` invokes `LoyaltyService.awardPoints()`, which is configured as `REQUIRES_NEW`.
    4. _The Engine Action:_ <mark style="background: #FFB8EBA6;">Spring pauses **Transaction 1** and holds its connection open. </mark> <mark style="background: #FFF3A3A6;">It goes back to the connection pool (e.g., HikariCP), checks out a _second_ connection, and opens a completely separate **Transaction 2** for the loyalty method.</mark>
    5. `awardPoints()` executes its SQL statements, finishes successfully, and hits **COMMIT** on **Transaction 2**. <mark style="background: #FF5582A6;">The loyalty points are now permanently saved to physical disk.</mark>
    6. Control returns to `checkout()`. Spring wakes up **Transaction 1**.
    7. Suddenly, the network drops, and `checkout()` crashes before completing. **Transaction 1 rolls back.** The customer's order record is wiped clean.
    8. **The Result:** The order is gone, but <mark style="background: #FF5582A6;">the customer **still keeps the loyalty points** because **Transaction 2** was completely independent and already committed</mark>.
- **Best Used For:** System audit logging, payment gateway history logging, or security tracking metrics <mark style="background: #BBFABBA6;">where you must write a record to the database even if the main business transaction crashes and rolls back.</mark>

### Strategy 3: `Propagation.MANDATORY` (The Strict Dependent)
#### The Mechanics & Lifecycle Context
This strategy states: _"I am a helper method that cannot manage myself. An active transaction must already exist before you call me. If you call me without a transaction, I will throw an exception instantly."_
- **The Step-by-Step Scenario:**
    1. A backend batch job calls `LoyaltyService.awardPoints()` directly from an un-annotated scheduler method (No active transaction).
    2. _The Engine Action:_ Spring's proxy intercepts the call, scans the execution thread, and finds zero active database boundaries.
    3.<mark style="background: #FFB8EBA6;"> Instead of executing any SQL or opening a connection, Spring instantly halts the thread</mark> and throws an `IllegalTransactionStateException`.
- **Best Used For:** Sensitive low-level financial balancing methods or account ledger reconciliation sub-routines that are dangerous to run as naked standalone queries outside of a parent orchestration process.

### Strategy 4: `Propagation.SUPPORTS` (The Chameleon)
#### The Mechanics & Lifecycle Context
This strategy states: _"I am completely flexible. If a transaction is already open, I will ride along inside it. If no transaction exists, I will run as a plain, non-transactional Java method."_
- **The Step-by-Step Scenario:**
    1. A reporting controller calls a data-fetching method inside `LoyaltyService` configured with `SUPPORTS` to display a user profile. No transaction is active. The method executes fast as a standard JDBC read operation.
    2. Later, `OrderService.checkout()` (which has an active transaction) calls that same loyalty data-fetching method. The method immediately joins the active transaction, gaining full transactional visibility to uncommitted data changes made by the checkout process.
- **Best Used For:** Read-only search or lookup methods that are shared between transactional write-heavy layers and non-transactional read-only web layers.

### 2. Definitive Blueprint Comparison Matrix

Use this master reference matrix to map runtime propagation behaviors:

|**Propagation Rule**|**Existing Transaction Present?**|**No Existing Transaction Present?**|**Connection Pool Utilization**|**Architectural Use Case**|
|---|---|---|---|---|
|**`REQUIRED`**|Joins existing transaction.|Opens a brand-new transaction.|Reuses current connection / allocates 1 if empty.|**Enterprise Baseline Standard.** Regular CRUD data manipulation methods.|
|**`REQUIRES_NEW`**|Suspends existing transaction; opens independent boundary.|Opens a brand-new transaction.|**Allocates 2 concurrent connections** from the pool simultaneously.|Centralized auditing systems, system log tables, notification event recording.|
|**`MANDATORY`**|Joins existing transaction.|Throws `IllegalTransactionStateException`.|Reuses current connection / Fails before allocation.|High-risk sub-routines that require an explicit parent container boundary to avoid data leakage.|
|**`SUPPORTS`**|Joins existing transaction.|Runs non-transactionally without any boundary.|Reuses current connection / Uses 0 transaction overhead.|Optimization for dual-use data retrieval methods shared across read and write layers.|

### 3. Production Spring Configurations
To implement these strategies in code, pass the `propagation` property into the annotation header.

_CRITICAL CODE REMINDER:_ As established in our Transaction Basics notes, <mark style="background: #ADCCFFA6;">for propagation attributes to work, the methods **must live in separate class files** to prevent the self-invocation proxy bypass loophole!</mark>

#### Step A: The Isolated Audit Log Service (`REQUIRES_NEW`)
```Java
package com.corporate.service;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

@Service
public class AuditLogService {

    // ALWAYS WRITES TO DISK: Even if the ordering process fails later, this log must be preserved!
    @Transactional(propagation = Propagation.REQUIRES_NEW, rollbackFor = Exception.class)
    public void logTransactionAttempt(String detail) {
        // Uses an independent connection pool allocation
        jdbcTemplate.update("INSERT INTO system_audit_logs (log_text) VALUES (?)", detail);
    }
}
```

#### Step B: The Primary Checkout Service (`REQUIRED`)
```Java
package com.corporate.service;

import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Propagation;
import org.springframework.transaction.annotation.Transactional;

@Service
public class OrderService {

    private final AuditLogService auditLogService;
    private final OrderRepository orderRepository;

    public OrderService(AuditLogService auditLogService, OrderRepository orderRepository) {
        this.auditLogService = auditLogService;
        this.orderRepository = orderRepository;
    }

    @Transactional(propagation = Propagation.REQUIRED, rollbackFor = Exception.class)
    public void checkout(Order order) {
        // 1. Logs the attempt. Hits the proxy -> suspends checkout transaction -> commits log permanently!
        auditLogService.logTransactionAttempt("User attempting purchase for order ID: " + order.getId());
        
        // 2. Core Business Logic (Runs inside the main transaction)
        orderRepository.save(order);
        
        // If this method throws an error right here, the order is safely rolled back, 
        // but the system_audit_log entry written in Step 1 remains perfectly intact on disk!
    }
}
```
