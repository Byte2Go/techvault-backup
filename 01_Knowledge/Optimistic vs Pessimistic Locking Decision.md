In a high-throughput enterprise application, data integrity degradation rarely happens when a single user is accessing a record. It happens <mark style="background: #FFB86CA6;">when **multiple concurrent threads** attempt to read and modify the exact same database row at the same millisecond.</mark>

As an Enterprise Architect, <mark style="background: #ABF7F7A6;">choosing between **Optimistic Locking** and **Pessimistic Locking** is a critical structural decision.</mark> It establishes <mark style="background: #D2B3FFA6;">how your system handles resource competition</mark>, <mark style="background: #FFF3A3A6;">dictates thread utilization inside your HikariCP connection pool, and determines your application's transaction</mark> throughput under heavy corporate workloads.

### 1. The Unified Context: The High-Volume Balance Ledger
To maintain strict architectural continuity across our execution playbook, we will analyze these locking strategies using our core asset: a **`Wallet` entity** tracking corporate funds where concurrent balance updates occur continuously.

```Java
package com.enterprise.finance.wallet.domain;

import jakarta.persistence.*;
import java.math.BigDecimal;

/**
 * ============================================================================
 * ARCHITECTURAL DESIGN PATTERN: CONCURRENCY LOCKING REGIMEN
 * ============================================================================
 * This entity serves as the foundation for examining concurrency strategies.
 * Depending on the chosen runtime lock mode, it will either leverage application-level version checking or force native kernel-level database row locks.
 * ============================================================================
 */
@Entity
@Table(name = "corporate_wallet")
public class Wallet {

    @Id
    @SequenceGenerator(name = "wallet_seq", sequenceName = "seq_wallet_id", allocationSize = 50)
    @GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "wallet_seq")
    private Long id;

    @Column(name = "account_number", nullable = false, unique = true)
    private String accountNumber;

    @Column(name = "balance", nullable = false)
    private BigDecimal balance;

    // 💡 OPTIMISTIC LOCKING ENGINE: Required for Version-based conflict detection
    @Version
    @Column(name = "version_num")
    private Long version;

    // Standard Constructors, Getters, and Setters
    public Wallet() {}

    public Wallet(String accountNumber, BigDecimal balance) {
        this.accountNumber = accountNumber;
        this.balance = balance;
    }

    public Long getId() { return id; }
    public String getAccountNumber() { return accountNumber; }
    public BigDecimal getBalance() { return balance; }
    public void setBalance(BigDecimal balance) { this.balance = balance; }
    public Long getVersion() { return version; }
}
```

### 2. Optimistic Locking (Application-Level Guardrails)
<mark style="background: #ADCCFFA6;">Optimistic Locking operates on the assumption that data conflicts are **rare**</mark>. <mark style="background: #FFB86CA6;">It completely avoids placing physical locks on the database rows</mark>, <mark style="background: #BBFABBA6;">allowing multiple concurrent transactions to read and modify the data simultaneously without blocking each other's threads.</mark>

#### The Underlying Mechanics: The `@Version` Property
Optimistic locking is managed entirely in application memory by Hibernate, relying on the `@Version` column mapped inside your entity.

##### The Execution Lifecycle:
1. **Thread 1** reads Wallet record #7. The current balance is `$1,000` and the `version_num` is `1`.
2. **Thread 2** reads Wallet record #7 at the exact same millisecond. It also sees a balance of `$1,000` and a `version_num` of `1`.
3. Thread 1 finishes its business calculation first, updating the balance to `$1,200`. When committing, Hibernate executes an atomic verification query:
    ```SQL
    UPDATE corporate_wallet SET balance = 1200, version_num = 2 WHERE id = 7 AND version_num = 1;
    ```
The database updates exactly 1 row. The commit succeeds, and the version increments to `2`.

4. Thread 2 finishes its calculation next, attempting to update the balance to `$1,500`. Hibernate issues its commit update query:
    ```SQL
    UPDATE corporate_wallet SET balance = 1500, version_num = 2 WHERE id = 7 AND version_num = 1;
    ```

5. **The Collision:** Because Thread 1 already changed the row's `version_num` to `2`, Thread 2's query matches **0 rows**.
6. **The Result:** <mark style="background: #FFF3A3A6;">Hibernate detects that no rows were updated, immediately rolls back Thread 2's transaction, and throws an</mark> **`OptimisticLockException`** (wrapped as a Spring `ObjectOptimisticLockingFailureException`) up the execution stack.

#### Architect's Remediation Pattern: Asynchronous Retry
When an optimistic collision happens, <mark style="background: #FFB86CA6;">your application must handle the failure gracefully</mark>. The standard architectural solution is <mark style="background: #BBFABBA6;">intercepting the exception using an AOP aspect or Spring Retry configurations to automatically re-read the fresh version and try again</mark>:

```Java
@Service
public class WalletService {

    @Autowired private WalletRepository repository;

    // 💡 ARCHITECT PATTERN: Automatically retries the transaction if an optimistic collision occurs
    @Retryable(
        retryFor = { ObjectOptimisticLockingFailureException.class },
        maxAttempts = 3,
        backoff = @Backoff(delay = 50)
    )
    @Transactional
    public void creditWallet(String accountNum, BigDecimal amount) {
        Wallet wallet = repository.findByAccountNumber(accountNum);
        wallet.setBalance(wallet.getBalance().add(amount));
        // No explicit save needed due to dirty checking; version check occurs on flush
    }
}
```

### 3. Pessimistic Locking (Kernel-Level Database Guardrails)
<mark style="background: #FFB86CA6;">Pessimistic Locking operates on the assumption that data conflicts are **highly likely**</mark>. Instead of waiting for the commit phase to check for changes, <mark style="background: #D2B3FFA6;">it aggressively blocks other connections at the database kernel level the moment data is read</mark>.

#### The Underlying Mechanics: Database Lock Modes
When your repository executes a query flagged with a pessimistic lock, Spring Data JPA instructs Hibernate to append database-specific locking syntax directly to the SQL generation stream (such as `FOR UPDATE` in Oracle/DB2/PostgreSQL).

```Java
@Repository
public interface WalletRepository extends JpaRepository<Wallet, Long> {

    // 💡 ARCHITECT SELECTION: Locks the row at the DB engine level immediately upon reading
    @Lock(LockModeType.PESSIMISTIC_WRITE)
    @Query("SELECT w FROM Wallet w WHERE w.accountNumber = :accountNumber")
    Wallet findByAccountNumberWithPessimisticLock(@Param("accountNumber") String accountNumber);
}
```

##### The Execution Lifecycle:
1. **Thread 1** executes the query with `PESSIMISTIC_WRITE`. Hibernate transmits the query down to the database:

    ```SQL
    SELECT id, balance, version_num FROM corporate_wallet WHERE account_number = 'ACC-7' FOR UPDATE;
    ```
2. The database kernel places an **Exclusive Row-Level Lock** on that row.
3. **Thread 2** attempts to read or update the exact same account row. The database kernel intercepts Thread 2 and **suspends its execution thread entirely**, forcing it to wait in a queue.
4. Thread 1 safely completes its business rules, alters the balance, flushes the change to disk, and terminates its `@Transactional` boundary.
5. The database transaction releases the exclusive row lock.
6. Thread 2's suspended connection automatically wakes up, takes its own exclusive lock on the newly updated row, and proceeds with its execution block safely.

#### The Operational Threat: Connection Pool Starvation
<mark style="background: #D2B3FFA6;">While Pessimistic locking guarantees strict data safety without forcing retry logic</mark>, it introduces a severe architectural bottleneck.

Because <mark style="background: #FFF3A3A6;">Thread 2 is physically suspended waiting for Thread 1 to finish, its active Java thread and its **HikariCP database connection remain completely blocked and unavailable**</mark>. If 100 concurrent requests hit the same hot customer wallet simultaneously, your entire connection pool will saturate instantly, causing cascading system latency spikes and timing out unrelated application endpoints.

### 4. The Architect's Decision Matrix: When to choose which?
To maintain absolute system predictability, architects evaluate the locking strategy using a clear set of operational tradeoffs:
#### Choose Optimistic Locking When:
- **Low Conflict Rates:** The business pattern shows that the probability of two threads targeting the exact same record simultaneously is low (e.g., users updating their own profile details).
- **High Horizontal Scalability Requirements:** You are <mark style="background: #BBFABBA6;">deploying to cloud-native, auto-scaling clusters</mark> where blocking database connections introduces severe system bottlenecks.
- **Read-Heavy Workloads:** The transaction profile is $90\%$ reads and only $10\%$ writes.

#### Choose Pessimistic Locking When:
- **High Conflict Rates / Hotspots:** Multiple parallel systems are constantly contending for the exact same rows (e.g., flash sales, high-frequency ledger processing, inventory allocation systems).
- **High Cost of Failure:** The business logic cannot tolerate retrying an operation (e.g., processing large, multi-step wire transfers where re-running an entire workflow introduces high financial risk).

### 5. Architectural Evaluation Matrix

| **Technical Metric**         | **Optimistic Locking (@Version)**                                                                 | **Pessimistic Locking (FOR UPDATE)**                                                                         |
| ---------------------------- | ------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------ |
| **Enforcement Boundary**     | **Application Layer** (Managed in JVM memory by Hibernate).                                       | **Database Kernel Layer** (Managed directly by Oracle / DB2 storage engine).                                 |
| **Thread State Profile**     | **Non-Blocking.** Threads run concurrently; failures are thrown at the very end during the flush. | **Blocking.** Concurrent threads are physically suspended, waiting in a database hardware queue.             |
| **Connection Pool Overhead** | **Low.** Connections are utilized efficiently and released quickly.                               | **High.** Risks immediate HikariCP pool starvation under heavy concurrent hotspot spikes.                    |
| **Failure Cost Engine**      | Requires explicit handling via **Application Retry Blocks** to recover from version mismatches.   | Resolves conflicts automatically via **Sequential Execution**, eliminating application-level error catching. |
| **SQL Performance Profile**  | Highly efficient. Statements remain standard, basic query operations.                             | Appends heavy locking clauses (`FOR UPDATE`), which can bypass optimizer plans if used carelessly.           |
