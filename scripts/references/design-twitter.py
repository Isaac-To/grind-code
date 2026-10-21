"""Reference solution — 355. Design Twitter.

Approach: a global monotonically increasing timestamp gives every tweet a
posting order. Each user owns a list of (time, tweetId); followees live in a
per-user set. getNewsFeed merges the tweet lists of the user plus all
followees with heapq.merge (already reverse-sorted by time), taking the 10
most recent.

Invariant: (time, tweetId) pairs are appended in strictly increasing time
order, so each user's list is sorted; heapq.merge therefore streams all
candidates in globally decreasing recency, and the first 10 are the feed.
A user implicitly "follows" themselves — self is always added to the
candidate set — and unfollow only removes an explicit followee.

Complexity: postTweet/follow/unfollow O(1); getNewsFeed O(F · log T) with
F followees merged and a 10-item cut — effectively O(F + 10·log F).
"""
from __future__ import annotations

import heapq
from itertools import islice

class Twitter:

    def __init__(self):
        self.time = 0                                   # global, monotonic clock
        self.tweets: dict[int, list[tuple[int, int]]] = {}  # userId -> [(time, tweetId)]
        self.following: dict[int, set[int]] = {}        # userId -> followee ids

    def postTweet(self, userId: int, tweetId: int) -> None:
        self.time += 1                                  # strictly increasing stamp
        self.tweets.setdefault(userId, []).append((self.time, tweetId))

    def getNewsFeed(self, userId: int) -> list[int]:
        # candidates: the user plus everyone they follow (self included)
        authors = self.following.get(userId, set()) | {userId}
        # each author's tweet list is time-ascending; reversed it is
        # descending, so heapq.merge streams candidates newest-first
        streams = (reversed(self.tweets[uid]) for uid in authors
                   if uid in self.tweets)
        merged = heapq.merge(*streams, reverse=True)
        return [tweet_id for _, tweet_id in islice(merged, 10)]

    def follow(self, followerId: int, followeeId: int) -> None:
        self.following.setdefault(followerId, set()).add(followeeId)

    def unfollow(self, followerId: int, followeeId: int) -> None:
        # discard: no error if the follow edge never existed
        self.following.get(followerId, set()).discard(followeeId)
