# Strategic DDD: Sharing the Big Map
**Strategic DDD** is just a method to break a massive, messy software system into smaller, clean pieces (like microservices). It makes sure <mark style="background: #BBFABBA6;">different coding teams do not step on each other’s toes</mark> by drawing clear lines between their projects.

### 1. Bounded Context (The Clear Meaning Boundary)
In a big company, different departments use the exact same word to mean completely different things. If you try to build one giant database table to make everyone happy, your code becomes a giant trap.

A **Bounded Context** is a strict boundary wall. Inside this wall, a word has exactly **one** meaning.

```
[ ENTERPRISE DOMAIN ]

  Context A (Dept 1 Model)  ──► [Upstream Sender]
                                     │
                               (Message Bus / Kafka)
                                     │
  Context C (Analytics Engine) ◄── [Downstream Receiver]

  Context B (Dept 2 Model)  ──► [Totally Separate Service]
  Shared Context            ──► [Global Helper Utilities]
```

#### Multi-Industry Meaning Table:

|**Word**|**Meaning in Context A**|**Meaning in Context B**|
|---|---|---|
|**"Account"**|**Bank Apps:** A wallet balance with a debit card.|**Bank Loans:** A debt record with a payment schedule.|
|**"Order"**|**Shopping Cart:** Items chosen and price checkout.|**Shipping Truck:** Box weight, size, and address.|
|**"Product"**|**Warehouse:** Storage space, height, and weight.|**Sales Web:** Price, discount code, and images.|

### 2. Context Mapping (How Services Talk)
When separate services need to share data, they **never** look inside each other's databases. They use safe communication channels:
- **Upstream / Downstream:** The service sending the data is **Upstream**. The service receiving it is **Downstream**. If the sender changes its data format, the receiver is forced to update its code to match.
- **Anti-Corruption Layer (ACL) / Translation Layer:** When your clean, modern code needs to talk to a messy, old legacy system, you don’t let the old system's weird structures ruin your code. You build an <mark style="background: #D2B3FFA6;">ACL—a small translation code block</mark> that intercepts the old format and transforms it into your clean format before processing.

## Tactical DDD: Writing the Core Code
Once your service borders are drawn, **Tactical DDD** gives you three simple tools to write safe logic: Entities, Value Objects, and Aggregates.

### 1. Entities vs. Value Objects (The Identity Rule)
Every object in your system falls into one of these two categories:

| **Pattern**      | **Definition**                                                                                                                                 | **Simple Examples**                                                                                                                 |
| ---------------- | ---------------------------------------------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------- |
| **Entity**       | Has a unique, unchanging identity tracking number (`ID`). Its features can change over time, but it stays the exact same item.                 | • _Bank:_ A plastic credit card card.<br>• _Shopping:_ A user profile account.<br>• _Logistics:_ A shipping shipping container.     |
| **Value Object** | **No Identity.** It is defined purely by its values. If you change a single value inside it, you throw away the old object and make a new one. | • _Bank:_ Money (amount, currency).<br>• _Shopping:_ Address (street, zip code).<br>• _Logistics:_ GPS point (latitude, longitude). |

#### Simple Code Blueprint: Value Object

```TypeScript
// Value Object: No ID, completely immutable, validates itself
export class Address {
    constructor(
        public readonly street: string, 
        public readonly postalCode: string, 
        public readonly country: string
    ) {
        // Safe Check: Stop bad data immediately upon creation
        if (!postalCode || postalCode.trim() === "") {
            throw new Error("Validation Failed: Postal Code cannot be empty.");
        }
    }

    // Compared by values, not by database ID
    public equals(other: Address): boolean {
        return this.street === other.street && 
               this.postalCode === other.postalCode && 
               this.country === other.country;
    }
}
```

### 2. Aggregates (The Doorkeeper Pattern)

An **Aggregate** is a<mark style="background: #FFB86CA6;"> small cluster of linked Entities and Value Objects</mark> <mark style="background: #ABF7F7A6;">that must be saved to the database together as one single package.</mark>

- **The Aggregate Root:** <mark style="background: #FFF3A3A6;">Every group has exactly one main parent boss</mark> called the Aggregate Root. External code is **forbidden** from reaching past the parent to modify children directly. You can only talk to the parent.
- **Guarding Business Rules:** The <mark style="background: #D2B3FFA6;">Aggregate Root is the single guard</mark> <mark style="background: #ADCCFFA6;">responsible for checking your business rules </mark>in memory before allowing any database writes.

```
[ AGGREGATE BOUNDARY ]

  (External API Calls)
           │
           ▼
  [ AGGREGATE ROOT PARENT ]  ◄── Single entry point & rule checker
           │
           ├──► [ Value Objects ]  ──► (Immutable details: Money, Address)
           │
           └──► [ Child Entities ] ──► (Internal list items managed by Root)
```

#### Real-World Examples:
- **Bank Accounts:** The Account is the Root parent. The `Balance` is a Value Object. The internal history logs are child elements. _The Rule:_ Balance must equal the sum of logs and cannot go below zero.
- **Shopping Order:** The Order is the Root parent. The `LineItems` are child entries. _The Rule:_ You cannot change items or address details once the status is marked as `SHIPPED`.
- **Logistics Delivery:** The Shipment is the Root parent. The `StopLogs` are child entries. _The Rule:_ A truck arrival stop cannot be recorded before the departure time.

#### Simple Code Blueprint: Aggregate Root

```Java
// Aggregate Root: Protects internal children from bad modifications
public class OrderAggregate {
    private final String orderId;            // The parent ID
    private String orderStatus;              // Internal state tracking
    private List<LineItem> lineItems;        // Protected child list
    private Address shippingAddress;         // Value Object

    // External code MUST call this public entry point method
    public void addProductItem(ProductDetails details, int quantity) {
        // 1. Check strict business rules before changing anything
        if ("SHIPPED".equals(this.orderStatus) || "DELIVERED".equals(this.orderStatus)) {
            throw new IllegalStateException("Rejected: Cannot change a completed order.");
        }
        
        // 2. Change the internal data safely under parent control
        String generatedItemId = UUID.randomUUID().toString();
        LineItem item = new LineItem(generatedItemId, details, quantity);
        this.lineItems.add(item);
    }
}
```

## Universal DDD Rule Summary

Save this quick checklist into your Obsidian vault files:
> **"Universal DDD Code Rules:**
> 1. **No Shared Database Tables:** Never let two different business services read or write to the same database tables. Keep their contexts separated.
> 2. **Repository Protection:** Only build database repository savers for the Aggregate Root parent. Never let outside code update internal child rows directly.
> 3. **Stop Using Raw Primitives:** Stop passing bare strings, integers, or floats for complex business data. Wrap them in self-checking Value Objects to block bugs at compile time."