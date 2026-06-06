# P2 · Day 3 — Java/Spring Ecosystem · JVM · Hibernate · Concurrency · Testing
**Pillar:** P2 — Java / Spring Ecosystem  
**Role Priority:** Java 🟢 Core · SA 🔵 Supporting · AI ⚪ Supporting  
**Day in Plan:** Day 3 (Week 1)  
**Time:** ~3 hours study + 1 hour Q&A practice

---

## Topic 1 · Spring Boot Microservice Structure & Clean Architecture

### In One Line
A well-structured Spring Boot service separates concerns into layers — each with a single responsibility — so the domain stays pure and infrastructure is swappable.

### Why It Matters
Java Architect interviews always ask: "How do you structure a Spring Boot service?" The wrong answer is "controller → service → repository." The right answer shows you understand why layers exist and how to keep business logic clean.

### Clean Architecture in Spring Boot

```
com.company.orderservice
├── api/                        ← Inbound adapters (REST controllers, gRPC handlers)
│   ├── OrderController.java
│   └── dto/                   ← Request/Response DTOs (never domain objects here)
├── application/               ← Use cases / Application services (orchestration only)
│   ├── PlaceOrderUseCase.java
│   └── command/               ← Command objects
├── domain/                    ← Pure business logic — NO Spring annotations
│   ├── Order.java             ← Aggregate root
│   ├── OrderLine.java
│   ├── Money.java             ← Value object
│   └── OrderRepository.java  ← Interface (port)
├── infrastructure/            ← Outbound adapters (JPA, Kafka, HTTP clients)
│   ├── persistence/
│   │   └── JpaOrderRepository.java
│   ├── messaging/
│   │   └── KafkaOrderEventPublisher.java
│   └── client/
│       └── PaymentServiceClient.java
└── config/                    ← Spring config, beans, security
```

**Dependency rule:** api → application → domain ← infrastructure  
Domain never imports infrastructure. Infrastructure implements domain interfaces.

### Key Spring Boot Annotations (what they actually mean)

| Annotation | Purpose | SA Gotcha |
|---|---|---|
| `@Service` | Marks application/domain service | Don't put it on domain objects — domain is POJO |
| `@Repository` | Marks persistence layer + exception translation | Use on JPA implementations, not domain interfaces |
| `@Transactional` | Wraps method in DB transaction | Only on application services, not domain |
| `@Component` | Generic Spring bean | Avoid overuse — be explicit about layer |
| `@RestController` | HTTP handler + `@ResponseBody` | Controllers = thin; delegate to use case |
| `@ConfigurationProperties` | Type-safe config binding | Prefer over `@Value` for structured config |

### Application Service Pattern
```java
@Service
@Transactional
public class PlaceOrderApplicationService {
    
    private final OrderRepository orderRepository;
    private final CustomerRepository customerRepository;
    private final DomainEventPublisher eventPublisher;
    
    public OrderId placeOrder(PlaceOrderCommand cmd) {
        // 1. Load aggregates
        Customer customer = customerRepository.findById(cmd.customerId())
            .orElseThrow(() -> new CustomerNotFoundException(cmd.customerId()));
        
        // 2. Execute domain logic (domain knows nothing about Spring)
        Order order = customer.placeOrder(cmd.items(), cmd.shippingAddress());
        
        // 3. Persist
        orderRepository.save(order);
        
        // 4. Publish domain events
        eventPublisher.publishAll(order.domainEvents());
        
        return order.id();
    }
}
```

### Spring Security + OAuth2 (brief — full coverage in P4 Day 5)
```java
@Configuration
@EnableWebSecurity
public class SecurityConfig {
    @Bean
    SecurityFilterChain filterChain(HttpSecurity http) throws Exception {
        return http
            .oauth2ResourceServer(oauth2 -> oauth2.jwt(Customizer.withDefaults()))
            .authorizeHttpRequests(auth -> auth
                .requestMatchers("/actuator/health").permitAll()
                .requestMatchers("/api/admin/**").hasRole("ADMIN")
                .anyRequest().authenticated()
            )
            .sessionManagement(s -> s.sessionCreationPolicy(STATELESS))
            .build();
    }
}
```

---

## Topic 2 · JPA / Hibernate Deep Dive

### In One Line
JPA is the abstraction; Hibernate is the implementation — you need to know both to avoid the performance disasters that kill production Java systems.

### Why It Matters
N+1 queries, lazy loading exceptions, transaction boundaries — these are the most common Java Architect interview traps. Every SA with Java depth needs to nail these.

### Entity Mapping Fundamentals

```java
@Entity
@Table(name = "orders")
public class Order {
    
    @Id
    @GeneratedValue(strategy = GenerationType.SEQUENCE, generator = "order_seq")
    @SequenceGenerator(name = "order_seq", sequenceName = "order_id_seq", allocationSize = 50)
    private Long id;
    
    @Column(nullable = false)
    private String status;
    
    @OneToMany(mappedBy = "order", cascade = CascadeType.ALL, 
               fetch = FetchType.LAZY, orphanRemoval = true)
    private List<OrderLine> lines = new ArrayList<>();
    
    @Version  // Optimistic locking
    private Long version;
}
```

**`allocationSize = 50`** — Hibernate pre-allocates 50 IDs in memory; one DB call per 50 inserts (not 1 DB call per insert).

### The N+1 Problem — Most Common Interview Question

**Problem:**
```java
// WRONG — N+1 queries
List<Order> orders = orderRepository.findAll();  // 1 query: SELECT * FROM orders
for (Order o : orders) {
    o.getLines().size();  // N queries: SELECT * FROM order_lines WHERE order_id = ?
}
// If 100 orders → 101 database queries
```

**Fix 1 — JPQL JOIN FETCH:**
```java
@Query("SELECT o FROM Order o JOIN FETCH o.lines WHERE o.status = :status")
List<Order> findWithLinesByStatus(@Param("status") String status);
```

**Fix 2 — EntityGraph:**
```java
@EntityGraph(attributePaths = {"lines", "customer"})
List<Order> findAll();
```

**Fix 3 — @BatchSize (Hibernate-specific):**
```java
@OneToMany(fetch = FetchType.LAZY)
@BatchSize(size = 50)  // Loads 50 collections in one query instead of N
private List<OrderLine> lines;
```

### Lazy Loading — LazyInitializationException

**Problem:** Access lazy association outside a transaction:
```java
// In Service (transaction closes after method returns)
Order order = orderRepository.findById(id).get();
// Transaction closed here
order.getLines().size();  // LazyInitializationException — session closed!
```

**Fix:** Load what you need inside the transaction:
```java
@Transactional(readOnly = true)
public OrderDetailDto getOrderDetail(Long id) {
    Order order = orderRepository.findWithLinesById(id);  // JOIN FETCH in query
    return mapper.toDto(order);  // DTO created inside transaction
}
```

> Rule: **Open Session in View is an anti-pattern** — it hides N+1 problems. Disable it (`spring.jpa.open-in-view=false`).

### Transaction Management

**Propagation types:**
| Propagation | Behavior |
|---|---|
| `REQUIRED` (default) | Join existing tx; create new if none |
| `REQUIRES_NEW` | Suspend outer tx; create own tx |
| `NESTED` | Savepoint within outer tx |
| `SUPPORTS` | Join if exists; run without tx if none |

**`REQUIRES_NEW` use case:**
```java
// Audit log must be written even if main transaction rolls back
@Transactional(propagation = Propagation.REQUIRES_NEW)
public void writeAuditLog(AuditEvent event) {
    auditRepository.save(event);
}
```

**Isolation levels:**
| Level | Dirty Read | Non-Repeatable Read | Phantom Read |
|---|---|---|---|
| READ_UNCOMMITTED | ✅ possible | ✅ possible | ✅ possible |
| READ_COMMITTED | ❌ | ✅ possible | ✅ possible |
| REPEATABLE_READ | ❌ | ❌ | ✅ possible |
| SERIALIZABLE | ❌ | ❌ | ❌ |

> Default in PostgreSQL = READ_COMMITTED. For financial operations, use REPEATABLE_READ.

### Optimistic vs Pessimistic Locking

**Optimistic Locking (preferred for low-contention):**
```java
@Version
private Long version;

// Hibernate checks version on UPDATE
// UPDATE orders SET ..., version = 6 WHERE id = 1 AND version = 5
// If version mismatch → OptimisticLockException → retry
```

**Pessimistic Locking (for high-contention, must-win scenarios):**
```java
@Lock(LockModeType.PESSIMISTIC_WRITE)
@Query("SELECT o FROM Order o WHERE o.id = :id")
Optional<Order> findByIdForUpdate(@Param("id") Long id);
// SELECT ... FOR UPDATE — DB row lock
```

### Interview Q&A (40L Java Architect Level)

**Q: How do you diagnose and fix N+1 queries in a production Spring app?**
A: First, enable Hibernate stats (`spring.jpa.properties.hibernate.generate_statistics=true`) or use p6spy to log actual SQL. You'll see 101 queries where you expect 1. Fix with JOIN FETCH in JPQL for one-off queries, or @EntityGraph for repository methods. For batch scenarios, @BatchSize(size=50) reduces N queries to N/50. Also disable `open-in-view` — it masks N+1 problems by keeping the session open through rendering.

**Q: What is the difference between optimistic and pessimistic locking? When do you use each?**
A: Optimistic locking uses a version column — read optimistically, check on write that no one else modified it since you read. Low DB overhead, great for low-contention writes. Pessimistic locking locks the row at the DB level (SELECT FOR UPDATE) — nothing else can modify it until you commit. Use optimistic for most business operations; use pessimistic only when you can't afford a retry (e.g., allocating a unique seat number, decrementing inventory in a flash sale).

**Q: Explain Spring @Transactional propagation — when would you use REQUIRES_NEW?**
A: REQUIRED (default) joins an existing transaction or creates one. REQUIRES_NEW always creates a new independent transaction, suspending the outer one. Use case: audit logging or sending notifications that must persist even if the main transaction rolls back. Example: in an order placement flow, if payment fails and we rollback, the audit log of "payment attempted" should still be written — so the audit write uses REQUIRES_NEW.

---

## Topic 3 · JVM Tuning & Garbage Collection

### In One Line
Understanding JVM heap, GC algorithms, and tuning flags separates a senior Java dev from a Java Architect — interviewers ask this to test depth.

### Memory Regions

```
JVM Memory:
├── Heap
│   ├── Young Generation (Eden + Survivor S0 + Survivor S1)
│   └── Old Generation (Tenured)
├── Metaspace (class metadata — no longer PermGen in Java 8+)
├── Stack (per-thread: stack frames, local variables)
└── Native Memory (JNI, Direct ByteBuffers)
```

**Object lifecycle:**
1. New objects → Eden
2. Minor GC → survivors move to S0/S1 (promotion counter increments)
3. After N minor GCs → promoted to Old Gen (N = `-XX:MaxTenuringThreshold`)
4. Old Gen fills → Major GC (Stop-the-World)

### GC Algorithms

| GC | Java Version | Best For | Latency |
|---|---|---|---|
| **G1GC** | Default (Java 9+) | General purpose, balanced | Low-medium |
| **ZGC** | Java 15+ (stable) | Ultra-low latency (sub-millisecond pauses) | Very low |
| **Shenandoah** | OpenJDK | Low-pause, concurrent | Very low |
| **ParallelGC** | Older apps | High throughput, accepts pauses | High |
| **SerialGC** | Single-core containers | Minimal memory overhead | High |

**For microservices in containers:** G1GC is default and good. For latency-sensitive services (payment processing, real-time APIs), evaluate ZGC (Java 17+).

### Key JVM Flags

```bash
# Heap sizing
-Xms2g -Xmx2g          # Set initial = max to avoid resizing
-XX:+UseG1GC            # Explicitly set GC
-XX:MaxGCPauseMillis=200 # G1 target pause time (soft target)

# In containers (Java 11+)
-XX:+UseContainerSupport          # Respect container memory limits
-XX:MaxRAMPercentage=75.0         # Use 75% of container RAM for heap

# GC logging (production)
-Xlog:gc*:file=/var/log/gc.log:time,uptime:filecount=5,filesize=20m

# OOM handling
-XX:+HeapDumpOnOutOfMemoryError
-XX:HeapDumpPath=/dumps/heap.hprof
```

### Memory Leak Pattern Recognition

| Symptom | Likely Cause |
|---|---|
| Old Gen grows indefinitely | Cache without eviction, static collections, listener not unregistered |
| Metaspace OOM | Class loader leak (dynamic class generation, old framework) |
| Native memory grows | Direct ByteBuffer leak, JNI |
| Frequent young GC | Too many short-lived objects; check if domain objects are over-allocated |

**Heap dump analysis tools:** VisualVM, Eclipse MAT (Memory Analyzer Tool), JDK Mission Control

---

## Topic 4 · Concurrency Patterns in Java

### In One Line
Java concurrency — locks, thread pools, CompletableFuture — is tested to see if you understand how to write safe, efficient parallel code and what can go wrong.

### Thread Safety Fundamentals

**Synchronized (intrinsic lock):**
```java
public class Counter {
    private int count = 0;
    
    public synchronized void increment() {  // Exclusive lock on this
        count++;
    }
    
    public synchronized int get() {
        return count;
    }
}
```

**ReentrantLock (explicit lock — more control):**
```java
private final ReentrantLock lock = new ReentrantLock();

public void increment() {
    lock.lock();
    try {
        count++;
    } finally {
        lock.unlock();  // Must unlock in finally
    }
}

// With timeout — avoid deadlock
if (lock.tryLock(100, TimeUnit.MILLISECONDS)) {
    try { ... } finally { lock.unlock(); }
}
```

**ReadWriteLock — for read-heavy scenarios:**
```java
private final ReadWriteLock rwLock = new ReentrantReadWriteLock();

public String read(String key) {
    rwLock.readLock().lock();    // Multiple readers allowed simultaneously
    try { return cache.get(key); }
    finally { rwLock.readLock().unlock(); }
}

public void write(String key, String value) {
    rwLock.writeLock().lock();   // Exclusive — no readers or writers
    try { cache.put(key, value); }
    finally { rwLock.writeLock().unlock(); }
}
```

### CompletableFuture — Async Orchestration

```java
// Sequential async pipeline
CompletableFuture<Order> future = CompletableFuture
    .supplyAsync(() -> orderRepo.findById(orderId))      // runs in ForkJoinPool
    .thenApplyAsync(order -> enrichWithCustomer(order))  // chained transformation
    .thenApplyAsync(order -> enrichWithInventory(order))
    .exceptionally(ex -> {
        log.error("Order enrichment failed", ex);
        return fallbackOrder();
    });

// Run multiple async calls in parallel, combine results
CompletableFuture<Order> orderFuture = fetchOrderAsync(orderId);
CompletableFuture<Customer> customerFuture = fetchCustomerAsync(customerId);
CompletableFuture<Inventory> inventoryFuture = fetchInventoryAsync(productId);

CompletableFuture.allOf(orderFuture, customerFuture, inventoryFuture)
    .thenApply(v -> buildResponse(
        orderFuture.join(), 
        customerFuture.join(), 
        inventoryFuture.join()
    ));
```

**Custom thread pool (don't use ForkJoinPool for blocking I/O):**
```java
ExecutorService ioPool = Executors.newFixedThreadPool(
    Runtime.getRuntime().availableProcessors() * 2  // I/O bound: 2x CPU count
);

CompletableFuture.supplyAsync(() -> callExternalService(), ioPool);
```

### Common Concurrency Pitfalls

| Pitfall | Problem | Fix |
|---|---|---|
| Using `HashMap` in shared state | Not thread-safe, data corruption | `ConcurrentHashMap` |
| Using `++count` without sync | Non-atomic read-modify-write | `AtomicInteger.incrementAndGet()` |
| Blocking in `ForkJoinPool` | Starves other async tasks | Use dedicated thread pool for blocking I/O |
| Deadlock | Thread A holds lock1, waits for lock2; Thread B holds lock2, waits for lock1 | Consistent lock ordering; tryLock with timeout |
| Thread pool saturation | All threads blocked waiting for downstream | Circuit breaker + bulkhead (separate pools) |

### Distributed Lock with Redis (Redisson)

```java
RedissonClient redisson = Redisson.create(config);
RLock lock = redisson.getLock("order-lock:" + orderId);

boolean acquired = lock.tryLock(5, 30, TimeUnit.SECONDS);  // wait 5s, hold 30s
if (acquired) {
    try {
        processOrder(orderId);
    } finally {
        lock.unlock();
    }
} else {
    throw new ConcurrentProcessingException("Order " + orderId + " already being processed");
}
```

### Interview Q&A (40L Java Architect Level)

**Q: What is the difference between synchronized and ReentrantLock?**
A: `synchronized` is simpler — JVM-managed intrinsic lock, automatic release even on exception, but no timeout, no tryLock, and can't be interrupted while waiting. `ReentrantLock` is explicit — you can tryLock with timeout (avoids deadlock), interrupt waiting threads, and use Condition variables for finer signaling control. I default to synchronized for simple cases and ReentrantLock when I need timeout or fair lock ordering.

**Q: How do you parallelize multiple external service calls in Spring?**
A: CompletableFuture with allOf. Call each external service with `supplyAsync` on a dedicated I/O thread pool (not ForkJoinPool — those threads shouldn't block). Combine with `allOf` to wait for all, then join each result. Add timeouts with `orTimeout()` (Java 9+) and handle failures with `exceptionally` or `handle`. Key: never use the default ForkJoinPool for blocking HTTP calls — it starves other async work.

**Q: How do you implement a distributed lock in a microservices system?**
A: Redis with Redisson's RLock. It uses the Redlock algorithm — lock is set with a TTL (so it auto-expires if the service dies without releasing). Use tryLock with a wait timeout and a hold timeout. This prevents two instances of the same service from processing the same order simultaneously. Important: always release in a finally block, and size the TTL conservatively beyond your expected operation time.

---

## Topic 5 · Testing Strategy — Spring Ecosystem

### In One Line
Effective Spring testing uses a layered strategy: unit tests for domain logic, slice tests for layers, integration tests for full flows, contract tests for API boundaries.

### Test Pyramid for Spring Microservices

```
         /‾‾‾‾‾‾‾‾‾‾‾‾‾‾\
        /   E2E Tests     \    ← Few; full system; slow
       /‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾\
      /  Integration Tests  \  ← @SpringBootTest, Testcontainers
     /‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾\
    /    Unit Tests            \ ← Most; pure JUnit/Mockito; fast
   /______________________________\
```

### Unit Tests — Domain Logic (Pure Java, No Spring)

```java
class OrderTest {
    
    @Test
    void should_apply_discount_for_premium_customer() {
        // Arrange
        Customer customer = CustomerFixtures.premiumCustomer();
        List<OrderItem> items = List.of(new OrderItem(product, 2));
        
        // Act
        Order order = customer.placeOrder(items, shippingAddress);
        
        // Assert
        assertThat(order.total()).isEqualTo(Money.of(180, USD));  // 10% discount
        assertThat(order.domainEvents()).hasSize(1)
            .first().isInstanceOf(OrderPlaced.class);
    }
}
```

> Domain tests have ZERO Spring context — they run in milliseconds.

### Slice Tests — Spring Layer Tests

**@WebMvcTest — controller only:**
```java
@WebMvcTest(OrderController.class)
class OrderControllerTest {
    
    @Autowired MockMvc mockMvc;
    @MockBean PlaceOrderUseCase placeOrderUseCase;  // mock the service
    
    @Test
    void should_return_201_with_order_id() throws Exception {
        given(placeOrderUseCase.placeOrder(any())).willReturn(new OrderId("ord-123"));
        
        mockMvc.perform(post("/api/orders")
                .contentType(APPLICATION_JSON)
                .content("""{"customerId": "cust-1", "items": [...]}"""))
            .andExpect(status().isCreated())
            .andExpect(jsonPath("$.orderId").value("ord-123"));
    }
}
```

**@DataJpaTest — repository only (with in-memory DB):**
```java
@DataJpaTest
@AutoConfigureTestDatabase(replace = NONE)  // Use real DB via Testcontainers
class OrderRepositoryTest {
    
    @Autowired OrderRepository orderRepository;
    
    @Test
    void should_find_orders_by_status() {
        Order saved = orderRepository.save(OrderFixtures.placed());
        List<Order> result = orderRepository.findByStatus("PLACED");
        assertThat(result).hasSize(1).extracting(Order::id).contains(saved.id());
    }
}
```

### Integration Tests — Testcontainers

```java
@SpringBootTest
@Testcontainers
class OrderFlowIntegrationTest {
    
    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:15");
    
    @Container
    static KafkaContainer kafka = new KafkaContainer(DockerImageName.parse("confluentinc/cp-kafka:7.4.0"));
    
    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.kafka.bootstrap-servers", kafka::getBootstrapServers);
    }
    
    @Autowired PlaceOrderApplicationService placeOrderService;
    
    @Test
    void should_place_order_and_publish_event() {
        OrderId orderId = placeOrderService.placeOrder(validCommand());
        assertThat(orderId).isNotNull();
        // verify Kafka event published...
    }
}
```

### WireMock — External Service Mocking

```java
@SpringBootTest
@AutoConfigureWireMock(port = 8089)
class PaymentServiceClientTest {
    
    @Autowired PaymentServiceClient client;
    
    @Test
    void should_handle_payment_service_timeout() {
        stubFor(post(urlEqualTo("/payments"))
            .willReturn(aResponse()
                .withFixedDelay(5000)  // 5 second delay
                .withStatus(200)));
        
        assertThatThrownBy(() -> client.processPayment(request()))
            .isInstanceOf(PaymentTimeoutException.class);
    }
}
```

### Mockito Essentials

```java
// Mock vs Spy
@Mock PaymentService paymentService;     // Full mock — all methods return null by default
@Spy  AuditService auditService;        // Real object — only stub what you override

// Argument captor
ArgumentCaptor<PaymentRequest> captor = ArgumentCaptor.forClass(PaymentRequest.class);
verify(paymentService).processPayment(captor.capture());
assertThat(captor.getValue().amount()).isEqualTo(Money.of(100, USD));

// BDDMockito (cleaner syntax)
given(paymentService.processPayment(any())).willReturn(paymentConfirmation());
willThrow(new PaymentDeclinedException()).given(paymentService).processPayment(failingRequest());
```

### Interview Q&A (40L Java Architect Level)

**Q: How do you structure tests for a Spring Boot microservice?**
A: Three levels. Pure unit tests for domain logic — no Spring context, fast, cover all business rules and edge cases. Slice tests for each layer — @WebMvcTest for controllers (HTTP, validation, error handling), @DataJpaTest for repositories (queries, indexes). Integration tests with Testcontainers for the full stack — real PostgreSQL, real Kafka — covering end-to-end flows. Contract tests via Pact or Spring Cloud Contract for the service API boundary. This gives fast feedback at unit level and confidence at integration level without needing all services running.

**Q: What is the difference between @Mock and @Spy in Mockito?**
A: @Mock creates a full mock — every method returns null/empty/0 by default, nothing real runs. @Spy wraps a real object — real methods run unless you stub a specific one. Use @Mock for dependencies you don't want to run (database, external service). Use @Spy when you want to test the real behavior of most methods but override one specific method (e.g., stub a private helper but test the real public method).

**Q: How do you test code that calls an external HTTP service?**
A: WireMock. It starts a local HTTP server that you configure to return specific responses or simulate errors and delays. Your service under test points to WireMock's port instead of the real service URL. This lets you test timeout handling, retry logic, and error responses without hitting real external systems. In Spring Boot, @AutoConfigureWireMock handles startup automatically. For more complex scenarios, use WireMock's request matching and response templating.

---

## Day 3 Quick Reference

| Topic | Key Interview Answer |
|---|---|
| Clean Architecture | Domain layer is POJO — no Spring; application service orchestrates; infra implements interfaces |
| N+1 | JOIN FETCH in JPQL or @EntityGraph; disable open-in-view; measure with stats |
| @Transactional | REQUIRED = join or create; REQUIRES_NEW = independent tx (audit logs, notifications) |
| Optimistic Lock | @Version — low contention, retryable; Pessimistic — high contention, must-win |
| CompletableFuture | allOf for parallel calls; custom thread pool for blocking I/O; orTimeout for deadlines |
| JVM in containers | -XX:+UseContainerSupport + -XX:MaxRAMPercentage=75.0 |
| GC choice | G1GC default; ZGC for sub-ms pause (Java 17+, payment/RT services) |
| Test pyramid | Unit (domain, pure) → Slice (@WebMvcTest, @DataJpaTest) → Integration (Testcontainers) |
| WireMock | Simulate external HTTP service — timeouts, errors, latency — no real calls needed |

---

*Tags: #java #spring-boot #clean-architecture #hibernate #N+1 #transactions #JVM #GC #CompletableFuture #concurrency #Mockito #Testcontainers #WireMock*
