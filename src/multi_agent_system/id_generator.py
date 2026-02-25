"""ID generators."""

from __future__ import annotations

import uuid
import time
from typing import Any


def generate_uuid() -> str:
    """Generate UUID."""
    return str(uuid.uuid4())


def generate_short_id(length: int = 8) -> str:
    """Generate short ID."""
    return uuid.uuid4().hex[:length]


def generate_timestamp_id() -> str:
    """Generate timestamp-based ID."""
    return f"{int(time.time() * 1000)}"


def generateNanoId(size: int = 21) -> str:
    """Generate Nano ID."""
    import string
    alphabet = string.ascii_letters + string.digits
    return "".join(alphabet[int.from_bytes(uuid.uuid4().bytes[i:i+1]) % len(alphabet)] for i in range(size))


class IDGenerator:
    """Configurable ID generator."""
    
    def __init__(self, prefix: str = "") -> None:
        self._prefix = prefix
    
    def generate(self) -> str:
        if self._prefix:
            return f"{self._prefix}_{generate_uuid()}"
        return generate_uuid()
