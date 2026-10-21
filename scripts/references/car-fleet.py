"""Reference solution — 853. Car Fleet.

Approach: a car's arrival time is (target - position) / speed. Sort cars
by position and process from the one closest to the target backwards.
A car catches the fleet ahead iff its own arrival time is <= the fleet's
arrival time — then it merges and never leads. If it would arrive
later, it can never catch up: it leads a brand-new fleet.

Invariant: `lead_time` is the arrival time of the current (slowest-
leading) fleet. Each car either joins the current fleet (time <= lead)
or becomes the leader of a new one (time > lead), updating lead_time.
Counting leaders counts fleets.

Key insight: position and speed never change after a merge (fleets move
at the lead car's pace), so comparing fixed solo arrival times suffices
— a car can only merge into a fleet that arrives *no later* than it.

Complexity: O(n log n) time for the sort, O(n) for the sweep;
O(n) space (or O(1) extra if sorted in place).
"""
from __future__ import annotations


class Solution:
    def carFleet(self, target: int, position: list[int], speed: list[int]) -> int:
        # pair up (position, speed) then order by position DESCENDING,
        # i.e. closest to the target first
        cars = sorted(zip(position, speed), reverse=True)
        fleets = 0
        lead_time = 0.0  # arrival time of the fleet currently being built
        for pos, spd in cars:
            time = (target - pos) / spd  # solo arrival time
            if time > lead_time:
                # cannot catch the fleet ahead — this car starts a new fleet
                fleets += 1
                lead_time = time  # and becomes its (slowest) leader
            # else: arrives no later than the fleet ahead -> merges, ignored
        return fleets
