### 12_Data_Architecture: Multi-Tenant Architecture

In an enterprise SaaS (Software as a Service) platform, you rarely build an entirely separate application stack for every single corporate client. Instead, you design a **Multi-Tenant Architecture**—a structural pattern where a <mark style="background: #FFB86CA6;">single physical instance of your application infrastructure serves</mark> multiple distinct clients, known as **Tenants**.

As an Enterprise Architect, your primary mission is to enforce **Tenant Isolation**. You must ensure that <mark style="background: #ABF7F7A6;">Tenant A (e.g., a bank) can never see, access, or alter the data of Tenant B (e.g., their primary competitor),</mark> <mark style="background: #ADCCFFA6;">even though their data flows through the exact same Kubernetes pods and database servers.</mark>

### 1. The Architectural Spectrum: Isolation vs. Cost
The fundamental decision in multi-tenancy comes down to a structural trade-off: do you optimize for absolute **security isolation** or absolute **infrastructure cost-efficiency**?

There are three primary data modeling strategies used to achieve this:
#### Strategy A: Database-per-Tenant (Isolated / High Cost)
Each tenant gets their own <mark style="background: #FFB86CA6;">completely separate, isolated physical database instance</mark>.
- **The Blueprint:** Tenant A connects to `db-tenant-a.internal`, Tenant B connects to `db-tenant-b.internal`.
- **Advantage:** Highest isolation level. You can back up or restore Tenant A's database without affecting Tenant B. It makes compliance with strict data-residency laws simple.
- **Limitation:** Extremely expensive. You are paying for idle compute power, CPU, and memory pools for every single database engine you spin up.

#### Strategy B: Schema-per-Tenant (Logical Separation / Medium Cost)
All tenants share the exact same physical database cluster, but they are <mark style="background: #FFB86CA6;">isolated into separate logical schemas or namespaces</mark>.
- **The Blueprint:** In a single PostgreSQL engine, you create separate schemas: `tenant_a.orders` and `tenant_b.orders`.
- **Advantage:** Moderate cost-efficiency. The database engine pools resources automatically, but <mark style="background: #ABF7F7A6;">tables and access permissions remain completely isolated</mark>.
- **Limitation:** Harder to scale horizontally. <mark style="background: #FFB8EBA6;">If one schema grows massively, it can consume the shared hardware disk and CPU</mark>, degrading performance for all other schemas on that instance (the "noisy neighbor" problem).

#### Strategy C: Shared Database, Shared Schema (Discriminator Column / Lowest Cost)
All tenants share the exact same physical database instance, the exact same logical schema, and the exact same tables.
- **The Blueprint:** Data is separated cleanly at the row level <mark style="background: #ABF7F7A6;">by using a mandatory tenant identifier column.</mark>

    ```SQL
    SELECT * FROM orders WHERE tenant_id = 'TENANT_A' AND order_id = 99;
    ```

- **Advantage:** Maximum cost-efficiency and pool density. You maintain a single database cluster, making indexing modifications and global application updates trivial to manage.
- **Limitation:** <mark style="background: #FFB8EBA6;">Highest risk of data leak anomalies.</mark> If a developer accidentally writes a query and forgets to append `WHERE tenant_id = ...`, Tenant A will instantly see Tenant B's data on their screen.

### 2. How the Traffic Flows (The Routing Layer)
To handle Multi-Tenancy cleanly without embedding complex branching logic throughout your business code, <mark style="background: #FFB86CA6;">you resolve the tenant identifier at the edge of your architecture using your Ingress layer.</mark>

1. **The Subdomain Handshake:** A corporate user logs into `client-a.saas-platform.com`.
2. **Edge Identification:** The <mark style="background: #ADCCFFA6;">Ingress Controller or API Gateway intercepts the HTTP request, parses the host header </mark>(`client-a`), maps it to a unique internal `Tenant ID`, and injects it as a secure HTTP header attribute (e.g., `X-Tenant-ID: T_001A`) before forwarding the traffic to your microservice pods.
3. **Context Propagation:** <mark style="background: #D2B3FFA6;">A Spring Boot filter catches the header and drops it into a thread-safe context locator</mark> (like a `ThreadLocal` storage frame) so the service layer always knows who is executing the operation.

### 3. Production Blueprint: Dynamic Shared-Schema Routing in Java
Let's look at how an architect automates row-level data isolation safely within a Shared Database engine using **Spring Data JPA** and **Hibernate Filters**. <mark style="background: #BBFABBA6;">This prevents developers from having to manually append tenant IDs to every single query.</mark>

#### 1. The Tenant Context Holder

```Java
package com.enterprise.saas.config;

public class TenantContext {
    private static final ThreadLocal<String> CURRENT_TENANT = new ThreadLocal<>();

    public static void setCurrentTenant(String tenantId) {
        CURRENT_TENANT.set(tenantId);
    }

    public static String getCurrentTenant() {
        return CURRENT_TENANT.get();
    }

    public static void clear() {
        CURRENT_TENANT.remove();
    }
}
```

#### 2. The Global Hibernate Interceptor
We attach a declarative `@Filter` definition to our base entities. This instructs the database engine to <mark style="background: #FFB86CA6;">automatically rewrite incoming SQL queries</mark> before they touch the storage kernel.

```Java
package com.enterprise.saas.domain;

import jakarta.persistence.*;
import org.hibernate.annotations.Filter;
import org.hibernate.annotations.FilterDef;
import org.hibernate.annotations.ParamDef;

@MappedSuperclass
@FilterDef(name = "tenantFilter", parameters = @ParamDef(name = "tenantId", type = String.class))
@Filter(name = "tenantFilter", condition = "tenant_id = :tenantId")
public abstract class TenantAwareBaseEntity {

    @Column(name = "tenant_id", nullable = false, updatable = false)
    private String tenantId;

    @PrePersist
    public void prePersist() {
        // Automatically stamps the tenant ID onto the record during creation
        this.tenantId = TenantContext.getCurrentTenant();
    }
}
```

#### 3. Activating the Automation Aspect
An Aspect intercepts database transactions and automatically binds the thread's active tenant token into Hibernate's engine parameters.

```Java
package com.enterprise.saas.config;

import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.annotation.Before;
import org.hibernate.Session;
import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import org.springframework.stereotype.Component;

@Aspect
@Component
public class TenantSecurityAspect {

    @PersistenceContext
    private EntityManager entityManager;

    @Before("execution(* com.enterprise.saas.repository..*(..))")
    public void injectTenantFilter() {
        Session session = entityManager.unwrap(Session.class);
        String activeTenant = TenantContext.getCurrentTenant();
        
        if (activeTenant != null) {
            // 💡 AUTOMATION: Forcefully injects the row restriction into the JPA session
            session.enableFilter("tenantFilter").setParameter("tenantId", activeTenant);
        }
    }
}
```

### 4. Architectural Selection Matrix

| **Evaluation Metrics**      | **Database-per-Tenant**                                           | **Schema-per-Tenant**                                 | **Shared Schema (Row-Level)**                                           |
| --------------------------- | ----------------------------------------------------------------- | ----------------------------------------------------- | ----------------------------------------------------------------------- |
| **Data Isolation Security** | **Absolute.** Physically distinct infrastructure boundaries.      | **High.** Logical namespace divisions.                | **Logical-Only.** Heavily reliant on application query governance.      |
| **Infrastructure Costs**    | Very High.                                                        | Medium.                                               | **Ultra-Low.** Maximizes connection and memory densities.               |
| **Noisy-Neighbor Defenses** | Perfect. Compute limits are hard-capped per instance.             | Moderate. Shares CPU but limits table locking ranges. | Poor. One heavy tenant can consume global storage IOPS bandwidth.       |
| **Schema Upgrade Paths**    | High Complexity. Requires rolling out updates across $N$ engines. | Medium Complexity. Requires multi-schema migrations.  | **Simple.** A single database mutation scripts updates for all records. |