"""Mini-program adapters module."""

from .miniprogram_adapter import (
    AdapterRegistry,
    AlipayAdapter,
    MiniProgramAdapter,
    MiniProgramRequest,
    MiniProgramResponse,
    WeChatAdapter,
    get_adapter_registry,
)

__all__ = [
    "MiniProgramAdapter",
    "MiniProgramRequest",
    "MiniProgramResponse",
    "WeChatAdapter",
    "AlipayAdapter",
    "AdapterRegistry",
    "get_adapter_registry",
]
