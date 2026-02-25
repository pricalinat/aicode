"""Request/Response parsers."""

from __future__ import annotations

from typing import Any, Dict


class JSONParser:
    """Parse JSON requests."""
    
    def parse(self, data: bytes) -> Dict:
        import json
        return json.loads(data)


class FormParser:
    """Parse form data."""
    
    def parse(self, data: bytes) -> Dict:
        from urllib.parse import parse_qs
        result = parse_qs(data.decode())
        # Convert lists to single values
        return {k: v[0] if len(v) == 1 else v for k, v in result.items()}


class MultipartParser:
    """Parse multipart data."""
    
    def parse(self, data: bytes, boundary: bytes) -> Dict:
        # Simplified - just return raw
        return {"raw": data}


class ParserRegistry:
    """Registry for parsers."""
    
    def __init__(self) -> None:
        self._parsers = {
            "application/json": JSONParser(),
            "application/x-www-form-urlencoded": FormParser(),
        }
    
    def register(self, content_type: str, parser: Any) -> None:
        self._parsers[content_type] = parser
    
    def parse(self, content_type: str, data: bytes) -> Dict:
        parser = self._parsers.get(content_type, JSONParser())
        return parser.parse(data)
