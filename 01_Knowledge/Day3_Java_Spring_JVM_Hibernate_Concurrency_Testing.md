# P2 · Day 3 — Java/Spring Ecosystem · JVM · Hibernate · Concurrency · Testing
**Pillar:** P2 — Java / Spring Ecosystem  
**Role Priority:** Java 🟢 Core · SA 🔵 Supporting · AI ⚪ Supporting  
**Day in Plan:** Day 3 (Week 1)  
**Time:** ~3 hours study + 1 hour Q&A practice

---

## Topic 1 · [[Spring Boot Microservice Structure & Clean Architecture]]

### In One Line
A well-structured Spring Boot service separates concerns into layers — each with a single responsibility — so the<mark style="background: #ABF7F7A6;"> domain stays pure</mark> and <mark style="background: #FFB86CA6;">infrastructure is swappable.</mark>

### Why It Matters
Java Architect interviews always ask: "How do you structure a Spring Boot service?" The wrong answer is "controller → service → repository." The right answer shows you understand why layers exist and how to keep business logic clean.

### Clean Architecture in Spring Boot

```
com.company.orderservice
├── api/                     ← Inbound adapters (REST controllers, gRPC handlers)
│   ├── OrderController.java
│   └── dto/              ← Request/Response DTOs (never domain objects here)
├── application/          ← Use cases / Application services (orchestration only)
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
<mark style="background: #ADCCFFA6;">Domain never imports infrastructure. Infrastructure implements domain interfaces.</mark>

### [[Spring Boot Annotations - App Layer Wise]]

| Annotation                 | Purpose                                         | SA Gotcha                                             |
| -------------------------- | ----------------------------------------------- | ----------------------------------------------------- |
| `@Service`                 | Marks application/domain service                | Don't put it on domain objects — domain is POJO       |
| `@Repository`              | Marks persistence layer + exception translation | ==Use on JPA implementations==, not domain interfaces |
| `@Transactional`           | Wraps method in DB transaction                  | Only on ==application services==, not domain          |
| `@Component`               | ==Generic Spring bean==                         | Avoid overuse — be explicit about layer               |
| `@RestController`          | HTTP handler + `@ResponseBody`                  | Controllers = thin; delegate to use case              |
| `@ConfigurationProperties` | Type-safe config binding                        | Prefer over `@Value` for structured config            |

---

## Topic 2 · [[JPA Hibernate Deep Dive]]

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

| GC             | Java Version           | Best For                                       | Latency    |
| -------------- | ---------------------- | ---------------------------------------------- | ---------- |
| **G1GC**       | ==Default (Java 9+)==  | General purpose, balanced                      | Low-medium |
| **ZGC**        | Java 15+ (stable)      | ==Ultra-low latency (sub-millisecond pauses)== | Very low   |
| **ParallelGC** | Older apps             | High throughput, accepts pauses                | High       |
| **SerialGC**   | Single-core containers | Minimal memory overhead                        | High       |

**For microservices in containers:** ==G1GC is default and good.== For latency-sensitive services (payment processing, real-time APIs), evaluate ZGC (Java 17+).

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

| Symptom                    | Likely Cause                                                                 |
| -------------------------- | ---------------------------------------------------------------------------- |
| Old Gen grows indefinitely | Cache without eviction, static collections, listener not unregistered        |
| Metaspace OOM              | Class loader leak (dynamic class generation, old framework)                  |
| Native memory grows        | Direct ByteBuffer leak, JNI                                                  |
| Frequent young GC          | ==Too many short-lived objects==; check if domain objects are over-allocated |

**Heap dump analysis tools:** VisualVM, Eclipse MAT (Memory Analyzer Tool), JDK Mission Control

---
## Topic 4 · [[Concurrency Patterns in Java]]

### In One Line
Java concurrency — <mark style="background: #FFB86CA6;">locks, thread pools, CompletableFuture</mark> — is tested to see if you understand how to write safe, efficient parallel code and what can go wrong.

### Thread Safety Fundamentals

**Synchronized:**
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

| Pitfall                         | Problem                                                                      | Fix                                            |
| ------------------------------- | ---------------------------------------------------------------------------- | ---------------------------------------------- |
| Using `HashMap` in shared state | Not thread-safe, data corruption                                             | `ConcurrentHashMap`                            |
| Using `++count` without sync    | Non-atomic read-modify-write                                                 | `AtomicInteger.incrementAndGet()`              |
| Blocking in `ForkJoinPool`      | Starves other async tasks                                                    | Use dedicated thread pool for blocking I/O     |
| Deadlock                        | Thread A holds lock1, waits for lock2; Thread B holds lock2, waits for lock1 | Consistent lock ordering; tryLock with timeout |
| Thread pool saturation          | All threads blocked waiting for downstream                                   | Circuit breaker + bulkhead (separate pools)    |

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

### Interview Q&A

**Q: What is the difference between synchronized and ReentrantLock?**
A: `synchronized` <mark style="background: #FFB86CA6;">is simpler — JVM-managed lock, automatic release even on exception, but no timeout, no tryLock, and can't be interrupted while waiting</mark>. `ReentrantLock` is <mark style="background: #ABF7F7A6;">explicit — you can tryLock with timeout (avoids deadlock), interrupt waiting threads, and use Condition variables for finer signaling control.</mark> I default to synchronized for simple cases and ReentrantLock when I need timeout or fair lock ordering.

**Q: How do you parallelize multiple external service calls in Spring?**
A: <mark style="background: #FFF3A3A6;">CompletableFuture</mark> with allOf. Call each external service with `supplyAsync` <mark style="background: #ADCCFFA6;">on a dedicated I/O thread pool </mark>(not ForkJoinPool — those threads shouldn't block). Combine with `allOf` to wait for all, then join each result. Add timeouts with `orTimeout()` (Java 9+) and handle failures with `exceptionally` or `handle`. Key: never use the default ForkJoinPool for blocking HTTP calls — it starves other async work.

**Q: How do you implement a distributed lock in a microservices system?**
A: <mark style="background: #ADCCFFA6;">Redis with Redisson's RLock</mark>. It uses the Redlock algorithm — <mark style="background: #D2B3FFA6;">lock is set with a TTL</mark> (so it auto-expires if the service dies without releasing). Use tryLock with a wait timeout and a hold timeout. This prevents two instances of the same service from processing the same order simultaneously. Important: always release in a finally block, and size the TTL conservatively beyond your expected operation time.

---

## Topic 5 · Testing Strategy — Spring Ecosystem

### In One Line
Effective Spring testing uses a layered strategy: <mark style="background: #FFB86CA6;">unit tests for domain logic</mark>, slice tests for layers, <mark style="background: #ADCCFFA6;">integration tests for full flows</mark>, <mark style="background: #ABF7F7A6;">contract tests for API boundaries</mark>.

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

### Interview Q&A

**Q: How do you structure tests for a Spring Boot microservice?**
A: Three levels. <mark style="background: #D2B3FFA6;">Pure unit tests for domain logic — no Spring context, fast, cover all business rules and edge cases</mark>. <mark style="background: #ADCCFFA6;">Slice tests for each layer — @WebMvcTest for controllers (HTTP, validation, error handling), @DataJpaTest for repositories (queries, indexes). Integration tests with Testcontainers for the full stack — real PostgreSQL, real Kafka — covering end-to-end flows</mark>. <mark style="background: #FFF3A3A6;">Contract tests via Pact or Spring Cloud Contract for the service API boundary. </mark>This gives fast feedback at unit level and confidence at integration level without needing all services running.

**Q: What is the difference between @Mock and @Spy in Mockito?**
A: <mark style="background: #ADCCFFA6;">@Mock creates a full mock</mark> — every method returns null/empty/0 by default, <mark style="background: #ADCCFFA6;">nothing real runs.</mark> <mark style="background: #FFF3A3A6;">@Spy wraps a real object</mark> — <mark style="background: #FFF3A3A6;">real methods run unless you stub a specific one</mark>. Use @Mock for dependencies you don't want to run (database, external service). Use @Spy when you want to test the real behavior of most methods but override one specific method (e.g., stub a private helper but test the real public method).

Let’s look at a concrete example using a standard `Calculator` class to see exactly how they behave differently.
```Java
public class Calculator {
    public int add(int a, int b) {
        return a + b; // Real behavior: actually calculates the sum
    }
}
```

## 1. `@Mock` (The Hollow Shell)
When you tell Mockito to create a `@Mock` of your `Calculator`, Mockito creates a brand-new, completely fake object that _looks_ like a calculator on the outside, but has **zero real code inside it**.
```Java
@Mock
Calculator mockCalc;

// Test Execution:
int result = mockCalc.add(2, 3); 
System.out.println(result); // Prints: 0
```

- **What happened?** Mockito completely intercepted the call. Because it is a full mock, the real code inside the `add` method (`return a + b;`) **never ran**.
- **The Default Rule:** By default, every single method on a `@Mock` returns a default blank value: `0` for numbers, `null` for objects, and `false` for booleans. It will _only_ return something else if you manually hardcode it using a stub (e.g., `when(mockCalc.add(2,3)).thenReturn(5);`).

## 2. `@Spy` (The Wire-Tapped Real Object)
When you create a `@Spy`, you start with a **living, breathing, real instance** of your class. Mockito simply wraps a sneaky tracking layer around it.
```Java
@Spy
Calculator spyCalc = new Calculator(); // Notice you initialize a REAL object here

// Test Execution:
int result = spyCalc.add(2, 3);
System.out.println(result); // Prints: 5
```

- **What happened?** The **real, actual code** inside the `add` method executed perfectly, calculated `2 + 3`, and returned `5`.
- **The Spy's Superpower:** Because it is wire-tapped, Mockito silently stands in the background logging everything that happens. You can now verify if the method was called:
    ```Java
    verify(spyCalc).add(2, 3); // Mockito can confirm: "Yes, this real method ran!"
    ```

## 3. The Partial Override (Why we use Spies)
The main reason architects use a `@Spy` is when they want the object to act completely real, _except_ for one specific method that they want to forcefully override.
Imagine our real calculator has a method that fetches live exchange rates from the internet:
```Java
public class FinancialCalculator {
    public double getLiveExchangeRate() {
        // Imagine this connects to the internet and talks to a real bank API
    }
    
    public double calculateTotalTax(double amount) {
        double rate = getLiveExchangeRate(); // Uses the internet method
        return amount * rate;
    }
}
```

If you are running a unit test, you don't want your test to fail just because the bank's website is down. You use a `@Spy` to run the real tax calculations, but hardcode _only_ the internet method:
```Java
@Spy
FinancialCalculator spyCalc = new FinancialCalculator();

// Tell the spy to fake the internet method, but leave everything else real
doReturn(1.2).when(spyCalc).getLiveExchangeRate();

// Test Execution:
double tax = spyCalc.calculateTotalTax(100); 
// 1. calculateTotalTax runs its REAL logic!
// 2. When it hits getLiveExchangeRate(), it uses your fake value (1.2) instead of the internet!
```

### Summary Checklist for Your Mental Map
- **`@Mock`:** A completely hollow proxy shell. No real code runs. Everything returns `null` or `0` unless you manually configure it. (Use for: Heavy things like external APIs or Databases).
- **`@Spy`:** A real, functional object. The real logic executes normally, but you have the power to selectively override individual methods when needed. (Use for: Testing real class logic while bypassing an troublesome internal helper method).

**Q: How do you test code that calls an external HTTP service?**
A: <mark style="background: #FFB86CA6;">WireMock. It starts a local HTTP server that you configure to return specific responses or simulate errors and delays.</mark> Your service under test points to WireMock's port instead of the real service URL. This lets you test timeout handling, retry logic, and error responses without hitting real external systems. In Spring Boot, @AutoConfigureWireMock handles startup automatically. For more complex scenarios, use WireMock's request matching and response templating.

---

## Day 3 Quick Reference

| Topic              | Key Interview Answer                                                                            |
| ------------------ | ----------------------------------------------------------------------------------------------- |
| Clean Architecture | Domain layer is POJO — no Spring; application service orchestrates; infra implements interfaces |
| N+1                | JOIN FETCH in JPQL or @EntityGraph; disable open-in-view; measure with stats                    |
| @Transactional     | REQUIRED = join or create; REQUIRES_NEW = independent tx (audit logs, notifications)            |
| Optimistic Lock    | @Version — low contention, retryable; Pessimistic — high contention, must-win                   |
| CompletableFuture  | allOf for parallel calls; custom thread pool for blocking I/O; orTimeout for deadlines          |
| JVM in containers  | -XX:+UseContainerSupport + -XX:MaxRAMPercentage=75.0                                            |
| GC choice          | G1GC default; ZGC for sub-ms pause (Java 17+, payment/RT services)                              |
| Test pyramid       | Unit (domain, pure) → Slice (@WebMvcTest, @DataJpaTest) → Integration (Testcontainers)          |
| WireMock           | Simulate external HTTP service — timeouts, errors, latency — no real calls needed               |

---

*Tags: #java #spring-boot #clean-architecture #hibernate #N+1 #transactions #JVM #GC #CompletableFuture #concurrency #Mockito #Testcontainers #WireMock*
