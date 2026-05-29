"""Password hashing (bcrypt) and JWT issue/verify (PyJWT).

Configuration via env:
  JWT_SECRET_KEY      signing secret (REQUIRED in production)
  JWT_EXPIRE_MINUTES  access-token lifetime (default 60)

If JWT_SECRET_KEY is unset a random per-process key is generated and a warning
logged: tokens then survive only for the life of the process, which is fine for
local dev but means every restart invalidates outstanding tokens. Set the var in
any real deployment.
"""

from __future__ import annotations

import logging
import os
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import bcrypt
import jwt

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"
_DEFAULT_EXPIRE_MINUTES = 60

# Stable random key for one process when JWT_SECRET_KEY is unset (dev only).
_ephemeral_key: str | None = None


def _secret_key() -> str:
    key = os.environ.get("JWT_SECRET_KEY")
    if key:
        return key
    global _ephemeral_key
    if _ephemeral_key is None:
        _ephemeral_key = secrets.token_urlsafe(48)
        logger.warning(
            "JWT_SECRET_KEY not set — using an ephemeral per-process key. "
            "Tokens will not survive a restart. Set JWT_SECRET_KEY in production."
        )
    return _ephemeral_key


def _expire_minutes() -> int:
    raw = os.environ.get("JWT_EXPIRE_MINUTES")
    if not raw:
        return _DEFAULT_EXPIRE_MINUTES
    try:
        return int(raw)
    except ValueError:
        logger.warning("invalid JWT_EXPIRE_MINUTES=%r — falling back to default", raw)
        return _DEFAULT_EXPIRE_MINUTES


def hash_password(password: str) -> str:
    """Return a bcrypt hash (with embedded salt) as a UTF-8 string."""
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Constant-time check of a plaintext password against a stored bcrypt hash."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        # Malformed/legacy hash — treat as a failed match rather than crashing.
        return False


def create_access_token(subject: str) -> str:
    """Issue a signed JWT whose `sub` claim is the username."""
    now = datetime.now(tz=UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "iat": now,
        "exp": now + timedelta(minutes=_expire_minutes()),
    }
    return jwt.encode(payload, _secret_key(), algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    """Verify a JWT and return its subject (username).

    Raises jwt.InvalidTokenError (incl. ExpiredSignatureError) on any problem,
    which the API layer maps to HTTP 401.
    """
    payload = jwt.decode(token, _secret_key(), algorithms=[ALGORITHM])
    sub = payload.get("sub")
    if not isinstance(sub, str) or not sub:
        raise jwt.InvalidTokenError("token missing subject")
    return sub
