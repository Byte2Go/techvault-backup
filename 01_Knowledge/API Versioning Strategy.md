## I. The Core Philosophies: When to Version?
A common mistake is versioning too early. <mark style="background: #ADCCFFA6;">You should only introduce a breaking version change when a modification **violates the consumer's expectations** (backward incompatibility).</mark>

- **Non-Breaking Changes (No Version Bump Required):**
    - Adding a new optional field to a JSON response payload.
    - Adding a brand-new endpoint (`/api/v1/analytics`).
    - Changing the internal database logic while keeping the data payload structure identical.
- **Breaking Changes (Mandatory Version Bump):**
    - <mark style="background: #FFF3A3A6;">Removing a field entirely or renaming an existing field key</mark> (e.g., changing `user_id` to `id`).
    - Changing data types (e.g., converting a single string field `address` into a nested object `{ street, zip }`).
    - <mark style="background: #D2B3FFA6;">Modifying validation constraints</mark> (e.g., making a previously optional field mandatory).

## II. The 3 Major Versioning Patterns & Trade-offs
There are three primary ways to <mark style="background: #ABF7F7A6;">signal an API version at the network layer</mark>. Each has dramatic implications for caching and ingress routing.
### 1. URL Path Versioning (The Industry Favorite)
The version number is baked <mark style="background: #FFB86CA6;">explicitly into the URI path structure</mark>.
- **Example:** `GET https://api.example.com/v1/orders/123`
- **Architectural Mechanics:** The API Gateway or Edge Ingress uses simple prefix-based regex matching (e.g., if path starts with `/v1/`, route to `order-service-v1` deployment pod).

### 2. Header-Based Versioning (Custom Headers)
The client sends the resource request to a generic URL, passing the <mark style="background: #FFB86CA6;">target version via a custom HTTP header</mark>.
- **Example:** `GET https://api.example.com/orders/123`
- **Header:** `X-API-Version: 2.0`
- **Architectural Mechanics:** The <mark style="background: #FFB8EBA6;">routing engine must explicitly parse the HTTP headers of every single incoming packet</mark> before making a routing decision.

### 3. Media Type / Content Negotiation Versioning (REST Purest)
The client uses the standard HTTP `Accept` header to demand a specific versioned representation of the resource.
- **Example:** `GET https://api.example.com/orders/123`
- **Header:** `Accept: application/vnd.company.v2+json`

## III. Deep-Dive Comparison Matrix

| **Strategy**            | **Caching Compatibility (CDNs)**                                                                         | **Ingress Routing Complexity**                                                | **Client Discovery / Readability**                                       | **Best Used For**                                                           |
| ----------------------- | -------------------------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------- | ------------------------------------------------------------------------ | --------------------------------------------------------------------------- |
| **URL Path**            | 🟢 **Perfect.** The unique URI serves as an ideal cache key for any standard edge cache or CDN.          | 🟢 **Low.** Simple string prefix matching at the proxy layer.                 | 🟢 **Excellent.** Completely transparent and readable.                   | ==**Public-facing Open APIs, B2B integrations, Saas developer products.**== |
| **Custom Header**       | 🔴 **Poor.** Requires CDNs to support complex `Vary` headers, often resulting in lower cache-hit ratios. | 🟡 **Medium.** Proxy must look deep into the packet headers for routing.      | 🟡 **Moderate.** Hides versioning inside code configuration.             | **Internal microservices, private mobile app backends (BFF).**              |
| **Content Negotiation** | 🔴 **Poor.** Suffers from severe cache-fragmentation at the CDN edge due to standard browser defaults.   | 🔴 **High.** Heavy parsing burden on API gateways to extract version strings. | 🔴 **Low.** Harder for humans to test quickly via standard browser tabs. | **Strictly REST-compliant hypermedia architectures.**                       |

## IV. Enterprise Implementation Patterns
When you launch `v2`, you <mark style="background: #FF5582A6;">don't want to maintain two entirely separate, duplicating codebases forever.</mark> Use these three patterns to handle the transition smoothly at the backend layer.

### 1. The Gateway Translation Pattern (Anti-Corruption Layer)
If `v2` introduces a massive shift in structure, you can deploy your core business logic using _only_ the new `v2` format, and delegate the transformation of old `v1` <mark style="background: #ADCCFFA6;">requests to your API Gateway or an intermediary adapter service.</mark>

```
[v1 Client] ──>/v1/users ──> [API Gateway] ──(Translates format)──> [Core App_v2]
[v2 Client] ──>/v2/users ───────────────────────────────────────────┘
```

- **Why it's used:** It protects your primary microservices from "code rot" and messy `if/else` version checks.
### 2. Code-Level DTO Mapping (The Application Layer Approach)
<mark style="background: #FFF3A3A6;">Inside your application code, keep a single controller layer</mark> <mark style="background: #BBFABBA6;">but route requests to different Data Transfer Objects (DTOs) based on version</mark>, mapping them cleanly to a shared domain model.

```
@GetMapping("/v1/users")
public UserResponseV1 getUserV1(String id) {
    UserDomain user = userService.findById(id);
    return modelMapper.convertToV1(user); // Map to old contract
}

@GetMapping("/v2/users")
public UserResponseV2 getUserV2(String id) {
    UserDomain user = userService.findById(id);
    return modelMapper.convertToV2(user); // Map to new contract
}
```

### 3. Sunset & Deprecation Policy (Lifecycle Governance)
Never launch a version without an explicit deprecation strategy. Always signal deprecation cleanly using standard HTTP response headers to prevent breaking clients down the line:
- **`Deprecation: true`** (Tells the client this version is outdated).
- **`Sunset: Tue, 01 Jun 2027 23:59:59 GMT`** (Gives the exact date the server will physically shut down the endpoint).
- Return a `410 Gone` status code once the sunset date passes and the endpoint is permanently deactivated.

### Suggested Cross-Links for your Knowledge Graph:
- `[[21_Backward_Compatibility_Data_Governance]]` $\rightarrow$ Connect this directly with your data schema evolution strategies (Avro/Protobuf backward compatibility).
- `[[25_API_Gateway_Rate_Limiting]]` $\rightarrow$ Map how the edge proxy routes `/v1/` vs `/v2/` paths to different target groups.
- `[[31_Architecture_Tradeoff_Compendium]]` $\rightarrow$ Cross-reference the caching vs. routing trade-off of URL vs Header choices.