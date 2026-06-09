Hibernate is not just an tool that writes SQL for you; it is a <mark style="background: #D2B3FFA6;">**state-management engine** that bridges memory (Java objects) and disk (database rows).</mark>

When production systems crash or slow down under heavy load, **90% of the time it is because a developer treated Hibernate like a basic utility without understanding <mark style="background: #ADCCFFA6;">how it manages memory, caching, and database connections under the hood.**</mark>

## 1. Entity Mapping Fundamentals (`infrastructure/persistence/`)

### What to Use Here (With Code Snippet)
This is your **JPA Entity**. Remember our foundation: this is an **`ENTITY + NON_POJO`**. It exists strictly to <mark style="background: #FFB86CA6;">map data to database tables</mark>, and it belongs entirely in the `infrastructure/persistence/` package.

```Java
package com.company.orderservice.infrastructure.persistence;

import jakarta.persistence.*;
import java.util.ArrayList;
import java.util.List;

@Entity // 1. Registers this class with Hibernate's state engine
@Table(name = "orders") // 2. Maps this class directly to a physical database table
public class OrderJpaEntity {
    
    @Id
    @GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "order_seq")
    @SequenceGenerator(name = "order_seq", sequenceName = "order_id_seq", allocationSize = 50)
    private Long id;
    
    @Column(name = "status", nullable = false)
    private String status;
    
    // 3. One order has many lines. Always default to LAZY fetching.
    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL, fetch = FetchType.LAZY, orphanRemoval = true)
    private List<OrderLineJpaEntity> lines = new ArrayList<>();
    
    @Version // 4. Activates Optimistic Locking protection
    private Long version;

    // Getters, setters, and mapping methods to convert to/from Core Domain Objects
}
```

### The Architectural Blueprint & "Why" Behind the Settings
- **`allocationSize = 50` (The ID Performance Booster):** 
	* _The Problem:_ If you use `GenerationType.IDENTITY`, your database must generate the ID for every single insert. <mark style="background: #FFB8EBA6;">This means Hibernate is forced to make a physical network trip to the database _for every single row_ you save</mark>, completely destroying batch processing.
    - _The Architect's Fix:_ By using a database sequence with `allocationSize = 50`, Hibernate makes **one network call** to reserve a block of 50 IDs. <mark style="background: #BBFABBA6;">It hands those IDs out in local memory for the next 50 inserts</mark>. This reduces your database network traffic by **98%**.

- **`FetchType.LAZY`:** 
	* _The Rule:_ **Never, under any circumstances, use `FetchType.EAGER`.** <mark style="background: #FFB8EBA6;">Eager fetching means whenever you load an `Order`, Hibernate automatically generates a heavy join query to load all associated lines, customers, and data</mark>—even if you only needed to check the order's status. It causes massive, silent memory consumption.

## 2. <mark style="background: #FFB86CA6;">MUST READ</mark>: [[8_Hibernate_Spring_Integration]]

## 4. Transaction Management & Propagation

When an <mark style="background: #ADCCFFA6;">application service calls another service, you must define how their database transactions interact.</mark> We do this via the `@Transactional(propagation = ...)` property.

### The Two Critical Propagation Types You Must Know

| **Propagation Type**       | **How it Behaves**                                                                                                       | **Real-World Use Case**                                                                                                                                                                                                               |
| -------------------------- | ------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **`REQUIRED`** _(Default)_ | If a transaction is already open, join it. If no transaction exists, create a brand-new one.                             | **Standard Operations:** Placing an order, updating a profile, adding items. Everything succeeds or fails as one atomic block.                                                                                                        |
| **`REQUIRES_NEW`**         | Always suspends any existing outer transaction and ==spins up a completely isolated, independent database transaction.== | **Audit Logs / Security Auditing:** If a user tries to transfer money and the transaction fails due to insufficient funds, the main transaction rolls back—but your audit log entry _must_ still write to disk to record the attempt. |

### Code Example: `REQUIRES_NEW` in Action
```Java
@Service
public class AuditService {
    private final AuditRepository auditRepository;

    @Transactional(propagation = Propagation.REQUIRES_NEW) // Independent lifecycle
    public void logSystemEvent(String message) {
        AuditEntity log = new AuditEntity(message);
        auditRepository.save(log);
    }
}
```

## 5. Transaction Isolation Levels (Data Integrity)
Isolation levels dictate how isolated your transaction is from changes happening concurrently in other database connections.

|**Level**|**Dirty Reads**|**Non-Repeatable Reads**|**Phantom Reads**|
|---|---|---|---|
|**`READ_COMMITTED`** _(PostgreSQL Default)_|❌ Prevented|Allowed|Allowed|
|**`REPEATABLE_READ`**|❌ Prevented|❌ Prevented|Allowed|

- **Dirty Read:** <mark style="background: #FF5582A6;">Your transaction reads uncommitted changes written by another transaction that is currently running.</mark> If that other transaction crashes and rolls back, your data becomes completely corrupted.
- **Non-Repeatable Read:** You read a row once. Another transaction modifies that row and commits it. <mark style="background: #FF5582A6;">You read the exact same row again, and the data has magically changed underneath you.</mark>

### Architect Recommendation
For standard web apps, stick to the database default (**`READ_COMMITTED`**). For high-integrity financial operations where values must not change mid-flight while a service calculates balances, elevate the isolation level:

```Java
@Transactional(isolation = Isolation.REPEATABLE_READ)
public void processFinancialSettlement() { ... }
```

## 6. Locking Strategies: Optimistic vs. Pessimistic
When multiple users try to modify the exact same database row at the exact same moment, you must protect your data from overwrites.

### Strategy 1: Optimistic Locking (Preferred for 95% of Applications)
- **How it works:** It assumes collisions are rare. It uses a `@Version` counter column in your table.
- **The Mechanics:**
    1. User A and User B both read an order with `version = 5`.
    2. User A clicks save first. Hibernate runs:
        `UPDATE orders SET status = 'PAID', version = 6 WHERE id = 1 AND version = 5;` (Success!)
    3. User B clicks save a second later. Hibernate runs:
        `UPDATE orders SET status = 'CANCELLED', version = 6 WHERE id = 1 AND version = 5;`
    4. Since User A already changed the version to 6, User B's update modifies **0 rows**. Hibernate catches this and throws an `OptimisticLockException`. User B is told: _"This data was updated by someone else, please refresh."_

### Strategy 2: Pessimistic Locking (Used for High-Contention / Must-Win Scenarios)
- **How it works:** It assumes collisions will happen. It locks the database row immediately upon reading it, forcing everyone else to wait in a queue.
- **The Mechanics:**

Java

```
@Lock(LockModeType.PESSIMISTIC_WRITE) // Triggers a native SQL "SELECT ... FOR UPDATE"
@Query("SELECT o FROM OrderJpaEntity o WHERE o.id = :id")
Optional<OrderJpaEntity> findByIdForUpdate(@Param("id") Long id);
```

- **The Impact:** The moment this query runs, the database physically locks that row. If another user attempts to read or modify this order, their execution thread pauses and waits until your transaction completely finishes processing and commits. Use this _only_ for ultra-critical steps like ticket inventory bookings or banking balance deductions.

## What NOT to Use Here (With Reasoning)
To keep your persistence layer performing efficiently, ensure these annotations and practices never appear:

- **Never use `@Service` or `@RestController` in this package.**
    - _Reasoning:_ <mark style="background: #FFF3A3A6;">This package is reserved for physical infrastructure adapters.</mark> <mark style="background: #FFB8EBA6;">Business coordination logic must never be mixed into database row mapping structures</mark>.

- **Never use `@GeneratedValue(strategy = GenerationType.IDENTITY)` for high-throughput batch insert applications.**
    - _Reasoning:_ As discussed, identity generation completely disables Hibernate's internal batch inserts capability, causing severe database performance bottlenecks.
- **Never use `@Transactional` on your entity data structures themselves.**
    - _Reasoning:_ Transactions dictate the lifecycles of business use cases and operations, which are orchestrated by the Application services. Data entities are passive data structures and have no authority over connection lifecycles.