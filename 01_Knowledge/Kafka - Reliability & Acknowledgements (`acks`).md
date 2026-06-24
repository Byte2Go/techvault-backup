When a producer writes a message, it doesn't just hope for the best. It waits for a receipt called an **Acknowledgement (ACK)**.
How you configure the `acks` property determines the balance between **raw speed** and **zero data loss**.

### 1. The Three ACK Modes

#### Mode 1: `acks=0` (Fire and Forget)
- **How it works:** The producer pushes the message onto the network wire and immediately assumes success. It never waits for a response.
- **Pros:** Fastest throughput; zero network latency overhead.
- **Cons:** Highest risk of data loss. If the broker crashes while the packet is mid-flight, the message vanishes forever.


#### Mode 2: `acks=1` (Leader Only — Default)
- **How it works:** The producer waits for confirmation from the **Partition Leader only**.
- **The Flow:** Producer $\rightarrow$ Leader writes to disk $\rightarrow$ Returns ACK $\rightarrow$ Success.
- **The Risk:** If the Leader crashes _immediately_ after sending the ACK but _before_ its Followers finish copying that offset, the message is permanently lost when a follower is promoted to the new leader.

#### Mode 3: `acks=all` (Full Quorum — Safest)
- **How it works:** The producer waits until **both the Leader and all healthy Followers** have written the message to disk.
- **The Flow:** Producer $\rightarrow$ Leader $\rightarrow$ Followers Sync $\rightarrow$ Full ACK $\rightarrow$ Success.
- **Pros:** Absolute durability. If the leader dies, the newly elected leader already has a perfect copy of the message.
- **Cons:** Slightly higher latency per write.

### 2. Quick-Reference Cheat Sheet

|**Setting**|**Who Waits?**|**Performance**|**Risk Profile**|**Production Use Case**|
|---|---|---|---|---|
|**`acks=0`**|Nobody|Highest|Extreme Data Loss|Non-critical metrics, clickstream tracking|
|**`acks=1`**|Leader Only|Balanced|Moderate (Loss on Leader crash)|Standard logs, cached states|
|**`acks=all`**|Leader + Followers|Slightly Slower|**Zero Data Loss**|Financial transactions, Orders, Billing|

### 3. The Retry Problem
If a broker crashes exactly while a message is traveling over the network, `acks=all` saves the day by refusing to send an ACK. The intelligent Kafka client catches the timeout exception and **automatically retries** the transmission to the new leader.

#### The Duplicate Trap
But what if the Leader _did_ write the message, but the network wire snapped right before the ACK could make it back to the producer?
1. The producer assumes the write failed because it received no ACK.
2. The producer automatically triggers a **Retry**.
3. The new leader accepts the retry and writes the message _again_.

**Result:** You now have a duplicate event on disk (e.g., `Order Created` written twice), breaking data integrity.

To prevent network retries from creating duplicates or scrambling order, Kafka uses a core feature called **Producer Idempotence**.