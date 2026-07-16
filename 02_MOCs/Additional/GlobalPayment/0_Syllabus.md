| Day | Focus                                                                     |
| --- | ------------------------------------------------------------------------- |
| 1   | Payment Domain Fundamentals + Payment Flow                                |
| 2   | B2B APIs, API Gateway, Security, OAuth2, Idempotency                      |
| 3   | Kafka, RabbitMQ, SQS/SNS, Event-Driven Architecture                       |
| 4   | Scalability, Concurrency, Distributed Systems                             |
| 5   | System Design (Payment Gateway, Merchant Onboarding, Notification System) |
| 6   | High Availability, DR, PCI-DSS, Tokenization, HSM, Observability          |
| 7   | Full mock interview with architecture scenarios and follow-up questions   |

These modules are interconnected, not isolated.

```
Payment Domain
        │
        ▼
API Integration
        │
        ▼
Messaging (Kafka/RabbitMQ)
        │
        ▼
Scalability
        │
        ▼
Distributed Systems
        │
        ▼
Security
        │
        ▼
Architecture Decisions
        │
        ▼
System Design
```

---

# Module 1 (Highest Priority)

# Payment Architecture

This should be the first module.

Not because you need to become a payment expert. Because every design question will use payment terminology.

Need to know:
- Merchant
- Customer
- Issuer
- Acquirer
- Card Network
- Payment Gateway
- Payment Processor
- Authorization
- Capture
- Clearing
- Settlement
- Funding
- Chargeback
- Refund
- Reversal
- Tokenization

Then understand

```
Customer

↓
Merchant

↓

Gateway

↓

Acquirer

↓

Visa

↓

Issuer

↓

Authorization

↓

Settlement

↓

Funding
```

Until this is crystal clear.

---

# Module 2 (Highest Priority)

## B2B API Integration

This is where your experience aligns perfectly.

Need to master

- REST
- OpenAPI
- Versioning
- Backward Compatibility
- SDK
- Webhooks
- API Gateway
- JWT
- OAuth2
- mTLS
- Rate Limiting
- Throttling
- Retry
- Idempotency
- Correlation ID
- Trace ID
- Error Handling

Expect questions like

> Design Merchant API.

---

# Module 3

## Messaging

Not Kafka syntax.

Architecture.

Need to know

Kafka

RabbitMQ

SQS

SNS

ActiveMQ

Need to answer

Why Kafka?

Why MQ?

Ordering?

Partition?

Consumer Group?

Exactly Once?

At Least Once?

Dead Letter Queue?

Retry?

Replay?

---

# Module 4

## Scalability

This will definitely come.

Need to know

Horizontal Scaling

Vertical Scaling

Auto Scaling

Stateless Services

Load Balancer

Redis

Caching

CDN

Connection Pooling

Thread Pool

Queue

Backpressure

---

# Module 5

## Distributed Systems

Very important.

Topics

Idempotency

Circuit Breaker

Saga

CQRS

Event Sourcing

Outbox Pattern

Distributed Lock

Optimistic Locking

Pessimistic Locking

Eventually Consistent

CAP Theorem

---

# Module 6

## API Security

Round 2 already exposed this as a weaker area.

Need to know

OAuth2

JWT

OIDC

mTLS

TLS

PCI DSS

HSM

Vault

Secrets

Encryption

Field Level Encryption

Tokenization

Masking

API Keys

Replay Attack

Nonce

---

# Module 7

## High Availability

Need to know

Multi AZ

Multi Region

Active Active

Active Passive

Failover

Split Brain

RTO

RPO

Disaster Recovery

Chaos Engineering

Health Checks

Graceful Degradation

---

# Module 8

## Architecture Decisions

This is where senior architects shine.

Questions like

Why Kafka instead of RabbitMQ?

Why REST instead of gRPC?

Why SQL instead of NoSQL?

Why Sync instead of Async?

Why Microservices instead of Modular Monolith?

Why Redis?

Why Event Driven?

Why Webhooks?

Trade-offs are more important than definitions.

---

# Then comes System Design

I don't think they'll ask

> Design Facebook.

Instead they'll ask things close to their business.

Examples:

Design Merchant Onboarding Platform

Design Payment Gateway

Design Notification Platform

Design Transaction Status API

Design Settlement Platform

Design Reconciliation Platform

Design Partner Integration

Design Payment Routing Engine

Design Fraud Detection Pipeline

----
A structured course with **10 modules** containing:

- **~150 high-probability interview questions**, ordered from basic to expert.
- **Architecture diagrams** for every major payment flow and system.
- **Trade-off discussions** (e.g., Kafka vs RabbitMQ, REST vs gRPC, SQL vs NoSQL).
- **Model answers** tailored to your resume and experience, so you can answer authentically rather than memorizing.
- **Real Global Payments–style system design scenarios**, including partner onboarding, merchant integration, payment routing, notifications, settlement, reconciliation, and high-availability design.