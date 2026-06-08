In a large Single Page Application talking to many microservices, <mark style="background: #ADCCFFA6;">"state" is the data your frontend needs to remember</mark>. The architectural insight is that <mark style="background: #FFF3A3A6;">**not all data is the same kind** — and treating it all the same leads to bloated, buggy, slow apps.</mark>

The solution is to split state into three buckets based on a single question: **who owns this data?**

---
### Bucket 1 — Server State: data owned by your backend
This is data that lives in your backend microservices (e.g., a list of orders, user profile data, products catalog). Your frontend is just borrowing a copy of it to display on the screen.
- **The Problem:** If 3 different components need the `/orders` data, you don't want to make 3 separate API calls, and you don't want to manually write code to handle loading spinners, error messages, or cache expiration.
- **The Solution (React Query / SWR):** These libraries act as an **intelligent network cache layer** right inside the browser.
    - If Component A asks for `/orders`, React Query fetches it from the microservice and saves it in memory.
    - If Component B asks for `/orders` two seconds later, React Query instantly hands it the cached copy from memory instead of making a second slow network call.
    - It automatically handles background refetching when the user clicks back onto the tab, ensuring data doesn't get stale.
---
### Bucket 2 — Client State: data owned purely by the UI
This is data that your backend microservices **do not care about**. It is completely local to the user's current visual layout.
- **Examples:** Is the dark mode toggle turned on? Is the left sidebar collapsed or expanded? Is a notification modal popup currently open?
- **The Solution (Zustand / Redux):** You use a lightweight global state manager like **Zustand** to hold these UI settings. Because this data is tiny and purely visual, it stays strictly in the frontend memory and never hits an API.
---
### Bucket 3 — URL State: data owned by the browser address bar
This is data that tracks _where_ the user is looking inside a page, directly managed by the browser's URL path and query parameters (e.g., `company.com/products?category=shoes&page=2`).
- **The Problem:** If a user filters a product list to "Shoes", clicks on page 2, finds a cool item, and emails the link to a coworker, the coworker should see **exactly** page 2 of shoes when they click the link.
- **The Solution:** You do **not** store filters or pagination numbers in React Query or Zustand. You store them directly in the **URL**. The frontend application reads the URL parameters on load and configures the screen automatically. This makes your app's state entirely **bookmarkable and shareable**.

---

### The decision rule

Every time you add new data to your frontend, ask one question:

|Answer|Bucket|Tool|
|---|---|---|
|A database / microservice|Server State|React Query / SWR|
|The user's current UI session only|Client State|Zustand / Redux|
|The user's current location within a page|URL State|Browser URL / Router|

Getting this right means your components stop fighting over duplicate API calls, your global store stays lean, and your users can share or bookmark any view in your app without losing context.