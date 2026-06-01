In a highly regulated, high-concurrency banking environment like a Finance Subledger system, **the second option—Dual Running without changing the Mainframe system until all functionality is migrated (the Strangler Fig Pattern)—is overwhelmingly preferred.**

Removing features piece-by-piece directly from the Mainframe in the early stages introduces immense architectural risk and technical debt.

Here is the strategic breakdown of why you choose Dual Run, and how you defend this choice to an executive panel.

## ❌ Why Option 1 (Piecemeal Removal) is High-Risk

- **Monolithic Tight Coupling:** Mainframe systems are highly interconnected. A single COBOL program often handles data verification, ledger calculations, and reporting all in one place. Trying to cut out one specific feature creates a "spiderweb effect," forcing you to constantly modify and patch the legacy COBOL code just to keep the remaining features alive.
    
- **The Latency Trap:** If you remove Feature A from the Mainframe and move it to a cloud microservice, but Features B and C remain on the Mainframe, the Mainframe will have to make a network call (via an API gateway) to the cloud mid-batch. Doing this millions of times during a tight nightly batch window will introduce devastating network latency, causing the Mainframe batch run to fail its SLA.
    
- **No Safety Net:** If your newly built microservice suffers an outage or a data calculation bug on day one, your entire financial pipeline halts because the legacy code for that feature has already been deleted.
    

## 🛡️ Why Option 2 (Dual Run / Strangler Fig) is the Enterprise Standard

- **Zero-Downtime Rollback (Safety):** During a Dual Run, the Mainframe remains the undisputed **System of Record**. Your new Java microservices run in "shadow mode," processing the same live data streams in parallel. If the microservice fails, crashes, or encounters a rounding error, production operations are completely unaffected. You simply fix the Java code and restart the shadow container.
    
- **Deterministic Validation:** It gives you the ability to run **Automated Reconciliation**. You can write automated scripts that compare the output of the Mainframe DB2 database with your new Oracle/Cloud database row-by-row, penny-by-penny. You only decommission the Mainframe component after the dual run produces 100% mathematical alignment across critical cycles, like a full month-end close.
    
- **Clean Architectural Boundaries:** Your development team doesn't waste time writing throwaway "bridge code" inside the old COBOL codebase. They can focus 100% of their energy on building clean, modern, future-proof Spring Boot APIs and Spring Batch pipelines.
    

## 🎯 Architecture Panel Defense Script

> **Interviewer:** _"If you have to migrate a core legacy system, would you prefer to carve out features one by one from the Mainframe and replace them with microservices, or would you run them in parallel until the entire system is ready to cut over?"_
> 
> **Your Script:** *"For a critical, high-volume tier-1 platform like a Finance Subledger, my definitive recommendation is to utilize a **Dual-Run strategy via the Strangler Fig Pattern, keeping the Mainframe codebase completely untouched until we are ready for a phased cutover**.
> 
> Carving out features directly from the Mainframe piece-by-piece creates massive architectural risk. It forces us to constantly modify highly coupled legacy COBOL code and introduces severe cross-network latency bottlenecks during critical batch windows if a Mainframe job has to wait on a cloud microservice mid-stream.
> 
> By choosing a Dual-Run strategy, we maintain the Mainframe as our stable System of Record while streaming identical data payloads asynchronously to our new Spring Boot and Spring Batch services. This allows us to implement continuous, automated nightly reconciliations to verify data accuracy down to the exact penny without impacting live business operations. We only redirect the true system of record to the Java ecosystem after a complete, flawless financial cycle has been proven in the shadow environment, guaranteeing a zero-downtime, risk-free migration."*