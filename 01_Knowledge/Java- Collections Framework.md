## 📌 Arrays

### Definition
- An **array** is an **indexed collection** of a fixed number of **homogeneous data elements**.
- It represents a group of elements of the **same data type**.
- Advantage: We can represent a large number of elements using a **single variable**, improving readability.
### Limitations of Arrays
1. **Fixed Size** → Once created, <mark style="background: #FFB8EBA6;">the size cannot be increased or decreased</mark>.
    - Must know size in advance, which is not always possible.
2. **Homogeneous Elements Only** → Can store only one type of data.
    - Example: `Student[]` can store only `Student` objects.
3. **No Underlying Data Structure** → <mark style="background: #FF5582A6;">Arrays are not built on standard DS</mark>.
    - Hence, **no ready‑made methods** (search, sort, etc.).
    - Programmer must write code explicitly for every requirement.
4. **Type Restriction** → Normal arrays cannot hold heterogeneous objects.
    - Workaround: `Object[]` can store different types, but still lacks flexibility.

### Differences: Arrays vs Collections

| **Arrays**                                        | **Collections**                                    |
| ------------------------------------------------- | -------------------------------------------------- |
| Fixed in size.                                    | Growable in nature.                                |
| Not memory‑efficient.                             | ==Memory‑efficient (size adjusts dynamically).==   |
| Performance‑wise ==recommended (direct access).== | Performance not as high, but flexible.             |
| Can store **homogeneous elements only**.          | Can store **homogeneous + heterogeneous objects**. |
| No underlying DS → no ready‑made methods.         | Built on DS → ready‑made methods available.        |
| Can store **primitives + objects**.               | Can store ==**objects only** (not primitives).==   |

👉 **Key Takeaway:**
- Use **arrays** when <mark style="background: #D2B3FFA6;">performance and fixed size</mark> are priorities.
- Use **collections** when flexibility, <mark style="background: #ADCCFFA6;">heterogeneous storage, and ready‑made APIs are required.</mark>

## 📌 Collection Framework Overview

### Collection vs Collections
- **Collection** →
    - An **interface** used to represent a group of objects as a single entity.
    - Defines the <mark style="background: #FFB86CA6;">most common methods (`add`, `remove`, `size`, `iterator`, etc.).</mark>
- **Collections** →
    - A **utility class** in `java.util` package.
    - Provides static methods for operations like **sorting, searching, synchronization wrappers**.

👉 **Key Difference:**
- _Collection_ = blueprint (interface).
- _Collections_ = helper (utility class).
### 9 Key Interfaces in the Framework
1. **Collection** → Root interface.
2. **List** → Duplicates allowed, insertion order preserved.
3. **Set** → No duplicates, order not preserved.
4. **SortedSet** → Unique elements, <mark style="background: #FFF3A3A6;">in sorted order.</mark>
5. **NavigableSet** → <mark style="background: #FFB86CA6;">SortedSet + navigation methods.</mark>
6. **Queue** → FIFO, elements prior to processing.
7. **Map** → Key‑value pairs, keys unique.
8. **SortedMap** → Map with keys <mark style="background: #FFF3A3A6;">in sorted order.</mark>
9. **NavigableMap** → <mark style="background: #FFB86CA6;">SortedMap + navigation methods.</mark>

### Legacy Classes in Collection Framework
These existed before Java 1.2 and were later re‑engineered to fit into the framework:
- **Enumeration (I)** → Legacy cursor.
- **Dictionary (AC)** → Abstract class for key‑value pairs.
- **Vector (C)** → <mark style="background: #BBFABBA6;">Synchronized list.</mark>
- **Stack (C)** → Child of Vector, <mark style="background: #FFB86CA6;">LIFO.</mark>
- **Hashtable (C)** → <mark style="background: #BBFABBA6;">Synchronized map</mark>, no nulls.
- **Properties (C)** → Child of Hashtable, <mark style="background: #BBFABBA6;">String‑String pairs (config files).</mark>

###  Diagram – Big Picture
```Code
Collection Framework
   |
   +-- Collection (I)
   |      |
   |      +-- List (I) → ArrayList, LinkedList, Vector → Stack
   |      +-- Set (I) → HashSet → LinkedHashSet
   |      |             SortedSet (I) → NavigableSet (I) → TreeSet
   |      +-- Queue (I) → PriorityQueue, BlockingQueue → LinkedBlockingQueue,       |                                                      PriorityBlockingQueue
   |
   +-- Map (I)
          |
          +-- HashMap → LinkedHashMap
          +-- IdentityHashMap
          +-- WeakHashMap
          +-- SortedMap (I) → NavigableMap (I) → TreeMap
          +-- Dictionary (AC) → Hashtable → Properties
```

👉 **Key Takeaway:**
- The framework provides **interfaces** (blueprints), **classes** (implementations), and **utility classes** (helper methods).
- <mark style="background: #FFF3A3A6;">Legacy classes were adapted into the framework</mark> for backward compatibility.

## 📌 Collection Interface
### Role as Root Interface
- **Collection** is the **root interface** of the entire Collection Framework.
- It represents a **group of individual objects** as a single entity.
- Defines the ==**common/general methods**== <mark style="background: #ADCCFFA6;">applicable to all collection objects.</mark>
- No concrete class directly implements **Collection** — it serves as a **foundation** for other interfaces like ==**List, Set, Queue**==.
### Key Methods in Collection Interface
<mark style="background: #D2B3FFA6;">add, remove, clear, contains, size, toArray, iterator</mark>
1. `boolean add(Object o)` → Add single element.
2. `boolean addAll(Collection c)` → Add all elements from another collection.
3. `boolean remove(Object o)` → Remove specific element.
4. `boolean removeAll(Collection c)` → Remove all elements present in another collection.
5. `boolean retainAll(Collection c)` → Keep only elements present in another collection.
6. `void clear()` → Remove all elements.
7. `boolean contains(Object o)` → Check if element exists.
8. `boolean containsAll(Collection c)` → Check if all elements exist.
9. `boolean isEmpty()` → Check if collection is empty.
10. `int size()` → Returns number of elements.
11. `Object[] toArray()` → Convert collection to array.
12. `Iterator iterator()` → <mark style="background: #ADCCFFA6;">Get iterator to traverse elements.</mark>

### Position in Framework
```Code
Collection (I) [Root Interface]
   |
   +-- List (I) → ArrayList, LinkedList, Vector → Stack
   +-- Set (I) → HashSet → LinkedHashSet
   |             SortedSet (I) → NavigableSet (I) → TreeSet
   +-- Queue (I) → PriorityQueue, BlockingQueue → LinkedBlockingQueue,                                                              PriorityBlockingQueue
```

👉 **Key Takeaway:**
- **Collection** is the **foundation** of the framework.
- All other <mark style="background: #FFB86CA6;">interfaces (List, Set, Queue) extend it,</mark> adding specialized behavior.
- Knowing these methods is crucial for interviews — they form the **common API** across all collections.
## 📌 List Interface
- **Child of Collection.**
- Represents a group of objects where ==**duplicates are allowed** and **insertion order is preserved**.==
- Index plays a key role → allows differentiation of duplicates and <mark style="background: #BBFABBA6;">positional access</mark>.
- Defines specific methods like:
    - `add(int index, Object o)`
    - `get(int index)`
    - `remove(int index)`
    - `set(int index, Object new)`
    - `indexOf(Object o)`, `lastIndexOf(Object o)`
    - `listIterator()`

### 📌 ArrayList
- **Underlying DS:** <mark style="background: #FFB86CA6;">Resizable (growable) array.</mark>
- **Duplicates:** Allowed.
- **Insertion Order:** Preserved.
- **Nulls:** Allowed.
- **Heterogeneous Objects:** Allowed<mark style="background: #FFB8EBA6;"> (except in TreeSet/TreeMap).</mark>
- **Performance:** Best for **retrieval operations** (supports `RandomAccess`).
- **Thread Safety:** Not synchronized → <mark style="background: #FFB8EBA6;">not thread‑safe.</mark>
- **Constructors:**
    1. `ArrayList()` → <mark style="background: #ADCCFFA6;">default capacity = 10.</mark>
    2. `ArrayList(int initialCapacity)` → custom capacity.
    3. `ArrayList(Collection c)` → <mark style="background: #ADCCFFA6;">creates equivalent ArrayList.</mark>

👉 **Best choice when frequent operation = retrieval. <mark style="background: #FF5582A6;">Worst choice for middle insertions/deletions.**</mark>

### 📌 LinkedList
- **Underlying DS:** Doubly linked list.
- **Duplicates:** Allowed.
- **Insertion Order:** Preserved.
- **Nulls:** Allowed.
- **Performance:** ==Best for **insertions/deletions in the middle**==. <mark style="background: #FF5582A6;">Worst for retrieval.</mark>
- **Implements:** Serializable, Cloneable (not RandomAccess).
- **Special Methods:**
    - `addFirst()`, `addLast()`
    - `getFirst()`, `getLast()`
    - `removeFirst()`, `removeLast()`

👉 **Best choice when frequent operation = insertion/deletion.**

### 📌 Vector
- **Underlying DS:** <mark style="background: #FFB86CA6;">Resizable array.</mark>
- **Duplicates:** Allowed.
- **Insertion Order:** Preserved.
- **Nulls:** Allowed.
- **Thread Safety:** Every method <mark style="background: #D2B3FFA6;">synchronized → thread‑safe.</mark>
- **Performance:** <mark style="background: #FFB8EBA6;">Lower than ArrayList (threads wait).</mark>
- **Legacy:** Introduced in 1.0v, later re‑engineered to implement List.
- **Special Methods:** `addElement()`, `removeElement()`, `capacity()`.

👉 **Best choice when thread safety is required.**

### 📌 Stack
- **Child Class of Vector.**
- **Order:** LIFO (Last In, First Out).
- **Methods:**
    - `push(Object o)` → insert.
    - `pop()` → remove & return top.
    - `peek()` → return top without removal.
    - `empty()` → check if stack is empty.
    - `search(Object o)` → returns offset if found, else ‑1.

👉 **Best choice when LIFO order is required.**

### **ASCII Diagram – List Hierarchy**
```Code
Collection (I) [1.2v]
        |
        v
     List (I) [1.2v]   
      /     |           \
ArrayList   LinkedList   Vector [1.0v Legacy]
                         |
                         v
                       Stack
```

👉 **Key Takeaway:**
- **ArrayList** → retrieval.
- **LinkedList** → insertion/deletion.
- **Vector** → thread‑safe list (legacy).
- **Stack** → LIFO operations.

## 📌 Cursors in Java
### Definition
- A **cursor** is used to **iterate objects one by one** from a collection.
- Java provides **three types of cursors**:
    1. **Enumeration** (legacy)
    2. ==**Iterator** (universal)==
    3. **ListIterator** (bi‑directional)

### 1. Enumeration
- **Introduced in:** Legacy classes (Vector, Hashtable).
- **Direction:** Forward only.
- **Access:** Read‑only (cannot remove).
- **Methods:**
    - `hasMoreElements()` → checks if more elements exist.
    - `nextElement()` → returns next element.
- **Limitations:**
    - Works only with legacy classes.
    - Cannot remove elements.
👉 **Best choice for legacy collections.**
### 2. Iterator
- **Introduced in:** Java 1.2.
- **Direction:** <mark style="background: #FFB86CA6;">Forward only.</mark>
- **Access:** <mark style="background: #ADCCFFA6;">Read + Remove.</mark>
- **Methods:**
    - `hasNext()` → checks if more elements exist.
    - `next()` → returns next element.
    - `remove()` → removes current element.
- **Limitations:**
    - Single direction only.
    - <mark style="background: #FFB8EBA6;">Cannot replace or add new elements.</mark>
👉 ==**Universal cursor for all collections.**==

### 3. ListIterator
- **Child of Iterator.**
- **Direction:** <mark style="background: #ABF7F7A6;">Bi‑directional (forward + backward).</mark>
- **Access:** <mark style="background: #ABF7F7A6;">Read + Remove + Replace + Add</mark>.
- **Methods:**
    - Forward: `hasNext()`, `next()`, `nextIndex()`
    - Backward: `hasPrevious()`, `previous()`, `previousIndex()`
    - Modification: `remove()`, `set(Object o)`, `add(Object o)`
👉 ==**Most powerful cursor, but works only with List implementations.**==

### Comparison Table

| Feature       | Enumeration                          | Iterator                          | ListIterator                                                                       |
| ------------- | ------------------------------------ | --------------------------------- | ---------------------------------------------------------------------------------- |
| Works With    | Legacy only                          | All collections                   | List only                                                                          |
| Direction     | Forward                              | Forward                           | Forward + Backward                                                                 |
| Access        | Read only                            | Read + Remove                     | Read + Remove + Replace + Add                                                      |
| Introduced In | Legacy (1.0)                         | 1.2v                              | 1.2v                                                                               |
| Methods       | `hasMoreElements()`, `nextElement()` | `hasNext()`, `next()`, `remove()` | `hasNext()`, `next()`, `hasPrevious()`, `previous()`, `remove()`, `set()`, `add()` |

👉 **Key Takeaway:**
- **Enumeration** → legacy, <mark style="background: #FFF3A3A6;">read‑only</mark>.
- **Iterator** → universal, forward only, <mark style="background: #FFF3A3A6;">read + remove</mark>.
- **ListIterator** → advanced, bi‑directional, <mark style="background: #FFF3A3A6;">Read + Remove + Replace + Add</mark>

## 📌 Set Interface
- **Child of Collection.**
- Represents a group of objects where **duplicates are not allowed** and **insertion order is not preserved**.
- Useful when <mark style="background: #FFB86CA6;">uniqueness of elements is required</mark>.
### 📌 HashSet (C)
- **Underlying DS:** Hash table.
- **Duplicates:** Not allowed.
- **Insertion Order:** <mark style="background: #FFB8EBA6;">Not preserved.</mark>
- **Nulls:** One `null` allowed.
- **Performance:** <mark style="background: #D2B3FFA6;">Best for search operations</mark> <mark style="background: #BBFABBA6;">(constant time average).</mark>
- **Thread Safety:** Not synchronized.
👉 **Best choice when uniqueness matters and order doesn’t.**

#### 📌 LinkedHashSet (C)
- **Underlying DS:** Hash table + LinkedList.
- **Duplicates:** Not allowed.
- **Insertion Order:** <mark style="background: #ADCCFFA6;">Preserved (due to linked list).</mark>
- **Nulls:** One `null` allowed.
- **Performance:** <mark style="background: #ABF7F7A6;">Slightly slower than HashSet (because of order maintenance)</mark>.
👉 **Best choice when uniqueness + predictable iteration order are required.**

### 📌 SortedSet (I)
- **Child of Set.**
- Represents a group of **unique objects** maintained in **sorted order**.
- Example implementation: **TreeSet**.

#### 📌 NavigableSet (I)
- **Child of SortedSet.**
- Provides navigation methods:
    - `lower()`, `floor()`, `ceiling()`, `higher()` → <mark style="background: #FFB86CA6;">to fetch closest matches.</mark>
- Example implementation: **TreeSet**.

##### 📌 TreeSet (C)
- **Underlying DS:** <mark style="background: #ADCCFFA6;">Balanced Tree (Red‑Black Tree).</mark>
- **Duplicates:** Not allowed.
- **Order:** Maintains elements in **sorted order**.
- **Nulls:** `null` not allowed (throws `NullPointerException`).
- **Performance:** Logarithmic time for add, remove, search.
- **Implements:** NavigableSet.
👉 **Best choice when uniqueness + sorted order are required.**

### ⚖️ Quick Contrast

| Feature     | HashSet           | LinkedHashSet                  | TreeSet                   |
| ----------- | ----------------- | ------------------------------ | ------------------------- |
| Order       | Unordered         | ==Insertion order preserved==  | ==Sorted order==          |
| Nulls       | One allowed       | One allowed                    | ==Not allowed==           |
| Performance | Fastest           | Slightly slower                | Logarithmic               |
| Use Case    | Unique, unordered | Unique + ==predictable order== | Unique + ==sorted order== |

###  Set Hierarchy
```Code
Collection (I) [1.2v]
        |
        v
     Set (I) [1.2v]
      /           \
HashSet (C) [1.2v]   SortedSet (I) [1.2v]
      |                   |
LinkedHashSet (C) [1.4v]  NavigableSet (I) [1.6v]
                               |
                               v
                           TreeSet (C) [1.2v]
```

👉 **Key Takeaway:**
- **HashSet** → fastest, unordered.
- **LinkedHashSet** → predictable iteration order.
- **TreeSet** → sorted order, but slower.

## 📌 Comparable & Comparator
### Comparable Interface
- **Package:** `java.lang`
- **Purpose:** Used for ==**default natural ordering** of objects==.
- **Method:**
    - `int compareTo(Object o)`
        - Returns **negative** if current object < given object.
        - Returns **zero** if equal.
        - Returns **positive** if current object > given object.
- **Limitation:** Only **one sorting sequence** (==natural order==) can be defined per class.

👉 Example:
```java
class Student implements Comparable<Student> {
    int rollNo;
    public int compareTo(Student s) {
        return this.rollNo - s.rollNo; // natural order by rollNo
    }
}
```

### Comparator Interface
- **Package:** `java.util`
- **Purpose:** Used for ==**customized sorting**== of objects.
- **Method:**
    - `int compare(Object o1, Object o2)`
        - Returns **negative** if o1 < o2.
        - Returns **zero** if equal.
        - Returns **positive** if o1 > o2.
- **Advantage:** Multiple sorting sequences can be defined (e.g., by name, by age, etc.).

👉 Example:
```java
class NameComparator implements Comparator<Student> {
    public int compare(Student s1, Student s2) {
        return s1.name.compareTo(s2.name); // sort by name
    }
}
```

### ⚖️ Quick Contrast

| Feature      | Compar==able==                   | Compara==tor==                         |
| ------------ | -------------------------------- | -------------------------------------- |
| Package      | java.lang                        | java.util                              |
| Method       | `compareTo(Object o)`            | `compare(Object o1, Object o2)`        |
| Sorting Type | ==Natural ordering==             | ==Customized ordering==                |
| Flexibility  | Only one sequence                | Multiple sequences possible            |
| Modification | ==Must modify class itself==     | ==No need to modify class==            |
| Use Case     | Default order (e.g., rollNo, ID) | Custom order (e.g., name, age, salary) |

👉 **Key Takeaway:**
- Use **Comparable** when you want a **single, natural ordering**.
- Use **Comparator** when you need **multiple or custom sorting logics**.

## 📌 Map Interface
- **Not** a child of Collection.
- Represents objects as **key‑value pairs**.
- **Keys:** <mark style="background: #ABF7F7A6;">Must be unique.</mark>
- **Values:** Can be duplicated.
- Common use case:<mark style="background: #FFB86CA6;"> fast lookups, associations</mark>, dictionaries.
- **Entry Interface**
	- Inner interface of Map.
	- Represents a single key‑value pair.
	- Methods:
	    - `getKey()` → returns key.
	    - `getValue()` → returns value.
	    - `setValue(Object v)` → updates value.

### 📌 HashMap (C)
- **Underlying DS:** <mark style="background: #D2B3FFA6;">Hash table</mark>.
- **Duplicates:** Keys not allowed, values allowed.
- **Nulls:** One `null` key allowed, multiple `null` values allowed.
- **Insertion Order:** Not preserved.
- **Thread Safety:** <mark style="background: #FFB8EBA6;">Not synchronized.</mark>
- **Performance:** <mark style="background: #BBFABBA6;">Very high for search operations.</mark>
👉 **Best choice for fast key‑value lookups.**

#### 📌 LinkedHashMap (C)
- **Underlying DS:** Hash table + <mark style="background: #ADCCFFA6;">Linked</mark>List.
- **Duplicates:** Keys not allowed, values allowed.
- **Insertion Order:** <mark style="background: #ADCCFFA6;">Preserved</mark>.
- **Nulls:** One `null` key allowed, multiple `null` values allowed.
👉 **Best choice when ==predictable iteration order== of key‑value pairs is required.**

### 📌 IdentityHashMap (C)
- **Underlying DS:** Hash table.
- **Key Comparison:** Uses == (reference equality) instead of `equals()`.
- **Use Case:** When <mark style="background: #ADCCFFA6;">identity comparison is required</mark> <mark style="background: #D2B3FFA6;">(e.g., caching)</mark>.

### 📌 WeakHashMap (C)
- **Underlying DS:** Hash table with weak references for keys.
- **Garbage Collection:** <mark style="background: #D2B3FFA6;">Keys are eligible for GC </mark> <mark style="background: #ADCCFFA6;">when no longer referenced.</mark>
- **Use Case:** <mark style="background: #FFF3A3A6;">Memory‑sensitive caches.</mark>

### 📌 SortedMap (I)
- **Child of Map.**
- Stores key‑value pairs in **ascending order of keys**.
### 📌 NavigableMap (I)
- **Child of SortedMap.**
- ==Provides navigation methods==:
    - `lowerEntry()`, `floorEntry()`, `ceilingEntry()`, `higherEntry()`.
- Example implementation: **TreeMap**.
#### 📌 TreeMap (C)
- **Underlying DS:** <mark style="background: #FFB86CA6;">Balanced Tree (Red‑Black Tree).</mark>
- **Duplicates:** Keys not allowed, values allowed.
- **Order:** Keys maintained in **sorted order**.
- **Nulls:** `null` keys not allowed, but `null` values allowed.
- **Implements:** <mark style="background: #FFB86CA6;">NavigableMap.</mark>
👉 **Best choice when sorted key‑value pairs are required.**


### 📌Dictionary (AC)
#### 📌 Hashtable (C)
- **Underlying DS:** Hash table.
- **Duplicates:** Keys not allowed, values allowed.
- **Nulls:** <mark style="background: #FFB8EBA6;">Neither `null` key nor `null` value allowed.</mark>
- **Thread Safety:** <mark style="background: #FFB86CA6;">Synchronized → thread‑safe.</mark>
- **Legacy:** Introduced in 1.0v.

👉 **Best choice when thread safety is required, but generally replaced by ==ConcurrentHashMap==.**
#### 📌 Properties (C)
- **Child class of Hashtable.**
- Represents **property files** (key‑value pairs of type String‑String).
- Commonly used for configuration settings.

### ⚖️ Quick Contrast

| Feature       | HashMap                      | LinkedHashMap                | IdentityHashMap     | WeakHashMap            | TreeMap                           | Hashtable          | Properties   |
| ------------- | ---------------------------- | ---------------------------- | ------------------- | ---------------------- | --------------------------------- | ------------------ | ------------ |
| Order         | Unordered                    | Insertion order preserved    | Identity equality   | GC‑sensitive           | Sorted keys                       | Unordered          | Unordered    |
| Nulls         | 1 null key, many null values | 1 null key, many null values | Allowed             | Allowed                | No null keys, null values allowed | No nulls           | No nulls     |
| Thread Safety | Not synchronized             | Not synchronized             | Not synchronized    | Not synchronized       | Not synchronized                  | Synchronized       | Synchronized |
| Legacy        | Modern                       | Modern                       | Modern              | Modern                 | Modern                            | Legacy             | Legacy       |
| Use Case      | Fast lookup                  | Predictable iteration        | Identity comparison | Memory‑sensitive cache | Sorted map                        | Thread‑safe legacy | Config files |

### Map Hierarchy
```Code
Map (I) [1.2v]
 ├── HashMap (C) [1.2v]
 │     └── LinkedHashMap (C) [1.4v]
 ├── IdentityHashMap (C) [1.4v]
 ├── WeakHashMap (C) [1.2v]
 ├── SortedMap (I) [1.2v]
 │     └── NavigableMap (I) [1.6v]
 │           └── TreeMap (C) [1.2v]
 └── Dictionary (AC)
       ├── Hashtable (C)
       └── Properties (C) [1.0v]
```

👉 **Key Takeaway:**
- **HashMap** → fast, allows nulls, unordered.
- **LinkedHashMap** → ordered.
- **IdentityHashMap** → ==identity comparison==.
- **WeakHashMap** → GC‑sensitive cache.
- **TreeMap** → sorted keys.
- **Hashtable** → legacy, synchronized, no nulls.
- **Properties** → config files.

## 📌 Utility Classes in Java

### 1. Collections Class
- **Package:** `java.util`
- **Type:** Utility class (not interface).
- **Purpose:** Provides **static methods** to operate on Collection objects.
- **Key Features:**
    - **Sorting:** `Collections.sort(List l)` → sorts elements of a List.
    - **Searching:** `Collections.binarySearch(List l, Object key)` → searches for an element in a sorted List.
    - **Synchronization Wrappers:**
        - `Collections.synchronizedList(List l)`
        - `Collections.synchronizedSet(Set s)`
        - `Collections.synchronizedMap(Map m)`
    - **Other Utilities:**
        - `Collections.reverse(List l)` → reverse order.
        - `Collections.shuffle(List l)` → randomize order.
        - `Collections.max(Collection c)` / `Collections.min(Collection c)` → find max/min element.
👉 **Best Use Case:** When you need helper methods for sorting, searching, or thread‑safe wrappers for collections.

### **2. Arrays Class**
- **Package:** `java.util`
- **Type:** Utility class for array operations.
- **Key Features:**
    - **Sorting:** `Arrays.sort(Object[] a)` → sorts array elements.
    - **Searching:** `Arrays.binarySearch(Object[] a, Object key)` → searches in sorted array.
    - **Conversion:** `Arrays.asList(Object[] a)` → converts array into a List view.
    - **Equality Check:** `Arrays.equals(Object[] a1, Object[] a2)` → compares arrays.
    - **Fill:** `Arrays.fill(Object[] a, Object val)` → fills array with given value.

👉 **Best Use Case:** When you need quick operations on arrays (sort, search, convert to List).

### ⚖️ Quick Contrast

|Feature|Collections Class|Arrays Class|
|---|---|---|
|Operates On|Collection objects (List, Set, Map)|Arrays|
|Sorting|`Collections.sort(List)`|`Arrays.sort(array)`|
|Searching|`Collections.binarySearch(List, key)`|`Arrays.binarySearch(array, key)`|
|Conversion|N/A|`Arrays.asList(array)`|
|Synchronization|Provides sync wrappers|Not applicable|
|Utility Scope|Collections framework|Arrays only|

👉 **Key Takeaway:**
- Use **Collections class** for operations on **Collection objects**.
- Use **Arrays class** for operations on **arrays**.
## 📌 Java 1.5 Enhancements – Queue & PriorityQueue
### Queue Interface
- **Child of Collection.**
- Represents a group of elements **prior to processing** (FIFO).
- Commonly used in scheduling, buffering, and messaging systems.

### PriorityQueue
- **Introduced in Java 1.5.**
- **Underlying DS:** Heap (priority heap).
- **Order:** Elements ordered by **priority** (natural ordering or custom `Comparator`).
- **Duplicates:** Allowed.
- **Nulls:** Not allowed (throws `NullPointerException`).
- **Performance:** Logarithmic time for insertion/removal.
- **Use Case:** Task scheduling, job queues.

👉 **Best choice when elements must be processed by priority rather than insertion order.**

## 📌 Java 1.6 Enhancements – NavigableSet & NavigableMap

### NavigableSet
- **Child of SortedSet.**
- Provides navigation methods to fetch closest matches:
    - `lower(E e)` → greatest element < e.
    - `floor(E e)` → greatest element ≤ e.
    - `ceiling(E e)` → least element ≥ e.
    - `higher(E e)` → least element > e.
- Example implementation: **TreeSet**.

👉 **Best choice when sorted set + navigation is required.**

### NavigableMap
- **Child of SortedMap.**
- Provides navigation methods for key‑value pairs:
    - `lowerEntry(K k)` → entry with greatest key < k.
    - `floorEntry(K k)` → entry with greatest key ≤ k.
    - `ceilingEntry(K k)` → entry with least key ≥ k.
    - `higherEntry(K k)` → entry with least key > k.
- Example implementation: **TreeMap**.

👉 **Best choice when sorted map + navigation is required.**

### ⚖️ Quick Contrast

| Feature    | Queue                 | PriorityQueue             | NavigableSet                          | NavigableMap                          |
| ---------- | --------------------- | ------------------------- | ------------------------------------- | ------------------------------------- |
| Introduced | 1.5                   | 1.5                       | 1.6                                   | 1.6                                   |
| Order      | FIFO                  | Priority (natural/custom) | Sorted + navigation                   | Sorted + navigation                   |
| Nulls      | Allowed               | Not allowed               | Not allowed                           | Not allowed                           |
| Use Case   | Buffering, scheduling | Task/job scheduling       | Sorted set with closest match queries | Sorted map with closest match queries |
|            |                       |                           |                                       |                                       |

👉 **Key Takeaway:**

- **Java 1.5** → introduced **Queue** and **PriorityQueue** for task scheduling.
- **Java 1.6** → introduced **NavigableSet** and **NavigableMap** for advanced navigation in sorted collections.
---

## 🎯 Decision Tree: Which Collection to Use?

```
START: What do you need to store?
│
├─► Single elements (not key-value pairs)
│   │
│   ├─► Need duplicates allowed?
│   │   ├─► YES → Use LIST
│   │   │   ├─► Frequent retrieval? → ArrayList
│   │   │   ├─► Frequent insert/delete? → LinkedList
│   │   │   └─► Need thread safety? → Vector
│   │   │       └─► Need LIFO? → Stack
│   │   │
│   │   └─► NO → Use SET (unique elements)
│   │       ├─► Order not important → HashSet
│   │       ├─► Need insertion order → LinkedHashSet
│   │       └─► Need sorted order → TreeSet
│   │
│   └─► Need FIFO/processing order? → Use QUEUE
│       └─► Need priority ordering? → PriorityQueue
│
└─► Key-value pairs → Use MAP
    ├─► Need thread safety?
    │   ├─► YES → Hashtable (legacy) or ConcurrentHashMap
    │   └─► NO → Continue...
    ├─► Order not important → HashMap
    ├─► Need insertion order → LinkedHashMap
    ├─► Need sorted keys → TreeMap
    ├─► Identity-based keys → IdentityHashMap
    └─► Memory-sensitive cache → WeakHashMap
```

---

## 📋 Quick Comparison Matrix

### Group of Objects (Collection Hierarchy)

|**Feature**|**List**|**Set**|**Queue**|
|---|---|---|---|
|**Duplicates**|✅ Allowed|❌ Not allowed|✅ Allowed|
|**Order**|Preserved|Not preserved|FIFO|
|**Index**|✅ Supported|❌ Not supported|❌ Not supported|
|**Use Case**|Ordered list|Unique items|Processing queue|

### List Implementations

|**Feature**|**ArrayList**|**LinkedList**|**Vector**|**Stack**|
|---|---|---|---|---|
|**DS**|Resizable array|Doubly linked list|Resizable array|Vector|
|**Retrieval**|⚡ Fast|🐢 Slow|⚡ Fast|⚡ Fast|
|**Insert/Delete**|🐢 Slow|⚡ Fast|🐢 Slow|⚡ Fast (LIFO)|
|**Thread-safe**|❌|❌|✅|✅|
|**RandomAccess**|✅|❌|✅|✅|

### Set Implementations

|**Feature**|**HashSet**|**LinkedHashSet**|**TreeSet**|
|---|---|---|---|
|**DS**|Hash table|Hash table + LL|Balanced tree|
|**Order**|None|Insertion|Sorted|
|**Performance**|O(1)|O(1)|O(log n)|
|**Nulls**|✅ (one)|✅ (one)|❌|
|**Heterogeneous**|✅|✅|❌|

### Map Implementations

|**Feature**|**HashMap**|**LinkedHashMap**|**TreeMap**|**Hashtable**|**WeakHashMap**|**IdentityHashMap**|
|---|---|---|---|---|---|---|
|**DS**|Hash table|Hash table + LL|Red-Black tree|Hash table|Hash table|Hash table|
|**Order**|None|Insertion|Sorted|None|None|None|
|**Null Keys**|✅ (one)|✅ (one)|❌|❌|✅|✅|
|**Null Values**|✅|✅|✅|❌|✅|✅|
|**Thread-safe**|❌|❌|❌|✅|❌|❌|
|**Key Comparison**|equals()|equals()|Comparable|equals()|equals()|==|

---

## 🔄 Cursors Decision Guide

```
Need to traverse collection?
│
├─► Legacy collection (Vector, Hashtable)?
│   └─► YES → Use Enumeration (read-only)
│
├─► Any collection, only need read/remove?
│   └─► YES → Use Iterator (universal, forward)
│
└─► List implementation, need full control?
    └─► YES → Use ListIterator (bi-directional, modify)

```


### Cursors Comparison

|**Feature**|**Enumeration**|**Iterator**|**ListIterator**|
|---|---|---|---|
|**Applicable**|Legacy only|All collections|List only|
|**Direction**|Forward|Forward|Both|
|**Operations**|Read only|Read + Remove|Read + Remove + Replace + Add|
|**Methods**|2|3|9|

---

## 📐 Sorting Strategy

```
Need to sort objects?
│
├─► Single default order?
│   └─► YES → Implement Comparable (compareTo)
│
└─► Multiple custom orders?
    └─► YES → Use Comparator (compare)
```

### Comparison

|**Feature**|**Comparable**|**Comparator**|
|---|---|---|
|**Package**|java.lang|java.util|
|**Method**|compareTo(obj)|compare(o1, o2)|
|**Sorting**|Natural|Customized|
|**Flexibility**|One order only|Multiple orders|
|**Class Change**|Required|Not required|

---

## 🏆 Best Practice Quick Guide

### When to Use What?

|**Requirement**|**Recommendation**|
|---|---|
|Fast random access|**ArrayList**|
|Frequent insert/delete|**LinkedList**|
|Thread-safe list|**Vector**|
|LIFO operations|**Stack**|
|Unique elements, unordered|**HashSet**|
|Unique elements, ordered insertion|**LinkedHashSet**|
|Unique elements, sorted|**TreeSet**|
|Fast key-value lookups|**HashMap**|
|Ordered key-value pairs|**LinkedHashMap**|
|Sorted key-value pairs|**TreeMap**|
|Thread-safe map|**ConcurrentHashMap** (preferred) or **Hashtable**|
|Configuration files|**Properties**|
|Processing queue|**PriorityQueue**|
|Memory-sensitive cache|**WeakHashMap**|
|Identity-based keys|**IdentityHashMap**|

---

## 🔑 Key Decisions Summary

### 1. **List vs Set vs Map vs Queue**

```
List: Duplicates allowed, order preserved
Set:  No duplicates, order not preserved (except LinkedHashSet)
Map:  Key-value pairs, unique keys
Queue: FIFO or priority order
```



### 2. **ArrayList vs LinkedList**

```
ArrayList: ⚡ Fast retrieval, 🐢 Slow insert/delete
LinkedList: ⚡ Fast insert/delete, 🐢 Slow retrieval
```



### 3. **HashSet vs TreeSet**

```
HashSet: ⚡ Fast O(1), order not important
TreeSet: 🐢 O(log n), sorted order needed
```



### 4. **HashMap vs TreeMap**

```
HashMap: ⚡ Fast lookups, order not important
TreeMap: 🐢 O(log n), sorted keys needed
```



### 5. **HashMap vs Hashtable**

```
HashMap: Fast, allows nulls, not synchronized
Hashtable: Slow, no nulls, synchronized
```


