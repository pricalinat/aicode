from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4


@dataclass
class Message:
    task_type: str
    content: dict[str, Any]
    trace_id: str = field(default_factory=lambda: str(uuid4()))
