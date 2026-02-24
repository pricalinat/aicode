"""Utilities for data serialization and transformation."""

from __future__ import annotations

import base64
import json
from dataclasses import asdict, is_dataclass
from typing import Any


def to_json(obj: Any, **kwargs: Any) -> str:
    """Convert object to JSON string."""
    if is_dataclass(obj):
        obj = asdict(obj)
    return json.dumps(obj, ensure_ascii=False, **kwargs)


def from_json(data: str, **kwargs: Any) -> Any:
    """Parse JSON string to object."""
    return json.loads(data, **kwargs)


def to_base64(data: str) -> str:
    """Encode string to base64."""
    return base64.b64encode(data.encode()).decode()


def from_base64(data: str) -> str:
    """Decode base64 string."""
    return base64.b64decode(data.encode()).decode()


def flatten_dict(d: dict, parent_key: str = "", sep: str = ".") -> dict:
    """Flatten nested dictionary."""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def unflatten_dict(d: dict, sep: str = ".") -> dict:
    """Unflatten dictionary."""
    result = {}
    for key, value in d.items():
        parts = key.split(sep)
        current = result
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
    return result


def merge_dicts(*dicts: dict) -> dict:
    """Deep merge multiple dictionaries."""
    result = {}
    for d in dicts:
        for key, value in d.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = merge_dicts(result[key], value)
            else:
                result[key] = value
    return result


def pick_keys(d: dict, keys: list[str]) -> dict:
    """Pick specific keys from dictionary."""
    return {k: v for k, v in d.items() if k in keys}


def omit_keys(d: dict, keys: list[str]) -> dict:
    """Omit specific keys from dictionary."""
    return {k: v for k, v in d.items() if k not in keys}
