"""Reference solution — 271. Encode and Decode Strings.

Approach: length-prefixed framing. Encode each string as
"<length>#<contents>" and concatenate; decode re-reads the length up to
the delimiter '#', then slices exactly that many characters. Because the
prefix is a decimal number followed by '#', and '#' can never appear in
a length, the boundary between frames is unambiguous even if the payload
itself contains '#' characters.

Invariant: encode produces frames such that decode, reading strictly left
to right, recovers each original string exactly once: the first '#'
after the cursor always terminates the length (digits only precede it),
and the next `length` characters are the payload. So decode(encode(strs))
== strs for any list of ASCII strings, including empty strings and an
empty list (which encode maps to "" — decode of "" yields []).

Complexity: O(total characters) time each way; encode output size is
input size plus O(len(strs) * digits) framing; O(1) extra work space
beyond the output (no auxiliary data structures beyond the list built).
"""
from __future__ import annotations

from typing import List


class Codec:
    def encode(self, strs: List[str]) -> str:
        # "<len>#<str>" per item; empty list -> "" (nothing framed).
        return "".join(f"{len(s)}#{s}" for s in strs)

    def decode(self, s: str) -> List[str]:
        result: List[str] = []
        i = 0                          # cursor into the framed stream
        while i < len(s):
            j = s.index("#", i)       # first '#' after cursor ends the digits
            length = int(s[i:j])       # payload length in decimal
            i = j + 1                  # step past the delimiter
            result.append(s[i:i + length])  # slice exactly `length` chars
            i += length               # advance past the payload to next frame
        return result
