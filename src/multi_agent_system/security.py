"""Security utilities for authentication and authorization."""

from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class Token:
    """An authentication token."""
    user_id: str
    token: str
    created_at: float
    expires_at: float
    permissions: list[str]


class AuthManager:
    """Manage authentication and authorization."""
    
    def __init__(self, secret_key: str | None = None) -> None:
        self._secret_key = secret_key or secrets.token_hex(32)
        self._tokens: dict[str, Token] = {}
    
    def create_token(
        self,
        user_id: str,
        ttl: int = 3600,
        permissions: list[str] | None = None,
    ) -> str:
        """Create an authentication token."""
        token = secrets.token_urlsafe(32)
        now = time.time()
        
        self._tokens[token] = Token(
            user_id=user_id,
            token=token,
            created_at=now,
            expires_at=now + ttl,
            permissions=permissions or [],
        )
        
        return token
    
    def verify_token(self, token: str) -> Token | None:
        """Verify a token."""
        token_obj = self._tokens.get(token)
        
        if not token_obj:
            return None
        
        if time.time() > token_obj.expires_at:
            del self._tokens[token]
            return None
        
        return token_obj
    
    def revoke_token(self, token: str) -> bool:
        """Revoke a token."""
        if token in self._tokens:
            del self._tokens[token]
            return True
        return False
    
    def has_permission(self, token: str, permission: str) -> bool:
        """Check if token has a permission."""
        token_obj = self.verify_token(token)
        
        if not token_obj:
            return False
        
        return permission in token_obj.permissions
    
    def generate_signature(self, data: str) -> str:
        """Generate HMAC signature."""
        return hmac.new(
            self._secret_key.encode(),
            data.encode(),
            hashlib.sha256,
        ).hexdigest()
    
    def verify_signature(self, data: str, signature: str) -> bool:
        """Verify HMAC signature."""
        expected = self.generate_signature(data)
        return hmac.compare_digest(expected, signature)


# Global auth manager
_auth_manager: AuthManager | None = None


def get_auth_manager(secret_key: str | None = None) -> AuthManager:
    """Get the global auth manager."""
    global _auth_manager
    if _auth_manager is None:
        _auth_manager = AuthManager(secret_key)
    return _auth_manager
