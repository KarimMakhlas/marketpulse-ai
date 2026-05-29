"""Tests for api/security.py — bcrypt hashing and JWT issue/verify."""

from __future__ import annotations

import jwt
import pytest

from marketpulse.api import security


def test_hash_and_verify_roundtrip() -> None:
    h = security.hash_password("correct horse battery staple")
    assert h != "correct horse battery staple"  # not stored in plaintext
    assert security.verify_password("correct horse battery staple", h) is True


def test_verify_rejects_wrong_password() -> None:
    h = security.hash_password("right-password")
    assert security.verify_password("wrong-password", h) is False


def test_verify_handles_malformed_hash() -> None:
    # Must not raise on a non-bcrypt string.
    assert security.verify_password("whatever", "not-a-bcrypt-hash") is False


def test_token_roundtrip(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-at-least-32-bytes-long!!")
    token = security.create_access_token("alice")
    assert security.decode_access_token(token) == "alice"


def test_decode_rejects_tampered_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-at-least-32-bytes-long!!")
    token = security.create_access_token("bob")
    with pytest.raises(jwt.InvalidTokenError):
        security.decode_access_token(token + "x")


def test_decode_rejects_wrong_secret(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "secret-a-padded-to-thirty-two-bytes-xx")
    token = security.create_access_token("carol")
    monkeypatch.setenv("JWT_SECRET_KEY", "secret-b-padded-to-thirty-two-bytes-xx")
    with pytest.raises(jwt.InvalidTokenError):
        security.decode_access_token(token)


def test_decode_rejects_expired_token(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-at-least-32-bytes-long!!")
    monkeypatch.setenv("JWT_EXPIRE_MINUTES", "-1")  # already expired
    token = security.create_access_token("dave")
    with pytest.raises(jwt.ExpiredSignatureError):
        security.decode_access_token(token)
