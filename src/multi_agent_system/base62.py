"""Base62 encoding."""

from __future__ import annotations

import string


ALPHABET = string.ascii_letters + string.digits


def encode_base62(num: int) -> str:
    """Encode number to base62."""
    if num == 0:
        return ALPHABET[0]
    arr = []
    base = len(ALPHABET)
    while num:
        num, rem = divmod(num, base)
        arr.append(ALPHABET[rem])
    return "".join(reversed(arr))


def decode_base62(text: str) -> int:
    """Decode base62 to number."""
    base = len(ALPHABET)
    num = 0
    for c in text:
        num = num * base + ALPHABET.index(c)
    return num
