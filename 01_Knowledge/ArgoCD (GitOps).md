## The Problem with Traditional Push Deployment Model
In a traditional pipeline, Jenkins compiles the code, builds a Docker image, and then directly connects to your production Kubernetes cluster to deploy it. This model has two structural flaws.
- **Security flaw:** <mark style="background: #FFB8EBA6;">For Jenkins to deploy, it must permanently hold admin credentials</mark> (`kubeconfig`) for your production cluster. <mark style="background: #FF5582A6;">A single Jenkins breach gives an attacker complete control over production.</mark>
- **Drift flaw:** <mark style="background: #FFB8EBA6;">If an engineer bypasses the pipeline</mark> and manually runs a `kubectl` command to change something on the cluster, <mark style="background: #FF5582A6;">Jenkins has no awareness of it</mark>. <mark style="background: #FFF3A3A6;">The cluster now runs a configuration different from what your files declare.</mark> This silent divergence is called **configuration drift**, and in a large team it compounds until things break unexpectedly.

**GitOps solves both problems by inverting who initiates the deployment.**
## The GitOps Inversion: Pull Instead of Push
<mark style="background: #FFF3A3A6;">Rather than an external CI server pushing changes into the cluster</mark>, <mark style="background: #ADCCFFA6;">you install a controller—ArgoCD—inside the cluster.</mark> <mark style="background: #BBFABBA6;">ArgoCD continuously watches a Git repository and pulls the declared configuration into the cluster itself.</mark>

- **Old way (Push):** `Jenkins ───► Kubernetes Cluster (holds admin credentials)`
- **GitOps (Pull):** `Git Repo ◄─── ArgoCD (inside cluster) (reads & self-applies)`

<mark style="background: #BBFABBA6;">No external system holds cluster credentials.</mark> <mark style="background: #D2B3FFA6;">The cluster reaches out to Git.</mark> This eliminates the credential exposure problem at the architectural level.

## The Two-Repository Strategy
ArgoCD does not read your application source code. Git does not store compiled binaries, and ArgoCD cannot deploy raw Java or Python files. <mark style="background: #ABF7F7A6;">Enterprise GitOps therefore splits all files into two completely separate repositories.</mark>
- **Repo A — Application Code Repo (Owned by Developers):** Contains source code, unit tests, and build configuration. Developers push here and open pull requests here. Jenkins watches this repo.
- **Repo B — Infrastructure Manifest Repo (Owned by DevOps/Platform Teams):** <mark style="background: #FFF3A3A6;">Contains only Kubernetes text configurations, Helm charts, or Kustomize setups.</mark> Zero application source code. <mark style="background: #ADCCFFA6;">These text files declare what the cluster should run—including a text reference to the **exact container image version** living in your registry</mark>:

```
# Inside Repo B — this is what ArgoCD reads
image: nexus.company.com/order-service:sha-abc123
```

<mark style="background: #BBFABBA6;">ArgoCD watches Repo B exclusively.</mark> It reads these text blueprints, extracts the image reference, and tells the cluster to pull that compiled binary from the registry.

## Where ArgoCD Physically Lives
ArgoCD is not a sidecar inside your application pods. It is not an agent on a worker node. <mark style="background: #ABF7F7A6;">It is a standalone application installed in its own isolated namespace—typically named `argocd`</mark>—running as a set of control pods on your cluster.
- **To watch Git:** It uses a read-only HTTPS or SSH token to poll Repo B every few minutes, or responds instantly via a Git webhook.
- **To deploy:** It does not touch your application pods directly. <mark style="background: #ADCCFFA6;">It talks to the **Kubernetes API Server**,</mark> which then handles pulling images from the registry, spinning up new pods, and terminating old ones. ArgoCD issues the instruction; Kubernetes executes it.

## The Reconciliation Loop
ArgoCD runs a continuous comparison loop. Every few seconds it compares two states:
- **Desired State:** What Repo B declares should be running.
- **Actual State:** What is physically running in the cluster right now.

```
 [ Repo B: "Run 3 replicas of sha-abc123" ]
                     │
                     ▼
                 [ ArgoCD ]
                     │
 [ Cluster: "Running 1 replica of sha-old" ]
                     │
             States don't match
                     │
          ┌──────────┴──────────┐
          │                     │
     selfHeal: true        selfHeal: false
          │                     │
    Auto-correct           Alert + wait
    cluster to Git         for manual sync
```

If the states match, ArgoCD reports **Synced** and does nothing. If anyone manually scales pods or edits a live configuration, ArgoCD detects the drift immediately. If `selfHeal` is enabled, it overwrites the manual change and restores the Git-declared state.

Git is the single source of truth. Not the cluster, and not a human's memory of what they last ran.

## How Jenkins and ArgoCD Divide the Work
Jenkins and ArgoCD are not competitors. They divide the pipeline cleanly down the middle: **Jenkins owns CI (Source Code to Published Artifact). ArgoCD owns CD (Published Artifact to Running Cluster).**

They never speak directly to each other. <mark style="background: #ABF7F7A6;">Their only communication channel is a text commit to Repo B.</mark>

### The Complete End-to-End Flow:
1. **Developer merges to main** in Repo A.
2. **Jenkins CI Runs (Watches Repo A):** Compiles code, runs tests, runs security scans, <mark style="background: #ADCCFFA6;">builds the Docker image, and pushes that image to Nexus/ECR </mark> <mark style="background: #FFB86CA6;">tagged as `sha-abc123`.</mark>
3. **The Jenkins Hand-off Step:** <mark style="background: #BBFABBA6;">Jenkins automatically edits a text file inside **Repo B**, changing one line of text</mark>: `image: sha-old ──► image: sha-abc123`. Jenkins commits and pushes this change to Repo B. Jenkins' job is now done.
4. **ArgoCD Runs (Watches/ WebHook Repo B):** Detects the new text commit, reads `image: sha-abc123`, compares it to the live cluster state, detects the drift, and <mark style="background: #FFB86CA6;">instructs the Kubernetes API to update.</mark>
5. **Kubernetes Executes:** <mark style="background: #ADCCFFA6;">Pulls the binary image `sha-abc123` from Nexus and recycles your pods safely.</mark>

The critical insight here is that<mark style="background: #BBFABBA6;"> **Jenkins writes a text file and ArgoCD reads that text file**</mark>. They are fully decoupled. If Jenkins goes offline, your live cluster remains protected by ArgoCD. If you need a rollback, you do not touch Jenkins at all.

## The Concept of the ArgoCD Mapping Object
Think of an ArgoCD Application as a **logical bridge**. It is a single tracking map that sits inside the cluster. Its only job is to <mark style="background: #FFB86CA6;">point its left hand at a specific folder in Git, and its right hand at a specific folder in the cluster</mark>.

Here is exactly how that map coordinates for our `order-service`:
### 1. The Source Boundary (Where the code comes from)
You tell the map to look exactly at your infrastructure repository (**Repo B**), but you don't let it look at the whole repository. You isolate it down to a tight path:
- **The Repository:** `https://github.com/your-company/k8s-manifests`
- **The Target Branch:** `main`
- **The Isolated Path Folder:** `services/order-service/production`

> **The Rule:** ArgoCD will now _only_ watch the text files inside the `order-service/production` folder. If someone changes the configuration for the _payment-service_ in a completely different folder, this specific map ignores it completely.

### 2. The Destination Boundary (Where the code goes)
Now you tell the map exactly where to drop those files inside your live cloud environment:
- **The Target Cluster:** Your live Production Kubernetes cluster.
- **The Target Namespace:** `production`

> **The Rule:** ArgoCD takes the specific text configuration files it found inside the Git folder `services/order-service/production` and applies them _exclusively_ to the `production` namespace inside the cluster.

### 3. The Automation Policies (How it behaves)
Finally, you turn on two security rules for this specific `order-service` mapping:
- **`prune: true` (The Clean-up Rule):** Suppose your `order-service` grows, and you have a configuration file inside your Git folder for an extra routing rule or a database connection helper. <mark style="background: #ADCCFFA6;">Later, you realize you don't need it anymore, so you delete that text file from the Git folder</mark> `services/order-service/production`. <mark style="background: #FFB86CA6;">Because `prune` is set to true, ArgoCD notices it is gone from Git and automatically deletes that exact running component from the live cluster. </mark>This prevents old, unused settings from sticking around forever.
- **`selfHeal: true` (The Anti-Tamper Rule):** Suppose an engineer gets an alert at 3:00 AM, logs directly into the production cluster console using a command line, and manually changes the memory limit of the running `order-service` container to keep it from crashing. The moment they hit enter, ArgoCD catches it. I<mark style="background: #D2B3FFA6;">t compares the live cluster to the text files inside `services/order-service/production`. It sees that Git says the memory limit should be `512MB`, but the live cluster is now set to `1024MB`. Because `selfHeal` is true, ArgoCD instantly overwrites the engineer's manual change and forces the cluster back to `512MB`.</mark>

### The Unified Visual Map
To tie it all together, this is what the tracking map looks like in action for our service:

```
  [ GIT REPOSITORY: k8s-manifests ]
                │
                └───► [ Path: services/order-service/production ] 
                                      │
                                      ▼  (Watched by)
                             ┌─────────────────┐
                             │   ARGOCD MAP    │
                             │ "order-service" │
                             └─────────────────┘
                                      │
                                      ▼  (Applied to)
                        [ KUBERNETES PRODUCTION CLUSTER ]
                                      │
                                      └───► [ Namespace: production ]
```

By setting up this clear map, the `order-service` configuration inside Git is completely locked to the live `order-service` running inside your production namespace.

## Rollbacks
Suppose pushed a change having memory leak issue in Git and **Repo B** got updated after successful CI. Now ArgoCD triggered for Deployment of <mark style="background: #FFB86CA6;">Defective Image Version (bad-commit-sha)</mark>. How will you roll back to old version?
- **GitOps rollback:** This requires exactly one standard Git command:

```Bash
git revert <bad-commit-sha>
```

The moment that revert commit merges into Repo B, ArgoCD detects the change, pulls the previous text manifest version (which points to the last known good image tag in Nexus), and restores the cluster within seconds. There is no Jenkins involvement and no manual cluster terminal commands.

## Audit trails
Audit trails come for free. <mark style="background: #FFF3A3A6;">Because every infrastructure change is a Git commit, your compliance team has a complete, tamper-proof record: who changed what, when, which PR approved it, and what the configuration looked like before and after. </mark>There is no side channel for undocumented production updates.

## Architectural Responsibility Summary

| **Component**           | **Owns**                                                                                                     | **Does NOT Own**                                              |
| ----------------------- | ------------------------------------------------------------------------------------------------------------ | ------------------------------------------------------------- |
| **Jenkins / GitLab CI** | Compiling, testing, scanning, building the image, pushing to the registry, and updating the Repo B text tag. | Anything touching the live cluster.                           |
| **Nexus / ECR**         | Storing and serving the compiled binary container images.                                                    | Any deployment logic.                                         |
| **Repo B**              | The single source of truth text file for what the cluster should run.                                        | Application source code.                                      |
| **ArgoCD**              | Cluster synchronization, drift detection, and automated self-healing.                                        | Code compilation or artifact building.                        |
| **Kubernetes API**      | Pulling the actual images from the registry and recycling the live pods.                                     | Knowing or caring where the deployment instruction came from. |