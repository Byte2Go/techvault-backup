When a user clicks a button on a browser, an HTTP request travels across the internet to your Spring Boot application server. Inside your server, this request flows through a strict, layer-by-layer pipeline before it ever reaches your Controller class.

### 1. The Thread Model (How requests are handled)
#### The Old Way: Thread-Per-Request (Tomcat Default)
- **The Problem:** Traditional servers assign one dedicated operating system thread to every single incoming HTTP request. If that thread needs to wait for a slow database query or an external API call, the thread freezes (blocks).
- **The Disaster:** Threads consume significant server memory. <mark style="background: #FF5582A6;">If you have 200 users waiting on slow database calls, all 200 Tomcat threads are frozen.</mark> New users trying to access your website will get a timeout error because the server has run out of available threads, even though the server's CPU is barely doing any work.

#### The Modern Way: Non-Blocking Event Loop (Spring WebFlux / Netty)
- **The Solution:** Modern high-scale architectures use <mark style="background: #FFB86CA6;">an asynchronous worker pool (like Netty)</mark>. A tiny number of loops (usually matching your server's CPU core count) accept incoming requests.
- <mark style="background: #ABF7F7A6;">When a request needs to wait for a database query, the thread drops a placeholder callback and immediately moves on to help the next user.</mark> <mark style="background: #D2B3FFA6;">When the database finally answers, an event triggers, and a thread wakes up to send the response back. </mark>A single server can easily handle tens of thousands of concurrent users using only a handful of threads.
### 2. The Internal Processing Pipeline (The Component Journey)
Once a request hits a standard Spring Boot application, it <mark style="background: #FFB86CA6;">passes through three distinct walls of defense and processing: **Filters**, **Interceptors**, and **AOP Aspect Advisors**.</mark>

```
[Incoming HTTP Request] 
       │
       ▼
 [1. Servlet Filter Wall]  <── Tomcat Layer (Security, Logging, CORS)
       │
       ▼
 [DispatcherServlet]       <── Spring Entry Point
       │
       ▼
 [2. Handler Interceptor]  <── Spring MVC Layer (Session, Token Check)
       │
       ▼
 [3. AOP Aspect Advisor]   <── Method Layer (Transactions, Custom Metrics)
       │
       ▼
 [Your Controller Method]  <── Your Core Business Logic
```


### Step 1: The Servlet Filter Wall (The Perimeter Guard via JBoss EAP)

#### The Normal Way (The Problem)
If you write security validation, CORS checks, or raw request logging inside your core Controller or Service logic, you break the "Separation of Concerns" rule. Your business classes become messy. Furthermore, if a malicious or bad request arrives, it travels deep into your internal Spring application routing context, wasting server memory and CPU cycles before finally being rejected.

#### The Filter Way (The Solution using JBoss EAP / Tomcat)
Filters operate at the <mark style="background: #FFB86CA6;">**Servlet Container boundary**, which is managed by JBoss EAP's web subsystem (called _Undertow_).</mark> They execute at the absolute entrance of your application network <mark style="background: #ABF7F7A6;">before the request ever touches Spring's core MVC dispatch engine</mark>.
- **How it works:** You <mark style="background: #ADCCFFA6;">write your security filters using standard Spring Security configurations</mark> inside your application code (packaged as a `.war` or `.ear` file). When you deploy your application, JBoss EAP boots up its web container first.
- <mark style="background: #BBFABBA6;">To bridge the gap between JBoss EAP and your Spring code, </mark> <mark style="background: #D2B3FFA6;">Spring registers a special class called the **`DelegatingFilterProxy`** directly into JBoss EAP's native servlet filter pipeline.</mark>
- When an HTTP request arrives, the <mark style="background: #D2B3FFA6;">JBoss EAP server processes it through this filter chain first.</mark> The `DelegatingFilterProxy` catches the request at the JBoss layer and instantly <mark style="background: #BBFABBA6;">passes it into your custom Spring Security Filter Chain.</mark>
- If a request is missing an internal token or violates a CORS policy, <mark style="background: #FFF3A3A6;">Spring Security halts the request immediately at this outer boundary and throws an error back to the user.</mark>
- **The Result:** The request is rejected early. Your core Spring MVC layout and Controller methods never have to see, parse, or process bad requests. JBoss EAP stops the bad traffic right at the border, protecting your internal application execution threads from wasting valuable enterprise computing resources.

### Step 2: The Handler Interceptor (The Framework Guard)
#### The Normal Way (The Problem)
Once a request passes the initial Filter wall, it reaches Spring's core coordinator, the `DispatcherServlet`. The `DispatcherServlet` <mark style="background: #FFB86CA6;">needs to map the request to the correct Controller class.</mark> <mark style="background: #ABF7F7A6;">If you write authorization checks, session validations, or framework inspections inside your Controller methods</mark>, <mark style="background: #FFB8EBA6;">you duplicate code across dozens of classes, making the application hard to maintain.</mark> A low-level Servlet Filter cannot easily fix this because it sits outside Spring and cannot easily inspect Spring-specific metadata like custom method annotations.

If you don't use an Interceptor, your Controller code looks like this:

```Java
@RestController
public class OrderController {

    @GetMapping("/orders/delete/{id}")
    public ResponseEntity<String> deleteOrder(@PathVariable Long id, HttpServletRequest request) {
        // PROBLEM: You have to write this check inside EVERY SINGLE protected method!
        String role = request.getHeader("X-Corporate-Role");
        if (!"Admin".equals(role)) {
            return ResponseEntity.status(403).body("Access Denied");
        }

        // Your actual business logic
        orderService.delete(id);
        return ResponseEntity.ok("Order Deleted");
    }
}
```

- **Why this is bad:** Your business method is polluted with security checks. If you have 50 controllers, you have to copy-paste this logic 50 times.

#### The Interceptor Way (The Solution)
With an Interceptor, you pull that check completely out of the Controller. You write it **once** in a dedicated Interceptor class:
```Java
@Component
public class RoleCheckInterceptor implements HandlerInterceptor {

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        // 1. Cast the "handler" object to see exactly which Controller Method is about to be called
        HandlerMethod method = (HandlerMethod) handler;
        
        // 2. The Interceptor is smart! It can look at annotations on your Controller method
        if (method.hasMethodAnnotation(RequiresAdmin.class)) {
            String role = request.getHeader("X-Corporate-Role");
            
            if (!"Admin".equals(role)) {
                response.setStatus(403);
                response.getWriter().write("Access Denied via Interceptor");
                return false; // <-- CRITICAL: Returning false COMPLETELY STOPS the request! It never hits the controller.
            }
        }
        return true; // <-- Continue down the track to the Controller
    }
}
```

Now, look how clean your Controller becomes. You just add a custom annotation (`@RequiresAdmin`), and the Interceptor handles the rest:

```Java
@RestController
public class OrderController {

    @GetMapping("/orders/delete/{id}")
    @RequiresAdmin // <-- The Interceptor reads this annotation and protects the method automatically
    public ResponseEntity<String> deleteOrder(@PathVariable Long id) {
        // 100% Clean Business Logic!
        orderService.delete(id);
        return ResponseEntity.ok("Order Deleted");
    }
}
```

##### What is the Interceptor doing differently than the `DispatcherServlet`?

| **Component**           | **Responsibility (What it does)**                                                                                                                                                                         | **What it knows**                                                                                                                       |
| ----------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| **`DispatcherServlet`** | **Traffic Router:** It reads the URL (`/orders/delete/1`) and finds out which Controller is responsible for it. It coordinates the whole lifecycle.                                                       | ==It only cares about matching URLs to Java classes.==                                                                                  |
| **`Interceptor`**       | **Process Inspector:** It stands in front of the chosen Controller. It can read the Controller's method annotations, inspect metadata, and **halt/stop the execution** before your Java method is called. | It has full access to the incoming request, the outgoing response, and the _exact Java method object_ (`handler`) that is about to run. |

Interceptors live completely **inside the Spring MVC framework**. They sit between the `DispatcherServlet` and your Controller.
- **How it works:** They provide three execution hooks: `preHandle()` (before your controller runs), `postHandle()` (after your controller runs but before the HTML/JSON view is made), and `afterCompletion()` (after everything is fully rendered). This allows you to check things like: _"Does the targeted controller method require a special user session parameter?"_
- **The Result:** It allows you to intercept requests using full knowledge of Spring's framework layout, rejecting or modifying requests right before they touch your java methods.
##### Java Reflection inside the Interceptor
When a request is moving towards your Controller, Spring passes the target controller method into the interceptor's `preHandle` method as the third parameter named `Object handler`. Inside the interceptor, we convert that generic `handler` object into a `HandlerMethod` object. Once we do that, we can use a method called **`.hasMethodAnnotation()`** to see if your custom label is sitting on top of the Controller method.

###### 1. First, we create the custom Java Annotation (The Label)
In Java, an annotation like `@RequiresAdmin` does not do anything by itself. It is just a label. The `RoleCheckInterceptor` has to explicitly search for that label using Java Reflection.

```Java
import java.lang.annotation.*;

@Target(ElementType.METHOD)          // Tells Java: This label goes on methods
@Retention(RetentionPolicy.RUNTIME)   // Tells Java: Keep this label alive when the app runs
public @interface RequiresAdmin {
    // This is just a blank label definition
}
```

###### 2. Next, the Interceptor inspects the method for that exact label
```Java
@Component
public class RoleCheckInterceptor implements HandlerInterceptor {

    @Override
    public boolean preHandle(HttpServletRequest request, HttpServletResponse response, Object handler) throws Exception {
        
        // 1. Check if the handler is actually a controller method (safeguard)
        if (handler instanceof HandlerMethod) {
            HandlerMethod targetMethod = (HandlerMethod) handler;
            
            // 2. THE LINK: We check if the controller method has our custom @RequiresAdmin label!
            if (targetMethod.hasMethodAnnotation(RequiresAdmin.class)) {
                
                // If the label IS there, we perform our security check logic:
                String role = request.getHeader("X-Corporate-Role");
                if (!"Admin".equals(role)) {
                    response.setStatus(403);
                    response.getWriter().write("Access Denied - You need Admin role!");
                    return false; // Stop the request here!
                }
            }
        }
        
        return true; // No @RequiresAdmin label found, or check passed! Keep going to the controller.
    }
}
```

###### 3. Finally, your Controller just uses the label

```Java
@RestController
public class OrderController {

    @DeleteMapping("/orders/{id}")
    @RequiresAdmin // <── The Interceptor's .hasMethodAnnotation() check finds this!
    public ResponseEntity<String> deleteOrder(@PathVariable Long id) {
        orderService.delete(id);
        return ResponseEntity.ok("Order Deleted");
    }
}
```

###### How they link together step-by-step:
1. A request comes in for `/orders/5`.
2. The `DispatcherServlet` figures out that `OrderController.deleteOrder()` should handle it.
3. Before executing that method, Spring passes `deleteOrder()` as the `handler` parameter into the `RoleCheckInterceptor`.
4. The Interceptor asks: _"Does this `handler` have the `@RequiresAdmin` annotation attached to it?"_ (`targetMethod.hasMethodAnnotation(RequiresAdmin.class)`).
5. **Yes, it does!** So the interceptor forces the security check.

### Step 3: AOP Aspect Advisors (The Method Guard)
#### The Normal Way (The Problem)
When your Controller method runs, it often needs technical routines that have nothing to do with business logic. For example, <mark style="background: #FFB86CA6;">it needs to open a database transaction before the code runs, close the transaction when it finishes, or log how many milliseconds the method took to run.</mark> Writing `transaction.begin()` and `transaction.commit()` manually in every single Java method makes code incredibly messy and duplicate.

#### The AOP Way (The Solution)
Aspect-Oriented Programming (AOP) allows you to isolate these repetitive technical routines into a separate class (an Aspect).
- **How it works:** Spring <mark style="background: #ADCCFFA6;">creates a dynamic Java proxy wrapper around your Controller or Service class.</mark> <mark style="background: #BBFABBA6;">When a request calls your method, it hits the proxy wrapper first.</mark> <mark style="background: #D2B3FFA6;">If you have annotated your method with `@Transactional`, the AOP proxy secretly opens the database transaction, allows your business code method to execute, and then cleanly commits the transaction afterward.</mark>
- **The Result:** Your business methods remain 100% clean and focus exclusively on business rules, while technical cross-cutting concerns are handled automatically by proxy shells.

### Simple Checklist for Your Notes
- **Filters are Web Container Guards:** They sit at the outermost gate (Tomcat level). They handle broad, low-level network tasks like Security, CORS, and raw request logging before Spring even wakes up.
- **Interceptors are Spring MVC Guards:** They sit at the middle gate (Spring Framework level). They <mark style="background: #FFF3A3A6;">handle framework-specific tasks like checking handler mappings or parsing web session states right before a controller method is chosen</mark>.
- **AOP Aspects are Method Wrappers:** They sit at the inner gate (Java Method level). They use dynamic proxies to automatically inject technical capabilities like `@Transactional` or performance timers around your clean business code methods.