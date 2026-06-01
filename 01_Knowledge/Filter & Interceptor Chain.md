While both Servlet Filters and Handler Interceptors are designed to intercept traffic, they execute at different framework boundaries, look at different data scopes, and solve entirely separate design problems.
### 1. Structural Comparison Matrix

|**Feature**|**Servlet Filters (Wall 1)**|**Handler Interceptors (Wall 2)**|
|---|---|---|
|**Framework Layer**|Outside Spring MVC (Managed directly by the JBoss EAP deployment container)|Completely inside the Spring MVC execution context|
|**Data Scope**|Only sees low-level, raw network requests (`HttpServletRequest` text streams)|Sees the request, the response, and the _exact target Java method object_ (`HandlerMethod`)|
|**Reflection Capability**|**No.** Cannot read Controller classes, method metadata, or custom annotations|**Yes.** Can use Java reflection to read custom method labels before execution|
|**Best Used For**|Global infrastructure tasks: Security token extraction, global request/IP logging, and CORS blocking|Application-specific framework tasks: Controller method permission checks, framework metrics, and target annotations|

### 2. Implementation Blueprints
To see how these two components link together and programmatically inspect metadata inside an application context, look at this production layout:

#### Step A: Defining a Custom Marker Annotation (The Label)
<mark style="background: #FFB86CA6;">Annotations in Java do not perform actions on their own; they act as a metadata marker</mark> for downstream framework components.

```Java
package com.corporate.annotation;

import java.lang.annotation.*;

@Target(ElementType.METHOD)          // Tells Java: This label goes exclusively on methods
@Retention(RetentionPolicy.RUNTIME)   // Tells Java: Keep this label alive in memory when the app runs
public @interface RequiresAdmin {
    // Marker annotation inspected by the interceptor layer
}
```

#### Step B: The Interceptor Engine <mark style="background: #FFB86CA6;">(Reading the Label via Reflection)</mark>
The interceptor uses the Spring-provided `handler` parameter to inspect the targeted execution code path before invoking the business logic.

```Java
package com.corporate.interceptor;

import com.corporate.annotation.RequiresAdmin;
import org.springframework.stereotype.Component;
import org.springframework.web.method.HandlerMethod;
import org.springframework.web.servlet.HandlerInterceptor;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

@Component
public class RoleCheckInterceptor implements HandlerInterceptor {

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        
        // 1. Safeguard: Ensure the target handler is an actual Controller Java method (not a static resource)
        if (handler instanceof HandlerMethod) {
            HandlerMethod targetMethod = (HandlerMethod) handler;
            
            // 2. THE LINK: Use Java Reflection to see if our custom @RequiresAdmin label is present on the method
            if (targetMethod.hasMethodAnnotation(RequiresAdmin.class)) {
                
                // If the label is found, execute the targeted authorization validation:
                String role = request.getHeader("X-Corporate-Role");
                if (!"Admin".equals(role)) {
                    response.setStatus(403);
                    response.getWriter().write("Access Denied - Interceptor halted request lifecycle!");
                    
                    return false; // CRITICAL: Returning false completely breaks the HandlerExecutionChain!
                }
            }
        }
        
        return true; // Return true to allow the request to proceed to the Controller method
    }
}
```

#### Step C: The Clean Business Controller

By isolating the cross-cutting security framework logic inside the interceptor, the controller remains entirely free of repetitive authorization blocks.

```Java
package com.corporate.controller;

import com.corporate.annotation.RequiresAdmin;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/v1/orders")
public class OrderController {

    @DeleteMapping("/{id}")
    @RequiresAdmin // <── Handled automatically by RoleCheckInterceptor.preHandle() via reflection
    public ResponseEntity<String> deleteOrder(@PathVariable Long id) {
        // 100% Pure Business Logic
        orderService.deleteOrderById(id);
        return ResponseEntity.ok("Order successfully purged.");
    }
}
```

### 3. Execution Lifecycle Short-Circuiting
The core programmatic difference between a Filter and an Interceptor is how they halt bad traffic:
- **Filter Short-Circuiting:** A filter stops execution by refusing to call `filterChain.doFilter(request, response)`. It handles the response immediately, meaning the request is killed before it can ever be evaluated by Spring's `DispatcherServlet`.
- **Interceptor Short-Circuiting:** An interceptor stops execution by returning `false` inside `preHandle()`. When Spring MVC receives a `false` signal, it actively breaks the `HandlerExecutionChain` loop, prevents the targeted controller method from invoking, and triggers the `afterCompletion()` hooks of any previously executed interceptors to clean up memory structures safely.