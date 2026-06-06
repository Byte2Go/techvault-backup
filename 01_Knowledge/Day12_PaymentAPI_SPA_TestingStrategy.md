# P8 · Day 12 — Payment API · SPA Integration · Microservices Testing Strategy
**Pillar:** P8 — Integration & Migration (final day)  
**Role Priority:** SA 🔵 Core · Java 🟢 Core · AI ⚪ Supporting  
**Day in Plan:** Day 12 (Week 2)  
**Scenarios covered:** S3, S17, S18

---

## Topic 1 · Payment API Integration — Razorpay / Stripe

### In One Line
Payment integration is not just an API call — it requires idempotency, webhook handling, PCI scope management, and robust failure recovery to be production-ready.

### Architecture Overview

```
User → [SPA / Mobile App]
           ↓
    [API Gateway / BFF]
           ↓
    [OrderService]           ← coordinates the flow
           ↓
    [PaymentService]         ← owns all payment logic; ACL wraps Razorpay
           ↓
    [Razorpay API]           ← processes card data; returns payment token
           ↑
    [Webhook Endpoint]       ← Razorpay pushes async payment events here
```

### Razorpay Integration Flow

```
Step 1: Create Razorpay Order (server-side)
  OrderService → PaymentService:
    POST https://api.razorpay.com/v1/orders
    { "amount": 99900,          ← in paise (₹999.00)
      "currency": "INR",
      "receipt": "order-123",   ← your internal order ID (idempotency)
      "notes": { "customerId": "cust-456" }
    }
  Razorpay returns: { "id": "order_abc123", "status": "created" }

Step 2: Render payment widget (client-side)
  SPA receives razorpayOrderId from BFF
  Loads Razorpay Checkout.js
  User enters card details → Razorpay handles card data (PCI scope stays with them)
  Razorpay calls your callback with:
    { "razorpay_payment_id": "pay_xyz789",
      "razorpay_order_id": "order_abc123",
      "razorpay_signature": "HMAC-SHA256 of order_id|payment_id" }

Step 3: Verify payment (server-side — critical)
  SPA sends all three tokens to your PaymentService
  PaymentService verifies signature:
    expected = HMAC-SHA256(razorpayOrderId + "|" + paymentId, razorpayKeySecret)
    if expected != received → reject (possible tampering)
  If valid → mark order as PAID → publish OrderPaid event

Step 4: Webhook (async confirmation / failure)
  Razorpay pushes to your webhook endpoint:
    payment.captured  → payment successful
    payment.failed    → payment failed
    refund.created    → refund initiated
```

### Idempotency — The Critical Design

```java
@Service
public class PaymentService {

    @Transactional
    public PaymentResult initiatePayment(PaymentRequest request) {
        // Check: has this order already been paid?
        Optional<Payment> existing = paymentRepo.findByOrderId(request.orderId());
        if (existing.isPresent()) {
            return PaymentResult.from(existing.get());  // Return cached result — no double charge
        }

        // Create Razorpay order — use orderId as receipt (Razorpay deduplicates by receipt)
        RazorpayOrder razorpayOrder = razorpayClient.createOrder(
            request.amount(), request.orderId()  // receipt = orderId
        );

        // Persist payment record BEFORE returning to client
        Payment payment = paymentRepo.save(Payment.builder()
            .orderId(request.orderId())
            .razorpayOrderId(razorpayOrder.id())
            .status(PENDING)
            .amount(request.amount())
            .build());

        return PaymentResult.pending(payment.id(), razorpayOrder.id());
    }

    @Transactional
    public void verifyAndCapture(PaymentVerificationRequest req) {
        // Verify HMAC signature (prevent tampering)
        String expected = HmacUtils.hmacSha256Hex(
            razorpayKeySecret,
            req.razorpayOrderId() + "|" + req.razorpayPaymentId()
        );
        if (!expected.equals(req.razorpaySignature())) {
            throw new PaymentVerificationException("Invalid payment signature");
        }

        Payment payment = paymentRepo.findByRazorpayOrderId(req.razorpayOrderId())
            .orElseThrow();
        payment.markCaptured(req.razorpayPaymentId());
        paymentRepo.save(payment);

        eventPublisher.publish(new OrderPaid(payment.orderId(), payment.amount()));
    }
}
```

### Webhook Handler — Idempotent & Signature-Verified

```java
@RestController
@RequestMapping("/webhooks/razorpay")
public class RazorpayWebhookController {

    @PostMapping
    public ResponseEntity<Void> handleWebhook(
            @RequestBody String payload,
            @RequestHeader("X-Razorpay-Signature") String signature) {

        // 1. Verify webhook signature
        String expected = HmacUtils.hmacSha256Hex(webhookSecret, payload);
        if (!expected.equals(signature)) {
            log.warn("Invalid Razorpay webhook signature — possible spoofing");
            return ResponseEntity.status(HttpStatus.UNAUTHORIZED).build();
        }

        RazorpayEvent event = parseEvent(payload);

        // 2. Idempotency — check if already processed
        if (webhookEventRepo.exists(event.id())) {
            log.info("Duplicate webhook event {} — skipping", event.id());
            return ResponseEntity.ok().build();  // Return 200 — don't cause retries
        }

        // 3. Process event
        switch (event.type()) {
            case "payment.captured" -> paymentService.handleCapture(event);
            case "payment.failed"   -> paymentService.handleFailure(event);
            case "refund.created"   -> paymentService.handleRefund(event);
            default -> log.info("Unhandled webhook event type: {}", event.type());
        }

        // 4. Mark as processed
        webhookEventRepo.markProcessed(event.id());
        return ResponseEntity.ok().build();
    }
}
```

**Critical rule:** Always return 200 to Razorpay even if your processing fails — otherwise Razorpay retries indefinitely. Handle failures internally (DLQ, alerting).

### Payment Failure Handling — State Machine

```
Payment States:
  INITIATED → PENDING → CAPTURED → REFUNDED
                      ↘ FAILED
                      ↘ EXPIRED (Razorpay order expires after 15 min if not paid)

Failure scenarios and responses:
  Card declined:      → Mark FAILED; notify user; release inventory reservation
  Payment timeout:    → Razorpay order expires; webhook "payment.failed" received
  Network failure:    → Idempotency key prevents double charge on retry
  Webhook not received: → Scheduled job: poll Razorpay for orders in PENDING > 30 min
```

### PCI-DSS Scope Reduction

```
With Razorpay Checkout.js:
  → Card data NEVER touches your servers
  → Razorpay's JS handles card collection in an iframe (their domain)
  → You store: payment tokens, Razorpay order IDs (NOT card numbers, NOT CVV)
  → Your PCI scope: SAQ-A (simplest level)
  → No need for: HSM, PCI audits, cardholder data environment (CDE)

If you build your own payment form (DO NOT — but for knowledge):
  → Card data touches your server → PCI scope = SAQ-D (most complex)
  → Requires: penetration testing, network segmentation, annual audit, quarterly scans
```

### Refund Design

```java
@Transactional
public RefundResult initiateRefund(String orderId, Money amount, String reason) {
    Payment payment = paymentRepo.findByOrderId(orderId)
        .orElseThrow(() -> new PaymentNotFoundException(orderId));

    // Idempotency: one refund per order (or per refund request ID)
    if (payment.isRefunded()) {
        return RefundResult.alreadyRefunded(payment.refundId());
    }

    // Call Razorpay
    RazorpayRefund refund = razorpayClient.createRefund(
        payment.razorpayPaymentId(),
        amount.inPaise(),
        Map.of("notes", reason)
    );

    payment.markRefundInitiated(refund.id(), amount);
    paymentRepo.save(payment);

    eventPublisher.publish(new RefundInitiated(orderId, amount));
    return RefundResult.initiated(refund.id());
    // Actual refund confirmation comes via webhook: refund.created / refund.failed
}
```

### Interview Q&A

**Q: How do you design a payment integration that handles network failures and retries safely?**
A: Three layers. First, idempotency at the order creation level — use your internal orderId as the Razorpay receipt; Razorpay deduplicates by receipt, so creating the same order twice returns the same Razorpay order. Second, idempotency at the verification level — before processing a payment capture, check if it's already in CAPTURED state in your DB; return cached result if so. Third, webhook idempotency — store processed webhook event IDs in a dedup table; ignore duplicates (return 200 to stop retries). The HMAC signature verification on webhooks prevents spoofed events. A scheduled reconciliation job polls Razorpay for any PENDING orders older than 30 minutes — catches missed webhooks.

**Q: How does Razorpay Checkout.js reduce your PCI scope?**
A: Razorpay renders the payment form in an iframe served from their domain. Card numbers and CVV never touch your servers — they go directly from the browser to Razorpay's servers. You receive a payment token and order ID, not card data. This means your PCI scope drops to SAQ-A — the simplest compliance level requiring minimal controls. If you built your own payment form that POSTed card data to your server, you'd need full SAQ-D compliance: network segmentation, HSM, quarterly vulnerability scans, annual penetration test, PCI audit.

---

## Topic 2 · SPA Integration Patterns (React / Angular)

### In One Line
SPA architecture with microservices requires deliberate decisions on auth flow, state management, error handling, and real-time updates — each with a clear pattern.

### Full Auth Flow (Revisited — SPA Focus)

```
React App → clicks Login
  → Redirects to Keycloak/Auth0 (Authorization Code + PKCE)
  → User authenticates
  → Redirect back to SPA with auth code
  → SPA exchanges code for tokens (backend or SPA direct)
  → Access token: stored in memory (React state / Zustand)
  → Refresh token: HttpOnly cookie (server sets it)

Every API call:
  fetch('/api/orders', {
    headers: { 'Authorization': `Bearer ${accessToken}` }
  })

On 401 (token expired):
  → SPA calls /auth/refresh (sends refresh token cookie automatically)
  → Gets new access token → retries original request
  → If refresh fails → redirect to login

Token storage rule:
  ✅ Access token → memory (React state) — lost on page reload (by design)
  ✅ Refresh token → HttpOnly cookie — JS cannot access; safe from XSS
  ❌ Never → localStorage (XSS can steal it)
  ❌ Never → sessionStorage (same XSS risk as localStorage)
```

### API Layer Design in SPA

```typescript
// Centralised API client — handles auth, errors, retries
class ApiClient {
  private accessToken: string | null = null;

  async request<T>(url: string, options: RequestInit = {}): Promise<T> {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        'Authorization': this.accessToken ? `Bearer ${this.accessToken}` : '',
        ...options.headers,
      },
      credentials: 'include',   // Send cookies (refresh token)
    });

    if (response.status === 401) {
      await this.refreshToken();          // Refresh and retry once
      return this.request<T>(url, options);
    }

    if (!response.ok) {
      const error = await response.json();
      throw new ApiError(response.status, error.message, error.correlationId);
    }

    return response.json();
  }

  private async refreshToken() {
    const res = await fetch('/auth/refresh', {
      method: 'POST',
      credentials: 'include'
    });
    if (!res.ok) {
      this.accessToken = null;
      window.location.href = '/login';   // Force re-login
      return;
    }
    const { accessToken } = await res.json();
    this.accessToken = accessToken;
  }
}
```

### Server-Sent Events / WebSocket — Real-Time Updates

```
Use case: Order tracking page — show live status updates without polling

Option 1: Polling (simple but inefficient)
  setInterval(() => fetchOrderStatus(orderId), 5000);   // every 5 seconds
  → Unnecessary load; stale between polls

Option 2: Server-Sent Events (SSE) — one-way server push
  const eventSource = new EventSource(`/api/orders/${orderId}/events`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  eventSource.onmessage = (event) => {
    const update = JSON.parse(event.data);
    setOrderStatus(update.status);
  };
  // Server pushes: data: {"status": "SHIPPED", "trackingNumber": "TN123"}
  // Works over HTTP/1.1; simpler than WebSocket; one-direction only

Option 3: WebSocket — bi-directional
  const ws = new WebSocket(`wss://api.company.com/ws/orders/${orderId}`);
  ws.onmessage = (event) => { ... };
  // Use when client also needs to send messages (live chat, collaborative editing)

Recommendation: SSE for notifications/tracking; WebSocket for collaborative features
```

### State Management Architecture

```
Global state (Zustand / Redux):
  auth: { user, accessToken, isAuthenticated }
  cart: { items, total }
  notifications: { unreadCount }

Server state (React Query / TanStack Query):
  // Handles caching, refetching, stale-while-revalidate
  const { data: orders, isLoading, error } = useQuery({
    queryKey: ['orders', customerId],
    queryFn: () => api.getOrders(customerId),
    staleTime: 30_000,        // consider fresh for 30 seconds
    refetchOnWindowFocus: true,
  });

  // Mutations with optimistic updates
  const placeOrder = useMutation({
    mutationFn: (orderData) => api.placeOrder(orderData),
    onMutate: async (newOrder) => {
      // Optimistically update UI before server confirms
      await queryClient.cancelQueries({ queryKey: ['cart'] });
      queryClient.setQueryData(['cart'], { items: [], total: 0 });
    },
    onError: (err, newOrder, context) => {
      // Rollback on error
      queryClient.setQueryData(['cart'], context.previousCart);
    },
    onSettled: () => queryClient.invalidateQueries({ queryKey: ['orders'] }),
  });

URL state (React Router):
  /orders?status=PLACED&page=2    ← filters and pagination in URL = shareable/bookmarkable
```

### CORS — Common Interview Question

```
Problem: React at https://app.company.com calls API at https://api.company.com
Browser blocks cross-origin request (different subdomain = different origin)

Fix (API Gateway / Spring Boot):
@Configuration
public class CorsConfig implements WebMvcConfigurer {
    @Override
    public void addCorsMappings(CorsRegistry registry) {
        registry.addMapping("/api/**")
            .allowedOrigins("https://app.company.com", "https://staging.company.com")
            .allowedMethods("GET", "POST", "PUT", "DELETE", "OPTIONS")
            .allowedHeaders("Authorization", "Content-Type", "X-Requested-With")
            .allowCredentials(true)   // Required for cookies (refresh token)
            .maxAge(3600);            // Preflight cache: 1 hour
    }
}

Preflight (OPTIONS) request:
  Browser: OPTIONS /api/orders, Origin: https://app.company.com
  Server: Access-Control-Allow-Origin: https://app.company.com
          Access-Control-Allow-Credentials: true
  Browser: Proceeds with actual GET/POST
```

---

## Topic 3 · Microservices Testing Strategy

### In One Line
Effective microservices testing is a deliberate pyramid — heavy fast unit tests, targeted slice tests, selective integration tests, and contract tests at boundaries — not all-or-nothing E2E.

### The Microservices Test Pyramid

```
              ╱‾‾‾‾‾‾‾‾‾‾‾‾╲
             ╱   E2E Tests   ╲         ← 5-10 critical user journeys only
            ╱‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾╲
           ╱  Contract Tests   ╲       ← Every service boundary (Pact)
          ╱‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾╲
         ╱  Integration Tests   ╲      ← Testcontainers — real DB, Kafka
        ╱‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾╲
       ╱    Unit Tests (Domain)   ╲    ← Bulk of tests — pure JUnit/Mockito
      ╱________________________________╲

Speed:   ms        seconds      minutes      hours
Cost:    low       medium       high         very high
```

### Layer 1 — Unit Tests (Domain Logic)

```java
// Fast, no Spring context, no DB, no network
// Cover: business rules, edge cases, domain events, value objects

class OrderTest {

    @Test
    void cannot_add_item_to_cancelled_order() {
        Order order = OrderFixtures.cancelled();

        assertThatThrownBy(() -> order.addItem(ProductFixtures.any(), 1))
            .isInstanceOf(InvalidOrderStateException.class)
            .hasMessageContaining("Cannot modify a cancelled order");
    }

    @Test
    void discount_applied_for_premium_customer() {
        Customer customer = CustomerFixtures.premium();
        Order order = customer.placeOrder(
            List.of(new OrderItem(product, 2)),
            shippingAddress
        );

        assertThat(order.total()).isEqualTo(Money.of(180, "INR")); // 10% discount
        assertThat(order.domainEvents())
            .hasSize(1)
            .first().isInstanceOf(OrderPlaced.class);
    }
}
// Runs in < 1ms. Run all unit tests in < 30 seconds.
```

### Layer 2 — Slice Tests (Spring Layers)

```java
// @WebMvcTest — test controller in isolation
@WebMvcTest(OrderController.class)
@Import(SecurityConfig.class)
class OrderControllerTest {

    @Autowired MockMvc mockMvc;
    @MockBean PlaceOrderUseCase placeOrderUseCase;

    @Test
    @WithMockUser(roles = "CUSTOMER")
    void place_order_returns_201_with_location_header() throws Exception {
        given(placeOrderUseCase.execute(any())).willReturn(new OrderId("ord-123"));

        mockMvc.perform(post("/api/orders")
                .contentType(APPLICATION_JSON)
                .content("""
                    { "items": [{"productId": "p1", "quantity": 2}],
                      "shippingAddressId": "addr-1" }
                    """))
            .andExpect(status().isCreated())
            .andExpect(header().string("Location", containsString("/api/orders/ord-123")))
            .andExpect(jsonPath("$.orderId").value("ord-123"));

        verify(placeOrderUseCase).execute(argThat(cmd ->
            cmd.items().size() == 1 && cmd.items().get(0).quantity() == 2
        ));
    }

    @Test
    void unauthenticated_request_returns_401() throws Exception {
        mockMvc.perform(post("/api/orders").contentType(APPLICATION_JSON).content("{}"))
            .andExpect(status().isUnauthorized());
    }
}
```

```java
// @DataJpaTest — test repository + DB queries
@DataJpaTest
@AutoConfigureTestDatabase(replace = NONE)          // Use real Postgres via Testcontainers
@Import(PostgresTestContainerConfig.class)
class OrderRepositoryTest {

    @Autowired OrderJpaRepository orderRepository;

    @Test
    void find_orders_by_customer_and_status_returns_correct_results() {
        orderRepository.save(OrderFixtures.placed(CUSTOMER_ID));
        orderRepository.save(OrderFixtures.shipped(CUSTOMER_ID));
        orderRepository.save(OrderFixtures.placed("other-customer"));

        List<Order> result = orderRepository
            .findByCustomerIdAndStatus(CUSTOMER_ID, "PLACED");

        assertThat(result).hasSize(1)
            .extracting(Order::customerId).containsOnly(CUSTOMER_ID);
    }
}
```

### Layer 3 — Integration Tests (Testcontainers)

```java
@SpringBootTest(webEnvironment = RANDOM_PORT)
@Testcontainers
class PlaceOrderIntegrationTest {

    @Container
    static final PostgreSQLContainer<?> postgres =
        new PostgreSQLContainer<>("postgres:15-alpine");

    @Container
    static final KafkaContainer kafka =
        new KafkaContainer(DockerImageName.parse("confluentinc/cp-kafka:7.5.0"));

    @Container
    static final GenericContainer<?> redis =
        new GenericContainer<>("redis:7-alpine").withExposedPorts(6379);

    @DynamicPropertySource
    static void configureProperties(DynamicPropertyRegistry registry) {
        registry.add("spring.datasource.url", postgres::getJdbcUrl);
        registry.add("spring.kafka.bootstrap-servers", kafka::getBootstrapServers);
        registry.add("spring.redis.host", redis::getHost);
        registry.add("spring.redis.port", () -> redis.getMappedPort(6379));
    }

    @Autowired TestRestTemplate restTemplate;
    @Autowired KafkaTestConsumer kafkaConsumer;

    @Test
    void place_order_persists_and_publishes_event() {
        // Act
        var response = restTemplate.postForEntity("/api/orders",
            new PlaceOrderRequest(CUSTOMER_ID, List.of(new OrderItemRequest("p1", 2))),
            OrderResponse.class);

        // Assert HTTP
        assertThat(response.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        String orderId = response.getBody().orderId();

        // Assert DB
        Order saved = orderRepository.findById(orderId).orElseThrow();
        assertThat(saved.status()).isEqualTo("PLACED");

        // Assert Kafka event published
        OrderPlacedEvent event = kafkaConsumer.poll("order-events", Duration.ofSeconds(5));
        assertThat(event.orderId()).isEqualTo(orderId);
        assertThat(event.customerId()).isEqualTo(CUSTOMER_ID);
    }
}
```

### Layer 4 — Contract Tests (Pact)

```java
// CONSUMER side (OrderService consuming PaymentService API)
@ExtendWith(PactConsumerTestExt.class)
@PactTestFor(providerName = "payment-service")
class PaymentServiceContractTest {

    @Pact(consumer = "order-service")
    public RequestResponsePact successfulPayment(PactDslWithProvider builder) {
        return builder
            .given("payment can be processed")
            .uponReceiving("a charge request for a valid order")
                .method("POST").path("/payments")
                .body(new PactDslJsonBody()
                    .stringType("orderId")
                    .numberType("amount")
                    .stringValue("currency", "INR"))
            .willRespondWith()
                .status(200)
                .body(new PactDslJsonBody()
                    .stringType("paymentId")
                    .stringValue("status", "SUCCESS")
                    .numberType("amount"))
            .toPact();
    }

    @Test
    @PactTestFor(pactMethod = "successfulPayment")
    void order_service_handles_successful_payment(MockServer mockServer) {
        PaymentServiceClient client = new PaymentServiceClient(mockServer.getUrl());
        PaymentResult result = client.charge(new ChargeRequest("ord-123", 99900, "INR"));

        assertThat(result.status()).isEqualTo(PaymentStatus.SUCCESS);
        assertThat(result.paymentId()).isNotEmpty();
    }
}
// Generates pact file → uploaded to Pact Broker
// PaymentService CI downloads + verifies it satisfies this contract
```

### Layer 5 — E2E Tests (Selective — Critical Journeys Only)

```java
// Tools: Playwright (web), Appium (mobile), RestAssured (API E2E)
// Run against: staging environment with all services running
// Frequency: before every production release (not every commit)

@Test
void customer_can_place_order_and_receive_confirmation() {
    // Given: customer logged in
    var token = authClient.login("test@example.com", "password");

    // When: place order
    var orderResponse = orderClient.placeOrder(token,
        new PlaceOrderRequest(List.of(new Item("product-1", 1)), "address-1"));

    assertThat(orderResponse.status()).isEqualTo(201);
    String orderId = orderResponse.body().orderId();

    // Then: order is PLACED
    await().atMost(5, SECONDS).until(() ->
        orderClient.getOrder(token, orderId).status().equals("PLACED"));

    // And: notification sent (check email mock / notification service)
    await().atMost(10, SECONDS).until(() ->
        notificationClient.getNotifications(orderId).stream()
            .anyMatch(n -> n.type().equals("ORDER_CONFIRMATION")));
}
```

### WireMock — External Service Simulation

```java
// Test payment service with simulated Razorpay responses
@SpringBootTest
@AutoConfigureWireMock(port = 0)   // random port; injected via properties
class PaymentServiceTest {

    @Test
    void handles_razorpay_timeout_gracefully() {
        // Simulate Razorpay being slow (> our 2s timeout)
        stubFor(post(urlEqualTo("/v1/orders"))
            .willReturn(aResponse()
                .withFixedDelay(5000)    // 5 second delay
                .withStatus(200)));

        assertThatThrownBy(() ->
            paymentService.initiatePayment(new PaymentRequest("ord-1", money(999))))
            .isInstanceOf(PaymentGatewayTimeoutException.class);
    }

    @Test
    void retries_on_razorpay_500_and_succeeds_on_third_attempt() {
        stubFor(post(urlEqualTo("/v1/orders"))
            .inScenario("Retry")
            .whenScenarioStateIs(STARTED)
            .willReturn(serverError())
            .willSetStateTo("Second attempt"));

        stubFor(post(urlEqualTo("/v1/orders"))
            .inScenario("Retry")
            .whenScenarioStateIs("Second attempt")
            .willReturn(serverError())
            .willSetStateTo("Third attempt"));

        stubFor(post(urlEqualTo("/v1/orders"))
            .inScenario("Retry")
            .whenScenarioStateIs("Third attempt")
            .willReturn(okJson(razorpayOrderResponse())));

        PaymentResult result = paymentService.initiatePayment(request());
        assertThat(result.status()).isEqualTo(PENDING);
        verify(3, postRequestedFor(urlEqualTo("/v1/orders")));
    }
}
```

### Testing Strategy Summary for Interviews

```
For a 20-service microservices system:

Unit tests:     500+ tests per service, < 30s total
                Cover: all domain logic, edge cases, error paths

Slice tests:    50-100 per service, < 2 min total
                Cover: controller validation, repo queries, security

Integration:    10-20 per service, < 5 min total (Testcontainers)
                Cover: end-to-end service flows with real DB + Kafka

Contract:       1 per service boundary, < 1 min
                Cover: API contract between each consumer-provider pair
                Tools: Pact (polyglot) or Spring Cloud Contract (Java)

E2E:            5-10 critical journeys, 20-30 min total
                Cover: most important user flows only
                Run: before production release; not every commit

Performance:    1 load test per service, 30 min
                Tools: k6 or Gatling
                Run: weekly or before high-traffic events

Chaos:          Quarterly game day
                Tools: AWS Fault Injection Simulator, Chaos Toolkit
```

### Interview Q&A

**Q: How do you test microservices without standing up all 20 services?**
A: Layered strategy. Unit tests cover domain logic with zero infrastructure — fast and numerous. Slice tests (@WebMvcTest, @DataJpaTest) test each layer in isolation, mocking the adjacent layer. Integration tests use Testcontainers for real databases and Kafka — the service under test, real external dependencies in containers, everything else mocked via WireMock. Contract tests (Pact) verify API boundaries without needing real services — the consumer defines expectations, the provider verifies them independently in its own CI pipeline. Only E2E tests need all services running — and I keep those to 5-10 critical user journeys. This gives 95% of confidence with 20% of the complexity of all-up integration environments.

**Q: What is the biggest testing mistake teams make with microservices?**
A: Over-reliance on E2E tests and under-investment in contract tests. Teams that rely on E2E for confidence end up with slow (30-min), flaky test suites that block CI. Contract testing gives you the same confidence for API compatibility in seconds, without needing a shared environment. The second mistake is testing the infrastructure instead of the domain — writing Testcontainers tests for simple CRUD that should just be a unit test. Fast tests run frequently; slow tests get skipped.

---

## Day 12 Quick Reference

| Topic | Key Interview Answer |
|---|---|
| Razorpay flow | Create order server-side → widget client-side → verify HMAC signature server-side → webhook async confirmation |
| Payment idempotency | orderId as Razorpay receipt; check DB before charging; webhook dedup table |
| Webhook handler | Verify HMAC → check idempotency → process → return 200 always |
| PCI scope | Razorpay Checkout.js → card never touches your servers → SAQ-A scope |
| SPA token storage | Access token in memory; refresh token in HttpOnly cookie; never localStorage |
| CORS | API Gateway / Spring sets Access-Control-Allow-Origin; allowCredentials=true for cookies |
| SSE vs WebSocket | SSE = one-way push (order tracking); WebSocket = bi-directional (chat, collaboration) |
| React Query | Server state management — caching, stale-while-revalidate, optimistic updates |
| Test pyramid | Unit (fast, many) → Slice → Integration (Testcontainers) → Contract (Pact) → E2E (few) |
| Contract testing | Consumer writes expectations → Pact Broker → provider verifies in CI; no shared env needed |
| WireMock | Simulate external services — timeouts, errors, retries — without hitting real APIs |

---

*Tags: #payment #Razorpay #Stripe #idempotency #webhook #PCI #SPA #React #CORS #SSE #WebSocket #testing #Pact #contract-testing #Testcontainers #WireMock #E2E #S3 #S17 #S18*
