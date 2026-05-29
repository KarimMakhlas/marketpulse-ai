"""FastAPI dependencies: LLM provider, current user, and the rate limiter.

The provider is resolved through the LLMProvider Protocol (architecture rule:
no direct SDK calls in the API layer). Tests override `get_provider` via
`app.dependency_overrides` to inject a fake.
"""

from __future__ import annotations

import os
from functools import lru_cache
from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from slowapi import Limiter
from slowapi.util import get_remote_address

from ..db import UserRecord, get_user
from ..llm.gemini import GeminiProvider
from ..llm.provider import LLMProvider
from .security import decode_access_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/token")

# Rate-limit storage: Redis if configured, else in-process memory (dev/test).
_storage_uri = os.environ.get("REDIS_URL", "memory://")
limiter = Limiter(key_func=get_remote_address, storage_uri=_storage_uri)


@lru_cache(maxsize=1)
def get_provider() -> LLMProvider:
    """Return a process-cached LLM provider (built once, reused across requests)."""
    return GeminiProvider()


_CREDENTIALS_EXC = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Could not validate credentials",
    headers={"WWW-Authenticate": "Bearer"},
)


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)]) -> UserRecord:
    """Decode the bearer token and load the matching user, or 401."""
    try:
        username = decode_access_token(token)
    except jwt.InvalidTokenError as exc:
        raise _CREDENTIALS_EXC from exc
    user = get_user(username)
    if user is None:
        raise _CREDENTIALS_EXC
    return user


CurrentUser = Annotated[UserRecord, Depends(get_current_user)]
Provider = Annotated[LLMProvider, Depends(get_provider)]
