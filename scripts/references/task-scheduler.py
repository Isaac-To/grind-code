"""Reference solution — 621. Task Scheduler.

Approach: counting + math, no simulation needed. Let `max_freq` be the
highest task frequency and `max_count` the number of tasks having that
frequency. The most frequent task forces a skeleton:
    (max_freq - 1) chunks of (n + 1) slots, plus max_count trailing slots,
giving (max_freq - 1) * (n + 1) + max_count. But if other tasks fill all the
idle gaps, no idle slots remain and the answer is just len(tasks).

Invariant: the schedule length is max(len(tasks), skeleton): you can always
fill the skeleton's gaps with the remaining tasks (there are at most
max_freq - 1 of each remaining type), and you can never beat the skeleton
because the most frequent task alone needs that many intervals.

Complexity: O(n) time to count; O(1) space (26 counters).
"""
from collections import Counter


class Solution:
    def leastInterval(self, tasks: list[str], n: int) -> int:
        freqs = Counter(tasks).values()
        max_freq = max(freqs)                    # most frequent task's count
        max_count = sum(1 for f in Counter(tasks).values() if f == max_freq)
        # skeleton: (max_freq - 1) full chunks of n+1 slots, plus one final
        # slot per task tied at max_freq
        skeleton = (max_freq - 1) * (n + 1) + max_count
        return max(len(tasks), skeleton)         # other tasks may absorb all idle
