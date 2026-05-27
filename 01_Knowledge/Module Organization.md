Module organization defines how top-level packages, directories, and classes are grouped inside a project repository. The chosen pattern directly dictates how easy it is to maintain, scale, and navigate a codebase as it grows.

### The Evolution: Horizontal vs. Vertical Slicing

#### Pattern 1: Package-by-Layer (Horizontal Slicing)
The traditional approach groups code purely by its **technical role** or framework component type at the root folder level.

```
com.company.myapp
 ├── controllers/       <--- Every API route in the app mixed together
 │    ├── UserController.java
 │    └── OrderController.java
 ├── services/          <--- Every business logic service mixed together
 │    ├── UserService.java
 │    └── OrderService.java
 └── repositories/      <--- Every database access layer mixed together
      ├── UserRepository.java
      └── OrderRepository.java
```

- **The Pitfall:** High coupling, low cohesion. As the application grows, these folders become massive dumping grounds. Fixing a single bug in the "Order Checkout" flow forces you to hunt through three or four completely different top-level folders to find the related files.
    

#### Pattern 2: Package-by-Feature (Vertical Slicing)
The modern industry <mark style="background: #BBFABBA6;">standard groups code by **business capability** or domain feature first</mark>. <mark style="background: #ADCCFFA6;">Technical groupings are nested inside each feature to keep things tidy.</mark>

```
com.company.myapp
 ├── user/                    
 │    ├── controller/         <--- Technical sub-grouping for User API
 │    ├── service/            <--- Technical sub-grouping for User Logic
 │    └── dao/                <--- Technical sub-grouping for User DB
 ├── product/                 
 │    ├── controller/         
 │    ├── service/            
 │    └── dao/                
 └── order/                   <--- Top-Level Business Feature Module
      ├── controller/          
      │    └── OrderController.java
      ├── service/             
      │    ├── OrderService.java
      │    └── PaymentService.java
      └── dao/                 
           ├── OrderDao.java
           └── OrderRowMapper.java
```

### W[[Module Organization]]hy the Hybrid (Feature → Layer) Approach Wins
This layout blends business-driven organization at the macro level with clean technical separation at the micro level.
- **Locality of Change (High Cohesion):** If you need to modify how orders or payments work, your changes are completely contained within the `/order` directory tree. You do not touch other domains.
- **Encapsulation & Access Control:** In Java, you can leverage default **package-private visibility** (omitting `public`). By keeping the `OrderDao` package-private inside the order package tree, you ensure that external modules (like `user` or `product`) cannot bypass boundaries to query order tables directly. They are forced to talk through the public `OrderService` API.
- **Microservices Readiness:** If a specific feature experiences massive traffic and needs to be broken out into its own standalone microservice later, you can cleanly lift the entire feature folder out of the project with minimal friction.

### Cross-Module Governance Rules
To prevent a Package-by-Feature codebase from turning into an unmaintainable "big ball of mud," architects enforce two strict communication rules:
#### 1. Feature Isolation
<mark style="background: #D2B3FFA6;">Modules are allowed to interact with each other **only** through public Service interfaces.</mark> An `OrderService` is never allowed to directly import or invoke an `UserDao`. It must request information via the public `UserService`.

#### 2. The Shared Kernel
For cross-cutting <mark style="background: #FFF3A3A6;">code that belongs to the entire infrastructure (such as global logging filters, JWT security token parsers, or uniform error wrappers)</mark>, <mark style="background: #ADCCFFA6;">place them in a dedicated, standalone utility directory completely separate from your business features</mark>:

```
com.company.myapp
 ├── user/
 ├── order/
 └── shared/           <--- Common utilities used by all features
      ├── security/
      └── logging/
```

### Summary Checklist for your Obsidian Index

> **"Module Organization Guidelines:**
> - **Group by Domain First:** Slice code vertically by business domain at the root level (`/user`, `/order`) to establish clear boundaries.
> - **Group by Layer Second:** Slice code horizontally _inside_ each feature module (`/controller`, `/service`, `/dao`) to keep responsibilities separate.
> - **Protect Data Boundaries:** Enforce public service boundaries to prevent features from directly modifying each other's underlying database structures."