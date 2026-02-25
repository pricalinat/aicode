"""Response formatters for different platforms."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ResponseFormat:
    """Response format metadata."""
    content_type: str
    encoding: str = "utf-8"


class JSONFormatter:
    """Format responses as JSON."""
    
    def format(self, data: Any) -> tuple[bytes, ResponseFormat]:
        import json
        return json.dumps(data).encode(), ResponseFormat("application/json")


class XMLFormatter:
    """Format responses as XML."""
    
    def format(self, data: Any) -> tuple[bytes, ResponseFormat]:
        import json
        # Simple dict to XML
        def to_xml(d: Any, root: str = "response") -> str:
            if isinstance(d, dict):
                items = "".join(f"<{k}>{to_xml(v)}</{k}>" for k, v in d.items())
                return f"<{root}>{items}</{root}>"
            elif isinstance(d, list):
                items = "".join(to_xml(i, "item") for i in d)
                return f"<{root}>{items}</{root}>"
            return str(d)
        
        xml = f'<?xml version="1.0" encoding="UTF-8"?>{to_xml(data)}'
        return xml.encode(), ResponseFormat("application/xml")


class PlainTextFormatter:
    """Format responses as plain text."""
    
    def format(self, data: Any) -> tuple[bytes, ResponseFormat]:
        text = str(data)
        return text.encode(), ResponseFormat("text/plain")


class FormatterRegistry:
    """Registry for response formatters."""
    
    def __init__(self) -> None:
        self._formatters = {
            "json": JSONFormatter(),
            "xml": XMLFormatter(),
            "text": PlainTextFormatter(),
        }
    
    def register(self, name: str, formatter: Any) -> None:
        self._formatters[name] = formatter
    
    def get(self, name: str) -> Any:
        return self._formatters.get(name, JSONFormatter())
