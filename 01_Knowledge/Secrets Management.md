# What Problem Are We Solving?
Every application needs sensitive information such as:
- Database passwords
- API keys
- Tokens
- Certificates
The challenge is simple:

> **How can an application obtain these secrets without exposing them inside source code, configuration files, or Git repositories?**

The objective is not to hide where secrets are used—it is to ensure that **humans never need to manually handle or store them in insecure places.**

---
# Traditional Approach (Not Recommended)
In many older systems, developers directly place passwords inside configuration files or code.
```text
Developer writes password
        ↓
Password committed to Git
        ↓
Everyone with repository access can see it
        ↓
Security Risk ❌
```

Example:

```properties
db.username=admin
db.password=SuperSecret123
```

Problems:
- Password visible in Git history
- Difficult to rotate passwords
- Accidental exposure is common
- Violates security best practices

---
# Modern Approach
Instead of storing secrets inside code, we store them in a dedicated secret management service.

```text
Password stored securely in AWS
        ↓
Application requests password when needed
        ↓
AWS provides password
        ↓
Application connects to database
```

This approach ensures:

- Secrets are centrally managed.
- Password rotation becomes easier.
- Developers never need to know the actual password.
- Git repositories remain free of sensitive information.

---
# The Three Fundamental Steps

## Step 1: Store the Secret in AWS Secrets Manager
AWS Secrets Manager acts like a secure vault.

```text
AWS Secrets Manager
┌─────────────────────────┐
│ Name : db-password      │
│ Value: SuperSecret123   │
└─────────────────────────┘
```

Think of it as a cloud-based password manager.
## Step 2: Grant Permission to Access Secrets
Applications running inside Kubernetes require authorization before AWS allows them to read secrets.
This authorization is provided through **IRSA <mark style="background: #D2B3FFA6;">(IAM Roles for Service Accounts)**</mark>.

```yaml
apiVersion: v1
kind: ServiceAccount
metadata:
  name: my-app
```

Conceptually:
```text
Application
     ↓
Service Account
     ↓
IAM Role
     ↓
AWS verifies identity
     ↓
Permission granted
```

IRSA acts like a **digital identity card** for Kubernetes workloads.

## Step 3: Retrieve the Secret
The application (or another component) requests the secret from AWS.

Conceptually:
```java
String password =
        awsClient.getSecretValue("db-password");

database.connect(username, password);
```

The application receives the password and uses it to establish a database connection.
![[Pasted image 20260621223103.png]]
---
# The GitOps Challenge
In Kubernetes environments managed by ArgoCD, <mark style="background: #FFB86CA6;">everything should originate from Git</mark>.

GitOps principle:
> Infrastructure and application configuration must be declared inside Git repositories.

However, this introduces a conflict.
### We Cannot Store
```text
db.password=SuperSecret123
```

because passwords inside Git create security risks.

### We Can Store
```yaml
ExternalSecret:
  name: db-password
  remoteRef:
    key: production/db-password
```

This file contains:
- No secret value
- Only the location of the secret
Think of it as a pointer or address.

---
# [External Secrets Operator (ESO)](https://external-secrets.io/latest/)

Its responsibility is:
> Synchronize secrets from external secret stores into Kubernetes.

It behaves like an automated robot.
## Responsibilities of ESO
1. Read the pointer stored in Git.
2. Determine which AWS secret is required.
3. Retrieve the secret from AWS Secrets Manager.
4. <mark style="background: #FFB86CA6;">Create or update a Kubernetes Secret.</mark>
5. Keep Kubernetes synchronized whenever the secret changes.

# End-to-End Flow

```text
1. Secret stored in AWS
        ↓
2. Pointer definition stored in Git
        ↓
3. ArgoCD deploys the pointer
        ↓
4. External Secrets Operator reads it
        ↓
5. ESO requests secret from AWS
        ↓
6. AWS returns secret
        ↓
7. ESO creates Kubernetes Secret
        ↓
8. Application reads Kubernetes Secret
        ↓
9. Application connects to database
```

---

# Architecture Overview

```text
                 ┌──────────────┐
                 │     Git      │
                 │ (No Secrets) │
                 └──────┬───────┘
                        │
                        ▼
                 ┌──────────────┐
                 │    ArgoCD    │
                 │   Deploys    │
                 └──────┬───────┘
                        │
                        ▼
        ┌───────────────────────────────────┐
        │            Kubernetes             │
        │                                   │
        │   External Secrets Operator (ESO) │
        │              │                    │
        │              ▼                    │
        │      Kubernetes Secret            │
        │              │                    │
        │              ▼                    │
        │         Java Application          │
        └──────────────┬────────────────────┘
                       │
                       ▼
               ┌──────────────┐
               │ AWS Secrets  │
               │   Manager    │
               └──────────────┘
```

---

# The Big Idea
At no point is the password:
- Stored in Git
- Hardcoded in source code
- Written in configuration files
- Manually copied by developers

The secret travels automatically:
```text
AWS Secrets Manager
        ↓
External Secrets Operator
        ↓
Kubernetes Secret
        ↓
Application
```

Human involvement is eliminated.

---

# Password Rotation
Suppose database passwords change every 30 days.

| Aspect                          | Without Auto-Rotation                  | With Auto-Rotation                       |
| ------------------------------- | -------------------------------------- | ---------------------------------------- |
| **App has hardcoded password?** | ❌ No                                   | ❌ No                                     |
| **Where is password?**          | In AWS Secrets Manager                 | In AWS Secrets Manager                   |
| **How app gets it?**            | Reads from AWS at startup              | Reads from AWS at startup                |
| **What changes?**               | The SECRET changes in AWS              | The SECRET changes in AWS                |
| **Who updates the SECRET?**     | **HUMAN** updates AWS manually         | **AWS LAMBDA** updates AWS automatically |
| **App restarts needed?**        | ✅ YES (must restart to read new value) | ❌ NO (ESO updates without restart)       |

Without automation:
```text
DB Password Changes
        ↓
Developers update configuration
        ↓
Redeploy applications
        ↓
High operational effort
```

With External Secrets Operator:
```text
Password changes in AWS
        ↓
ESO periodically checks AWS
        ↓
Detects new value
        ↓
Updates Kubernetes Secret
        ↓
Applications use the latest password
```

This enables automated secret rotation.

---

# Role of Each Component

| Component                           | Purpose                                                   |
| ----------------------------------- | --------------------------------------------------------- |
| **AWS Secrets Manager**             | Secure storage for passwords and secrets                  |
| **IRSA**                            | Provides identity and permissions to Kubernetes workloads |
| **Git Repository**                  | Stores secret references, never actual values             |
| **ArgoCD**                          | Deploys resources defined in Git                          |
| **External Secrets Operator (ESO)** | Synchronizes secrets from AWS into Kubernetes             |
| **Kubernetes Secret**               | Stores secrets inside the cluster                         |
| **Application**                     | Consumes the secret to perform its work                   |


---

## One-Line Summary
> **Secrets stay in AWS, Git stores only references, External Secrets Operator synchronizes them into Kubernetes, and applications consume them securely without humans ever managing passwords directly.**