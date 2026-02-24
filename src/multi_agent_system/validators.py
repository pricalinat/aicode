"""Validators for data validation."""

from __future__ import annotations

import re
from typing import Any, Callable


class Validator:
    """Base validator."""
    
    def __init__(self, message: str = "Validation failed") -> None:
        self.message = message
    
    def validate(self, value: Any) -> bool:
        raise NotImplementedError


class RequiredValidator(Validator):
    """Validate required field."""
    
    def validate(self, value: Any) -> bool:
        return value is not None and value != ""


class EmailValidator(Validator):
    """Validate email format."""
    
    def validate(self, value: Any) -> bool:
        if not value:
            return False
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, str(value)))


class LengthValidator(Validator):
    """Validate string length."""
    
    def __init__(self, min_length: int = 0, max_length: int = 0, message: str = "Invalid length") -> None:
        super().__init__(message)
        self.min_length = min_length
        self.max_length = max_length
    
    def validate(self, value: Any) -> bool:
        if not value:
            return False
        length = len(str(value))
        if self.min_length and length < self.min_length:
            return False
        if self.max_length and length > self.max_length:
            return False
        return True


class RangeValidator(Validator):
    """Validate numeric range."""
    
    def __init__(self, min_value: float = 0, max_value: float = 0, message: str = "Out of range") -> None:
        super().__init__(message)
        self.min_value = min_value
        self.max_value = max_value
    
    def validate(self, value: Any) -> bool:
        try:
            num = float(value)
            if self.min_value and num < self.min_value:
                return False
            if self.max_value and num > self.max_value:
                return False
            return True
        except (ValueError, TypeError):
            return False


def validate(data: dict, rules: dict[str, list[Validator]]) -> tuple[bool, dict]:
    """Validate data with rules."""
    errors = {}
    
    for field, validators in rules.items():
        value = data.get(field)
        for validator in validators:
            if not validator.validate(value):
                errors[field] = validator.message
                break
    
    return len(errors) == 0, errors
