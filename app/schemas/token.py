"""
Token schemas for JWT authentication and refresh tokens.
"""
from typing import Optional, Dict, Any

from pydantic import BaseModel


class Token(BaseModel):
    """
    Token schema for access and refresh tokens.
    """
    access_token: str
    token_type: str
    refresh_token: Optional[str] = None
    user: Optional[Dict[str, Any]] = None


class TokenPayload(BaseModel):
    """
    Token payload schema for JWT payload.
    Contains the data inside the JWT token.
    """
    sub: Optional[str] = None
    id: Optional[int] = None
    role: Optional[str] = None
    exp: Optional[int] = None


class RefreshTokenRequest(BaseModel):
    """
    Refresh token request schema.
    """
    refresh_token: str 