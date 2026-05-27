The **Database Per Service** pattern means <mark style="background: #ADCCFFA6;">each microservice must completely own its own data storage.</mark> No other service is allowed to read or write directly to that database.
### 1. The Core Architecture
<mark style="background: #FFB86CA6;">In this design, data is fully private. </mark>If Service A needs data from Service B, it cannot run a SQL query against Service B's tables. <mark style="background: #ADCCFFA6;">It _must_ ask Service B for the data through an authorized API or an event message.</mark>

```
  [ CHECKOUT SERVICE ]               [ SHIPPING SERVICE ]
           │                                  │
           ▼ (Private Access)                 ▼ (Private Access)
  ┌──────────────────┐               ┌──────────────────┐
  │  Checkout DB     │               │   Shipping DB    │
  │  • orders table  │               │  • trucks table  │
  │  • prices table  │               │  • labels table  │
  └──────────────────┘               └──────────────────┘
           ▲                                  ▲
           └────────── NO DIRECT ACCESS ──────┘
             (SQL JOINS ARE STRICTLY FORBIDDEN)
```

### 2. Why Do We Do This? (The Trade-offs)
This pattern is difficult to set up, but it is necessary for large systems <mark style="background: #BBFABBA6;">because it fixes major scaling problems.</mark>

| **The Big Benefits**                                                                                                                                                     | **The Hard Challenges**                                                                                       |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------- |
| **Independent Deploys:** The Checkout team can change their table structures (add columns, change types) without breaking the Shipping service.                          | **No SQL Joins:** You cannot combine data from two services using a simple `JOIN` query anymore.              |
| **Tech Freedom:** Checkout can use a relational database (like PostgreSQL) for financial data, while Shipping can use a NoSQL database (like MongoDB) for tracking data. | **Data Consistency:** You cannot use standard database transactions (`ACID`) across multiple services easily. |
| **Blast Radius Isolation:** If the Shipping database crashes under high load, the Checkout database stays up. Customers can still pay you money.                         | **Duplicate Data:** You have to store copies of the same data in multiple places to keep services fast.       |

### 3. How to Solve the "No SQL Joins" Problem

When you split databases, the most common question is: _How do I show a webpage that needs data from both tables?_ (For example: A user's profile dashboard showing both their **Order History** and their **Shipping Status**).

You have two simple production strategies to solve this:
#### Strategy A: Command Query Responsibility Segregation (CQRS)
You build <mark style="background: #FFB86CA6;">a completely separate "Read-Only" service that listens to events from both databases and merges the data into a fast, searchable view</mark> (like an Elasticsearch or Redis index).

```
[Checkout DB] ──► (Order Event) ────┐
                                    ▼
                               [ Kafka Bus ] ──► [CQRS Read DB] ──► [ User View ]
                                    ▲
[Shipping DB] ──► (Ship Event) ─────┘
```

- **How it works:** When a user views their dashboard, <mark style="background: #BBFABBA6;">the system doesn't query Checkout or Shipping. It queries the pre-merged CQRS database instantly.</mark>

#### Strategy B: <mark style="background: #ADCCFFA6;">API Composition </mark>
##### Option 1: The API Gateway Does It (Simple Systems , Not Recommended)
Some modern API Gateways (like Kong, AWS AppSync/GraphQL) have built-in tools to <mark style="background: #ADCCFFA6;">make multiple backend calls and merge the JSON strings together</mark> before sending them back to the user.

```
               ┌─────────────────── API GATEWAY ───────────────────┐
               │                                                   │
               │  1. Receives client request                       │
               │  2. Calls /orders AND /shipping at the same time  │
[ Browser ] ──►│  3. Merges JSON A + JSON B together               │
    ▲          │                                                   │
    └──────────┼── 4. Returns single combined JSON response ───────┘
               └───────────────────────────────────────────────────┘
```

- **When to use it:** When the merge is very simple (just nesting JSON objects) and you don't want to manage another server.
- **The Problem:** <mark style="background: #FF5582A6;">It makes your Gateway heavy.</mark> <mark style="background: #BBFABBA6;">Gateways are supposed to be fast security guards (handling login tokens and rate limits). </mark><mark style="background: #FF5582A6;">If you make them do heavy data processing, they slow down.</mark>

##### Option 2: The BFF Microservice (The Industry Standard)
In serious production systems, we use a <mark style="background: #BBFABBA6;">pattern called **BFF (Backend For Frontend)**</mark>. This is a small, lightweight microservice <mark style="background: #ADCCFFA6;">written specifically to do data composition for a specific user screen.</mark>

```
               ┌───────────────┐         ┌─────────────────────────┐
               │  API GATEWAY  │────────►│      BFF SERVICE        │
               │ (Security /   │         │ (Composition / Joiner)  │
[ Browser ] ──►│  Rate Limit)  │◄────────│                         │
               └───────────────┘         └─────────────────────────┘
                                              │               │
                                       (Call /orders)   (Call /shipping)
                                              ▼               ▼
                                        [Checkout MS]   [Shipping MS]
```

- **How it works:** The Gateway <mark style="background: #BBFABBA6;">just passes the request directly to the **BFF Service**.</mark> The BFF service does the hard work: it calls the backend services, loops through the data, filters out secret fields, and formats it perfectly for the mobile app or website.
- **Why it's better:** It keeps your Gateway super fast. It also gives frontend developers total control over how data is shaped without bothering the core backend teams.

### Option 3: UI-Level Composition (The Client Join)
There is a third option where **nobody** joins the data on the server side. The web browser or mobile app makes two separate calls through the gateway and handles it right on the screen.

```
                    ┌──► Call 1 ──► [ API Gateway ] ──► [ Checkout MS ]
                    │
[ Mobile App UI ] ──┤
                    │
                    └──► Call 2 ──► [ API Gateway ] ──► [ Shipping MS ]
```

- **How it works:** The phone screen loads instantly. <mark style="background: #CACFD9A6;">It shows a spinning loading wheel next to the "Order History" section, and another spinning wheel next to the "Delivery Status" section.</mark> <mark style="background: #ABF7F7A6;">As each network call finishes, that specific part of the screen pops into view.</mark>

### Summary Checklist for your Obsidian Notes

> **"Database Per Service Manifesto:**
> 1. **Zero Shared Tables:** If two services touch the same database table, you have a tight coupling bug. You must split the table or merge the services.
> 2. **Choose the Right Tool:** Match the database type to the specific service needs. Do not force every team to use the exact same database technology.
> 3. **Accept Eventual Consistency:** Data will not sync instantly across all services. Design your user interface to handle a small 2-to-3 second delay gracefully (e.g., show 'Processing' states)."