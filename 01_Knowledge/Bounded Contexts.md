### 1. The Core Problem: One Word, Different Meanings
In large software applications, different departments use the same word to mean completely different things.
If you try to build one giant database table or one single code object to make everyone happy, your code becomes a messy trap. A change requested by one team will accidentally break a feature for a completely different team.


```
               ┌─────────────────── THE ENTERPRISE ───────────────────┐
               │                                                      │
               │                 [ THE WORD: "PRODUCT" ]              │
               │                           │                          │
               ┌───────────────────────────┼───────────────────────────┐
               ▼                           ▼                          ▼
      [ Warehouse Team ]           [ Marketing Team ]            [ Billing Team ]
• Needs: Weight & Size      • Needs: Beautiful Images    • Needs: Price & Taxes
• Doesn't care about price. • Doesn't care about weight. • Doesn't care abt size.
```

### 2. The Solution: Bounded Contexts
A **Bounded Context** is a clear boundary line drawn around a specific part of your system. <mark style="background: #FFB86CA6;">Inside that boundary, a word has exactly **one** clear meaning</mark>.

<mark style="background: #FF5582A6;">Instead of creating one giant model,</mark> <mark style="background: #BBFABBA6;">you create separate, smaller models inside their own boundaries.</mark>

```
[ BOUNDED CONTEXT CODE ISOLATION ]

  Checkout Context   ──► Only contains features for Sales & Prices.
                             │ (Sends a simple success message)
                             ▼
  Shipping Context   ──► Only contains features for Boxes & Delivery.
```

The Shipping team can rewrite their code or change their database columns entirely, and the Checkout team's code will never break.

### 3. How to Enforce Bounded Contexts in Production
To keep these boundaries safe, enterprise systems follow three strict rules:
- **Database per Service:** Contexts **never** share database tables. The Shipping database and the Checkout database are completely separate. If one service needs data from the other, it <mark style="background: #FFB86CA6;">must ask via an API call or a message broker (like Kafka).</mark>
- **Microservice Isolation:** Each Bounded Context is built as its own microservice with its own independent code repository.
- **One Team, One Codebase:** One specific engineering team owns the codebase inside a context. They do not need to hold long meetings with other departments to deploy their changes.

### 4. Simple Code Example: Separate Models
Look at <mark style="background: #ADCCFFA6;">how the **exact same product ID** is handled by two completely different code repositories:</mark>

#### Repository A: `checkout-service`

```TypeScript
// This model only cares about the financial side of the item
export class Product {
    constructor(
        public readonly productId: string,
        public readonly price: number,
        public readonly currency: string
    ) {}
}
```

#### Repository B: `shipping-service`

```TypeScript
// This model only cares about the physical handling of the item
export class Product {
    constructor(
        public readonly productId: string,
        public readonly weightInKg: number,
        public readonly boxWidthCm: number
    ) {}
}
```

### Summary Checklist

> **"Bounded Context Rules Summary:**
> 1. **One Word, One Meaning:** If a business word changes its meaning when you talk to a different team, draw a boundary and separate the code.
> 2. **No Shared Databases:** Never let two separate domains read/write to the same database tables.
> 3. **Keep Models Small:** Only write properties that are absolutely necessary for that specific service's job."