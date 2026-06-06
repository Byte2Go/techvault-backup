# P6 · Day 8 — SQL/NoSQL · Redis · DB-per-Service · Elasticsearch · Vector Databases
**Pillar:** P6 — Data Architecture  
**Role Priority:** SA 🔵 Core · Java 🟢 Core · AI 🟣 Supporting  
**Day in Plan:** Day 8 (Week 2)  
**Time:** ~3 hours study + 1 hour Q&A practice

---

## Topic 1 · SQL vs NoSQL — Decision Framework

### In One Line
Pick the database that matches your access pattern — not the one that's trendy; every SA interview has a "choose a DB for this scenario" question.

### Decision Framework

```
START: What is your primary access pattern?

├── Relational data + ACID transactions + complex queries?
│     → PostgreSQL / MySQL (Relational)
│
├── Document data, flexible schema, JSON-native?
│     → MongoDB (Document)
│
├── Key → value lookups, extreme speed, caching?
│     → Redis (In-memory key-value)
│
├── Time-series data (metrics, IoT, logs)?
│     → InfluxDB / TimescaleDB (Time-series)
│
├── Wide-column, global scale, no joins, known access patterns?
│     → Cassandra / DynamoDB (Wide-column / Key-value)
│
├── Full-text search, relevance ranking?
│     → Elasticsearch / OpenSearch (Search)
│
├── Analytical queries on large datasets (OLAP)?
│     → Redshift / BigQuery / Snowflake (Data Warehouse)
│
└── Semantic / vector similarity search (AI)?
      → pgvector / Pinecone / Weaviate (Vector DB)
```

### Quick Selection Table

| Use Case | DB Choice | Why |
|---|---|---|
| Order management | PostgreSQL | ACID, relational, complex queries |
| User profiles | MongoDB | Flexible schema, nested addresses/preferences |
| Session / cache | Redis | Sub-ms reads, TTL support |
| Product catalog + search | Elasticsearch | Full-text search, faceted filters |
| IoT sensor data | InfluxDB or TimescaleDB | Time-series compression, range queries |
| Chat messages | Cassandra | High write throughput, time-ordered access |
| Shopping cart | Redis or DynamoDB | Fast reads, per-user key, TTL |
| Recommendation engine | pgvector or Pinecone | Similarity search on embeddings |
| Financial ledger | PostgreSQL | ACID, auditability, constraints |
| Analytics / reporting | Redshift or BigQuery | Column-store, scan billions of rows |

### SQL vs NoSQL — Core Tradeoffs

| Dimension | SQL (PostgreSQL) | NoSQL (MongoDB/Cassandra) |
|---|---|---|
| Schema | Rigid (migrations needed) | Flexible (schema-less / schema-optional) |
| Transactions | ACID | BASE (eventual consistency default) |
| Joins | Native, efficient | No joins — denormalize or application-side |
| Scaling | Vertical + read replicas | Horizontal sharding built-in |
| Query flexibility | Ad-hoc SQL, any column | Limited to designed access patterns |
| Best for | Complex relationships, transactions | Scale, flexibility, known access patterns |

> **SA rule:** If you're unsure, start with PostgreSQL. You can always migrate out. Migrating from NoSQL to relational when you realize you need transactions is painful.

---

## Topic 2 · PostgreSQL Deep Dive — Indexing, Partitioning, JSONB

### In One Line
PostgreSQL is the Swiss Army knife of databases — but only if you know how to wield indexes, partitions, and JSONB to make it perform at scale.

### Indexing Strategies

**B-Tree (default — most common):**
```sql
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_status_created ON orders(status, created_at DESC);  -- composite
-- Rule: put equality columns first, range/sort columns last in composite index
```

**Partial Index (index only relevant rows):**
```sql
-- Only index active orders — 10% of rows → index is 10x smaller → faster
CREATE INDEX idx_active_orders ON orders(customer_id, created_at)
WHERE status = 'ACTIVE';
```

**GIN Index (for JSONB, arrays, full-text search):**
```sql
CREATE INDEX idx_order_metadata ON orders USING GIN(metadata);
-- Allows: SELECT * FROM orders WHERE metadata @> '{"source": "mobile"}'
```

**Expression Index:**
```sql
CREATE INDEX idx_email_lower ON users(LOWER(email));
-- Allows: SELECT * FROM users WHERE LOWER(email) = 'user@example.com'
```

**Covering Index (include all columns needed — avoids table lookup):**
```sql
CREATE INDEX idx_orders_covering ON orders(customer_id)
INCLUDE (status, total, created_at);
-- Query can be answered from index alone — no heap fetch
```

### EXPLAIN ANALYZE — Diagnose Slow Queries

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM orders WHERE customer_id = 123 AND status = 'PLACED'
ORDER BY created_at DESC LIMIT 20;

-- Look for:
-- Seq Scan → missing index
-- Rows Removed by Filter (high) → index not selective enough
-- Buffers: hit vs read → cache hit ratio (want >99% hit)
-- Actual rows >> Estimated rows → stale statistics (run ANALYZE)
```

### Table Partitioning

**Range partitioning (by date — most common for time-series data):**
```sql
CREATE TABLE orders (
    id          BIGSERIAL,
    customer_id BIGINT NOT NULL,
    created_at  TIMESTAMPTZ NOT NULL,
    total       NUMERIC(12,2),
    status      VARCHAR(20)
) PARTITION BY RANGE (created_at);

CREATE TABLE orders_2025 PARTITION OF orders
    FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
CREATE TABLE orders_2026 PARTITION OF orders
    FOR VALUES FROM ('2026-01-01') TO ('2027-01-01');

-- Query on created_at → Postgres only scans relevant partition (partition pruning)
-- DROP old partitions instead of DELETE → instant, no bloat
```

**Benefits:**
- Query performance: partition pruning (only scan relevant partition)
- Maintenance: drop old partitions instantly vs expensive DELETE
- Archival: move old partitions to cheaper tablespace

### JSONB — Semi-Structured Data in PostgreSQL

```sql
-- Storing flexible metadata without separate tables
ALTER TABLE orders ADD COLUMN metadata JSONB;

-- Insert
INSERT INTO orders (customer_id, metadata) VALUES
(123, '{"source": "mobile", "promoCode": "SAVE10", "deviceId": "abc-xyz"}');

-- Query (uses GIN index)
SELECT * FROM orders WHERE metadata @> '{"source": "mobile"}';
SELECT * FROM orders WHERE metadata->>'promoCode' = 'SAVE10';

-- Update specific key without rewriting entire JSON
UPDATE orders SET metadata = jsonb_set(metadata, '{promoCode}', '"SAVE20"')
WHERE id = 456;

-- Aggregate over JSONB field
SELECT metadata->>'source' as source, COUNT(*)
FROM orders GROUP BY metadata->>'source';
```

**When to use JSONB over a separate table:**
- Data is optional / sparse (not all orders have metadata)
- Schema varies per record (different fields per order source)
- No need to query by those fields in most cases

### Interview Q&A

**Q: How do you handle a 1-billion row orders table in PostgreSQL?**
A: Partition by date range — most queries are time-bounded (last 30 days), so partition pruning eliminates 99% of the table. Index the partition key and common filter columns. Add read replicas for reporting queries. Archive partitions older than the retention window to cold storage (S3 via pg_partman or custom). For write scaling beyond a single primary, consider Citus for horizontal sharding — but try partitioning first.

**Q: When would you use JSONB instead of adding a new column?**
A: When data is sparse (only some rows have it), schema varies per record, or the field is a bag of optional attributes that don't need to be queried independently at high frequency. Don't use JSONB to avoid schema design — if you query a field in WHERE clauses or JOIN on it regularly, make it a proper column with an index. JSONB is a tool for flexibility, not a shortcut for schema laziness.

---

## Topic 3 · NoSQL Databases — Use Case Mastery

### MongoDB — Document Database

**Best for:** Flexible schema, hierarchical data, content management, user profiles

```javascript
// Document structure — no joins needed
{
  "_id": "user-123",
  "name": "Rahul Sharma",
  "email": "rahul@example.com",
  "addresses": [
    { "type": "home", "city": "Pune", "pin": "411001" },
    { "type": "office", "city": "Mumbai", "pin": "400001" }
  ],
  "preferences": {
    "notifications": { "email": true, "sms": false },
    "currency": "INR"
  }
}
```

**Indexing:**
```javascript
db.users.createIndex({ "email": 1 }, { unique: true })
db.users.createIndex({ "addresses.pin": 1 })  // index nested field
db.users.createIndex({ "name": "text" })       // text search index
```

**Transactions (since MongoDB 4.0):**
```javascript
const session = client.startSession();
session.startTransaction();
try {
    await orders.insertOne({ ... }, { session });
    await inventory.updateOne({ ... }, { session });
    await session.commitTransaction();
} catch (e) {
    await session.abortTransaction();
}
```

> MongoDB transactions exist but are slower than PostgreSQL. If you need frequent cross-document transactions, reconsider your data model.

### DynamoDB — AWS Key-Value / Wide Column

**Best for:** Known access patterns, high throughput, serverless, global tables

**Core concept — single-table design:**
```
Table: ecommerce
PK (partition key) | SK (sort key)     | attributes
USER#123           | PROFILE           | name, email, ...
USER#123           | ORDER#2026-01-01  | orderId, total, status
USER#123           | ORDER#2026-01-15  | orderId, total, status
PRODUCT#456        | DETAILS           | name, price, description
PRODUCT#456        | REVIEW#001        | rating, comment
```

**Access patterns designed upfront:**
- Get user: `PK=USER#123, SK=PROFILE`
- Get user's orders: `PK=USER#123, SK begins_with ORDER#`
- Get product: `PK=PRODUCT#456, SK=DETAILS`

**GSI (Global Secondary Index) for alternate access:**
```
GSI: status-index
PK: status  | SK: created_at
PLACED      | 2026-01-01T10:00:00
PLACED      | 2026-01-01T11:00:00
→ "Get all orders with status=PLACED sorted by time"
```

**When NOT to use DynamoDB:**
- Complex queries with multiple filter dimensions you didn't design for upfront
- Ad-hoc analytics
- Frequent JOINs / relational data

### Cassandra — Wide Column for High Write Throughput

**Best for:** Time-series, messaging, IoT, write-heavy workloads at massive scale

```sql
-- Cassandra table design — query-first approach
CREATE TABLE messages_by_conversation (
    conversation_id UUID,
    sent_at         TIMESTAMP,
    message_id      UUID,
    sender_id       UUID,
    content         TEXT,
    PRIMARY KEY (conversation_id, sent_at, message_id)
) WITH CLUSTERING ORDER BY (sent_at DESC);

-- This table is designed for ONE query: "get messages for conversation X ordered by time"
-- Any other query needs a separate table
```

**Key Cassandra principles:**
- Design table per query — no flexible querying
- Partition key determines which node stores data — choose for even distribution
- No joins, no transactions across partitions
- Eventual consistency by default (tunable with QUORUM reads)

---

## Topic 4 · Redis — Caching Patterns

### In One Line
Redis is an in-memory data structure store — used for caching, session management, distributed locks, rate limiting, and pub/sub — and every SA must know the right pattern for each.

### Cache-Aside (Lazy Loading) — Most Common

```java
public Product getProduct(String productId) {
    // 1. Check cache
    String cached = redis.get("product:" + productId);
    if (cached != null) {
        return deserialize(cached);        // Cache HIT — return immediately
    }

    // 2. Cache MISS — load from DB
    Product product = productRepo.findById(productId);

    // 3. Store in cache with TTL
    redis.setex("product:" + productId, 3600, serialize(product));  // TTL: 1 hour

    return product;
}

public void updateProduct(Product product) {
    productRepo.save(product);
    redis.del("product:" + product.getId());  // Invalidate cache on write
}
```

**Properties:** Cache only populated on demand. Cold start = all cache misses. DB is source of truth.

### Write-Through — Cache Updated on Every Write

```java
public void updateProduct(Product product) {
    productRepo.save(product);                                    // Write to DB
    redis.setex("product:" + product.getId(), 3600,              // Write to cache
        serialize(product));
}
```

**Properties:** Cache always up-to-date. More writes to Redis. Good for read-heavy data that changes frequently.

### Write-Behind (Write-Back) — Async DB Write

```java
public void updateProduct(Product product) {
    redis.set("product:" + product.getId(), serialize(product));  // Write to cache first
    messageQueue.publish(new ProductUpdateEvent(product));         // Async write to DB
}
```

**Properties:** Very fast writes. Risk: cache crashes before DB write → data loss. Only for non-critical data.

### Read-Through — Cache Sits in Front of DB

```
Application → Cache (Redis)
               → Cache HIT: return data
               → Cache MISS: Cache fetches from DB, stores, returns
               (Application never directly queries DB)
```

Used by managed caching solutions (AWS ElastiCache + DAX for DynamoDB).

### Cache Eviction Policies

| Policy | Behaviour | Use When |
|---|---|---|
| `allkeys-lru` | Evict least recently used | General caching — most common |
| `volatile-lru` | LRU only among keys with TTL | Mix of persistent + cached keys |
| `allkeys-lfu` | Evict least frequently used | Access patterns have hot/cold split |
| `noeviction` | Return error when full | Session store — losing sessions = bad |
| `volatile-ttl` | Evict key with lowest TTL first | Expire-based cache |

### Cache Stampede / Thundering Herd

**Problem:** Cache entry expires → 1000 concurrent requests all go to DB simultaneously → DB overload

**Fix 1 — Mutex lock on cache miss:**
```java
public Product getProduct(String productId) {
    String cached = redis.get("product:" + productId);
    if (cached != null) return deserialize(cached);

    // Only one thread fetches from DB; others wait
    String lockKey = "lock:product:" + productId;
    if (redis.set(lockKey, "1", SET_IF_NOT_EXISTS, EXPIRE, 5) != null) {
        try {
            Product product = productRepo.findById(productId);
            redis.setex("product:" + productId, 3600, serialize(product));
            return product;
        } finally {
            redis.del(lockKey);
        }
    } else {
        Thread.sleep(50);
        return getProduct(productId);  // Retry — lock holder should have populated cache
    }
}
```

**Fix 2 — Probabilistic early expiry (jitter):**
```java
// Add random jitter to TTL so entries don't all expire at the same time
int ttl = 3600 + (int)(Math.random() * 300);  // 60-65 minutes
redis.setex("product:" + productId, ttl, serialize(product));
```

### Redis Data Structures (beyond simple key-value)

```
String:   SET/GET — simple cache, counters (INCR)
Hash:     HSET/HGET — user session (field per attribute)
List:     LPUSH/RPOP — queue, feed, activity log
Set:      SADD/SMEMBERS — unique visitors, tags, followers
Sorted Set: ZADD/ZRANGE — leaderboard, rate limiting (sliding window), priority queue
Stream:   XADD/XREAD — event log, real-time feed (Kafka-lite)
```

**Rate limiting with Sorted Set:**
```java
// Sliding window rate limit: max 100 requests per minute
public boolean isAllowed(String userId) {
    long now = System.currentTimeMillis();
    long windowStart = now - 60_000;  // 1 minute ago
    String key = "ratelimit:" + userId;

    redis.zremrangeByScore(key, 0, windowStart);    // Remove old requests
    long count = redis.zcard(key);                   // Count requests in window

    if (count < 100) {
        redis.zadd(key, now, UUID.randomUUID().toString());  // Add this request
        redis.expire(key, 60);
        return true;
    }
    return false;
}
```

### Interview Q&A

**Q: What is cache-aside vs write-through? When do you use each?**
A: Cache-aside (lazy loading) populates the cache only on a miss — the application checks cache, misses, loads from DB, stores in cache. Simple, cache only holds what's been accessed. Write-through updates the cache on every write — always consistent but adds write latency. I use cache-aside for read-heavy data that's accessed infrequently (most products), and write-through for hot data that changes often and must always be current (user session, shopping cart). For very write-heavy workloads, write-behind (async DB write) maximizes write speed at the cost of some durability risk.

**Q: How do you handle cache invalidation?**
A: Three approaches. Key-based invalidation: delete the cache key on write — simple and correct for single entities. TTL-based: let entries expire naturally — acceptable for data where brief staleness is OK (product prices, catalog). Event-driven: on data change, publish an invalidation event to all cache nodes or services. The hardest part is deciding TTL — too short means high cache miss rate and DB load; too long means stale data. For financial data (balances, prices), short TTL or write-through. For static catalog data, longer TTL with explicit invalidation on updates.

---

## Topic 5 · Database-per-Service Pattern

### In One Line
Each microservice owns its database — no shared schemas, no cross-service joins — this is the foundation of true service independence.

### Why Database-per-Service

```
WRONG — Shared database:
  OrderService ──┐
  PaymentService ─┤──→ Shared PostgreSQL DB
  UserService   ──┘

Problems:
  - Schema change in Orders table → must coordinate with all teams
  - PaymentService can JOIN OrderService tables → hidden coupling
  - One service's slow query locks tables, affecting all services
  - Can't scale OrderService DB independently
  - Can't change OrderService DB technology (stuck with PostgreSQL for all)
```

```
RIGHT — Database per service:
  OrderService   → PostgreSQL (orders DB)
  PaymentService → PostgreSQL (payments DB)    ← separate instance/schema
  UserService    → PostgreSQL (users DB)
  CatalogService → Elasticsearch
  SessionService → Redis
```

### Cross-Service Data Queries — Solving Without Joins

**Problem:** BFF needs order + customer name in one response.

**Option 1 — API Composition (BFF aggregates):**
```
Web BFF:
  1. Call OrderService: GET /orders/123 → {orderId, customerId, items, total}
  2. Call UserService: GET /users/{customerId} → {name, email}
  3. Merge and return combined response
```

**Option 2 — Data Duplication via Events:**
```
When customer name changes:
  UserService → publishes CustomerNameUpdated event
  OrderService listens → updates its local copy of customer name in orders table

OrderService now has customer name locally → no API call needed
Trade-off: eventual consistency (brief window where name is stale)
```

**Option 3 — CQRS Read Model:**
```
Event projector builds a denormalized "OrderWithCustomer" read model:
  Kafka: OrderPlaced + CustomerCreated/Updated → OrderSummaryProjector
  → Builds: order_summaries table with orderId, customerId, customerName, total, status
  → BFF queries this single table
```

### Migration Path — Shared DB to DB-per-Service

```
Step 1: Separate schemas within same DB server
  orders_schema, payments_schema — same Postgres, different schemas
  → Enforce: services only connect to their schema (separate DB users)

Step 2: Separate data — break foreign keys, move to API calls
  payments_schema.orders_id (FK) → application-level lookup via OrderService API
  → Run dual-mode: read from both FK and API, compare results

Step 3: Separate DB servers
  Move payments_schema to its own Postgres instance
  Update PaymentService connection string

Step 4: (Optional) Change technology
  Move CatalogService from Postgres to Elasticsearch
```

---

## Topic 6 · Read Replicas & Replication Strategies

### In One Line
Read replicas offload read traffic from the primary, enabling horizontal read scaling — at the cost of eventual consistency between primary and replicas.

### PostgreSQL Replication

```
Primary (RDS) ──WAL streaming──→ Read Replica 1 (same AZ)
              ──WAL streaming──→ Read Replica 2 (different AZ)
              ──WAL streaming──→ Read Replica 3 (different region — DR)

Replication lag: typically <1 second; can spike under heavy write load
```

**Application routing:**
```java
@Configuration
public class DataSourceConfig {

    @Bean @Primary
    @ConfigurationProperties("spring.datasource.primary")
    DataSource primaryDataSource() { return DataSourceBuilder.create().build(); }

    @Bean
    @ConfigurationProperties("spring.datasource.replica")
    DataSource replicaDataSource() { return DataSourceBuilder.create().build(); }
}

// In service:
@Transactional(readOnly = true)  // Spring routes to replica when readOnly=true
public List<Order> getOrderHistory(String customerId) { ... }

@Transactional  // Routes to primary
public OrderId placeOrder(PlaceOrderCommand cmd) { ... }
```

### Replication Strategies

| Strategy | Description | Use When |
|---|---|---|
| **Async replication** | Primary doesn't wait for replica ack | Most OLTP — fastest writes, slight lag |
| **Sync replication** | Primary waits for replica ack before returning | Financial — zero data loss, slower writes |
| **Semi-sync** | Wait for at least one replica | Balance of safety and speed |
| **Multi-AZ (AWS RDS)** | Sync standby in different AZ — auto-failover | HA requirement; transparent failover <60s |

### When NOT to Use Read Replicas

- Data just written and immediately queried (replication lag → stale read)
- Use primary for reads that must reflect the latest write (e.g., immediately after placing an order, show order status)
- Pattern: write to primary, read from primary for the immediate response, then subsequent reads can use replica

---

## Topic 7 · Elasticsearch / OpenSearch

### In One Line
Elasticsearch is the go-to for full-text search, faceted filtering, and relevance ranking — built on Apache Lucene, it can handle queries that would kill a relational DB.

### Core Concepts

```
Index  = Table in SQL
Document = Row (JSON)
Field  = Column
Shard  = Horizontal partition (distributes across nodes)
Replica = Copy of shard (HA + read scaling)
```

### Indexing & Mapping

```json
PUT /products
{
  "mappings": {
    "properties": {
      "name":        { "type": "text", "analyzer": "standard" },
      "description": { "type": "text", "analyzer": "english" },
      "brand":       { "type": "keyword" },    // exact match, facets
      "price":       { "type": "double" },
      "category":    { "type": "keyword" },
      "rating":      { "type": "float" },
      "in_stock":    { "type": "boolean" },
      "created_at":  { "type": "date" }
    }
  }
}
```

**text** = analyzed (tokenized, stemmed) → full-text search  
**keyword** = not analyzed → exact match, aggregations, sorting

### Search Query

```json
GET /products/_search
{
  "query": {
    "bool": {
      "must": [
        { "match": { "name": "wireless headphones" }}  // full-text
      ],
      "filter": [
        { "term":  { "category": "Electronics" }},     // exact match
        { "term":  { "in_stock": true }},
        { "range": { "price": { "gte": 500, "lte": 5000 }}}
      ]
    }
  },
  "aggs": {
    "brands": { "terms": { "field": "brand" }},        // facets
    "price_ranges": {
      "range": {
        "field": "price",
        "ranges": [{"to": 1000}, {"from": 1000, "to": 5000}, {"from": 5000}]
      }
    }
  },
  "sort": [{ "_score": "desc" }, { "rating": "desc" }],
  "from": 0, "size": 20
}
```

### Sync Strategy — DB to Elasticsearch

```
Pattern 1 — Dual write (simple, risky):
  App writes to PostgreSQL + Elasticsearch simultaneously
  Risk: one succeeds, other fails → inconsistency

Pattern 2 — Event-driven (recommended):
  App writes to PostgreSQL → publishes ProductUpdated event to Kafka
  Elasticsearch Indexer (consumer) → indexes document in Elasticsearch
  Lag: milliseconds to seconds

Pattern 3 — Debezium CDC (no code change):
  Debezium captures PostgreSQL WAL changes → publishes to Kafka → Indexer → ES
  Works without changing application code
```

### When NOT to Use Elasticsearch

- Primary data store — use as a read model alongside a source-of-truth DB
- Simple exact-match queries — a properly indexed PostgreSQL handles this better
- ACID transactions — ES is eventually consistent, not transactional
- Small datasets — overhead not worth it below ~100K documents

---

## Topic 8 · Vector Databases — RAG Foundation

### In One Line
Vector databases store and search high-dimensional embeddings — the foundation of semantic search and Retrieval-Augmented Generation (RAG) for AI systems.

### Why Vector Search

```
Traditional search: "Find documents containing 'heart attack'"
  → Misses: "myocardial infarction", "cardiac arrest", "chest pain emergency"
  → Keyword matching only

Vector search: Convert query to embedding → find documents with similar embeddings
  → Finds "myocardial infarction" because it has similar meaning
  → Semantic similarity, not keyword match
```

### How Embeddings Work

```
Text → Embedding Model (OpenAI text-embedding-3, sentence-transformers, etc.)
     → Dense vector of 384-3072 dimensions
     → e.g., "order placed successfully" → [0.12, -0.34, 0.87, ..., 0.23] (1536 floats)

Similar meaning → vectors close together in high-dimensional space
Dissimilar meaning → vectors far apart
```

### Vector DB Options

| DB | Type | Best For | Notes |
|---|---|---|---|
| **pgvector** | PostgreSQL extension | Small-medium scale, existing Postgres | No extra infra; SQL + vectors |
| **Pinecone** | Managed cloud | Production RAG, no ops | Expensive at scale; very fast |
| **Weaviate** | Self-hosted / managed | Multi-modal, hybrid search | Open source; rich features |
| **Qdrant** | Self-hosted / managed | High performance, filtering | Rust-based; very fast |
| **ChromaDB** | Local / prototype | Development, testing | Not production-grade |
| **Amazon OpenSearch** | Managed (AWS) | AWS-native RAG | k-NN plugin |

### pgvector — PostgreSQL Extension

```sql
-- Enable extension
CREATE EXTENSION vector;

-- Table with embedding column
CREATE TABLE documents (
    id          BIGSERIAL PRIMARY KEY,
    content     TEXT,
    embedding   vector(1536),    -- OpenAI ada-002 dimension
    source      VARCHAR(100),
    created_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Create index for fast similarity search
CREATE INDEX ON documents USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);    -- lists = sqrt(row_count) roughly

-- Insert with embedding (from application)
INSERT INTO documents (content, embedding, source)
VALUES ('RBI requires data localization...', '[0.12, -0.34, ...]'::vector, 'rbi-guidelines.pdf');

-- Semantic search: find 5 most similar documents to a query embedding
SELECT content, source,
       1 - (embedding <=> '[query_embedding]'::vector) AS similarity
FROM documents
ORDER BY embedding <=> '[query_embedding]'::vector   -- <=> = cosine distance
LIMIT 5;
```

### RAG Architecture (Brief — full coverage in P9 Day 13)

```
User query: "What are the RBI data localization rules?"
      ↓
1. Embed query: OpenAI/Bedrock → query_vector[1536]
      ↓
2. Vector search: pgvector/Pinecone → top 5 similar document chunks
      ↓
3. Build prompt: "Context: [5 retrieved chunks]\n\nQuestion: What are the RBI rules?"
      ↓
4. LLM (Claude/GPT): generates answer grounded in retrieved context
      ↓
5. Return answer + source citations
```

**Chunking strategy:**
```
Document → split into chunks (500-1000 tokens with overlap)
  Overlap: chunk[n] last 100 tokens = chunk[n+1] first 100 tokens
  → Prevents context loss at chunk boundaries
  
Chunk size tradeoffs:
  Smaller chunks → more precise retrieval → less context per chunk
  Larger chunks → more context → less precise retrieval
  Typical: 512 tokens, 10% overlap
```

### Hybrid Search (Best of Both Worlds)

```
User query → 
  Full-text search (BM25/Elasticsearch) → keyword-match results
  Vector search (pgvector/Pinecone)     → semantic-match results
  Reciprocal Rank Fusion (RRF)          → merge and re-rank results

→ Catches both exact keyword matches AND semantic equivalents
→ Best retrieval quality for RAG systems
```

---

## Day 8 Quick Reference

| Topic | Key Interview Answer |
|---|---|
| DB selection | Match DB to access pattern; default to PostgreSQL; migrate out when you have a real reason |
| Composite index | Equality columns first, range/sort last; partial index for filtered subsets |
| PostgreSQL partition | Range partition by date; query pruning; DROP partition = instant archive |
| JSONB | Sparse optional attributes; GIN index for containment queries; don't replace proper columns |
| Cache-aside | Check cache → miss → load DB → store with TTL; invalidate on write |
| Write-through | Write DB + cache together; always fresh; higher write cost |
| Cache stampede | Mutex lock OR TTL jitter prevents thundering herd on expiry |
| DB-per-service | No shared schemas; cross-service data via API composition or event-driven duplication |
| Read replica | readOnly=true → replica; write → primary; watch for replication lag on immediate reads |
| Elasticsearch | text=analyzed (full-text); keyword=exact (facets); sync via Kafka events, not dual write |
| pgvector | PostgreSQL extension; cosine similarity; ivfflat index; for RAG and semantic search |
| Hybrid search | BM25 + vector search + RRF re-ranking = best RAG retrieval quality |

---

*Tags: #sql #nosql #postgresql #indexing #partitioning #JSONB #mongodb #dynamodb #cassandra #redis #cache-aside #write-through #elasticsearch #vector-db #pgvector #RAG #embeddings*
