"""Tests for the FastAPI layer — no network, no real LLM/Chroma/DB.

The user store is an in-memory fake, `search()` is patched to return fixed
chunks, and the LLM provider is a fake injected via dependency override (HTTP)
and monkeypatch (WebSocket calls get_provider() directly).
"""

from __future__ import annotations

from collections.abc import Iterator

import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from conftest import FakeProvider, make_chunk
from marketpulse.api import app as app_module
from marketpulse.api import deps
from marketpulse.api.app import create_app
from marketpulse.db import UserAlreadyExistsError, UserRecord


class FakeUserStore:
    def __init__(self) -> None:
        self._users: dict[str, UserRecord] = {}

    def create(self, username: str, password_hash: str) -> UserRecord:
        if username in self._users:
            raise UserAlreadyExistsError(username)
        rec = UserRecord(id=len(self._users) + 1, username=username, password_hash=password_hash)
        self._users[username] = rec
        return rec

    def get(self, username: str) -> UserRecord | None:
        return self._users.get(username)


@pytest.fixture
def provider() -> FakeProvider:
    return FakeProvider(tokens=["Hello ", "world [S1]."])


@pytest.fixture
def store() -> FakeUserStore:
    return FakeUserStore()


@pytest.fixture
def client(
    monkeypatch: pytest.MonkeyPatch,
    provider: FakeProvider,
    store: FakeUserStore,
) -> Iterator[TestClient]:
    monkeypatch.setenv("JWT_SECRET_KEY", "test-secret-key-at-least-32-bytes-long!!")
    monkeypatch.delenv("DATABASE_URL", raising=False)  # ensure_schema stays a no-op
    # Disable rate limiting for functional tests; the module-level limiter shares
    # state across the process and would otherwise trip on repeated registrations.
    # Rate limiting itself is covered by test_rate_limit_enforced.
    monkeypatch.setattr(deps.limiter, "enabled", False)

    # In-memory user store across both modules that reference the db helpers.
    monkeypatch.setattr(app_module, "create_user", store.create)
    monkeypatch.setattr(app_module, "get_user", store.get)
    monkeypatch.setattr(deps, "get_user", store.get)
    # Avoid real Chroma; answer() -> graph -> search() is patched at its source.
    monkeypatch.setattr(
        "marketpulse.graph.nodes.search", lambda q, k: [make_chunk(1), make_chunk(2)]
    )
    # /stats calls collection_count() which would otherwise open a real Chroma
    # client on disk — stub it so the stats endpoint stays isolated.
    monkeypatch.setattr(app_module, "collection_count", lambda: 1234)
    # WebSocket path calls get_provider() directly.
    monkeypatch.setattr(app_module, "get_provider", lambda: provider)

    app = create_app()
    app.dependency_overrides[deps.get_provider] = lambda: provider
    with TestClient(app) as c:
        yield c


def _register_and_token(client: TestClient, username: str = "alice") -> str:
    r = client.post("/auth/register", json={"username": username, "password": "password123"})
    assert r.status_code == 201, r.text
    r = client.post("/auth/token", data={"username": username, "password": "password123"})
    assert r.status_code == 200, r.text
    return str(r.json()["access_token"])


# --- health / stats / sources ----------------------------------------------


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    # Extended fields the Settings/Dashboard screens read.
    assert "version" in body
    assert body["model"]  # configured LLM model name
    assert body["default_k"] >= 1
    assert body["db"] is False  # DATABASE_URL deleted in the fixture
    assert "redis" in body


def test_stats_public(client: TestClient) -> None:
    r = client.get("/stats")
    assert r.status_code == 200
    body = r.json()
    assert body["articles_indexed"] == 1234  # stubbed collection_count
    assert body["queries_today"] is None  # no DB in tests
    assert body["sources_active"] >= 7  # real ingestion source set
    assert body["db_available"] is False


def test_sources_public(client: TestClient) -> None:
    r = client.get("/sources")
    assert r.status_code == 200
    rows = r.json()
    assert len(rows) >= 7
    ids = {row["id"] for row in rows}
    assert "ft" in ids and "sec_8k" in ids
    # Sorted by credibility, highest first.
    creds = [row["credibility"] for row in rows]
    assert creds == sorted(creds, reverse=True)


def test_queries_requires_auth(client: TestClient) -> None:
    r = client.get("/queries")
    assert r.status_code == 401


def test_queries_authed_returns_list(client: TestClient) -> None:
    token = _register_and_token(client, username="histuser")
    r = client.get("/queries", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json() == []  # query_log is a no-op without a DB


# --- auth -------------------------------------------------------------------


def test_register_returns_user(client: TestClient) -> None:
    r = client.post("/auth/register", json={"username": "newuser", "password": "password123"})
    assert r.status_code == 201
    body = r.json()
    assert body["username"] == "newuser"
    assert "id" in body
    assert "password" not in body  # never leak credentials


def test_register_duplicate_conflicts(client: TestClient) -> None:
    client.post("/auth/register", json={"username": "dup", "password": "password123"})
    r = client.post("/auth/register", json={"username": "dup", "password": "password123"})
    assert r.status_code == 409


def test_register_rejects_short_password(client: TestClient) -> None:
    r = client.post("/auth/register", json={"username": "shorty", "password": "x"})
    assert r.status_code == 422  # pydantic validation


def test_login_wrong_password_401(client: TestClient) -> None:
    client.post("/auth/register", json={"username": "eve", "password": "password123"})
    r = client.post("/auth/token", data={"username": "eve", "password": "WRONG"})
    assert r.status_code == 401


def test_login_unknown_user_401(client: TestClient) -> None:
    r = client.post("/auth/token", data={"username": "ghost", "password": "password123"})
    assert r.status_code == 401


# --- /query -----------------------------------------------------------------


def test_query_requires_auth(client: TestClient) -> None:
    r = client.post("/query", json={"query": "What about the Fed?"})
    assert r.status_code == 401


def test_query_rejects_bad_token(client: TestClient) -> None:
    r = client.post(
        "/query",
        json={"query": "hi"},
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert r.status_code == 401


def test_query_happy_path(client: TestClient) -> None:
    token = _register_and_token(client)
    r = client.post(
        "/query",
        json={"query": "What about the Fed?", "k": 2},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["answer"] == "Hello world [S1]."
    assert body["refused"] is False
    assert body["doc_grade"] == "sufficient"
    assert len(body["citations"]) == 2
    assert body["citations"][0]["marker"] == "[S1]"


def test_query_refusal_path(client: TestClient) -> None:
    # Grader returns INSUFFICIENT -> answer() takes the refusal branch.
    refusing = FakeProvider(tokens=["unused"], grade="INSUFFICIENT")
    client.app.dependency_overrides[deps.get_provider] = lambda: refusing
    token = _register_and_token(client)
    r = client.post(
        "/query",
        json={"query": "airspeed of an unladen swallow?", "k": 2},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["refused"] is True
    assert body["doc_grade"] == "insufficient"


# --- /query/stream (WebSocket) ---------------------------------------------


def test_ws_requires_token(client: TestClient) -> None:
    # No token -> server accepts then closes with a policy violation.
    with (
        pytest.raises(Exception),  # noqa: B017 - starlette raises WebSocketDisconnect
        client.websocket_connect("/query/stream") as ws,
    ):
        ws.receive_text()


def test_ws_stream_happy_path(client: TestClient) -> None:
    token = _register_and_token(client, username="wsuser")
    with client.websocket_connect(f"/query/stream?token={token}") as ws:
        ws.send_json({"query": "What about the Fed?", "k": 2})
        meta = ws.receive_json()
        assert meta["type"] == "meta"
        assert meta["refused"] is False
        assert len(meta["citations"]) == 2

        tokens = []
        while True:
            msg = ws.receive_json()
            if msg["type"] == "done":
                break
            assert msg["type"] == "token"
            tokens.append(msg["data"])
        assert "".join(tokens) == "Hello world [S1]."


# --- web UI mount -----------------------------------------------------------


def test_root_redirects_to_app(client: TestClient) -> None:
    r = client.get("/", follow_redirects=False)
    assert r.status_code in (307, 308)
    assert r.headers["location"] == "/app/"


def test_app_serves_index(client: TestClient) -> None:
    r = client.get("/app/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "MarketPulse" in r.text


def test_app_serves_api_client(client: TestClient) -> None:
    # The live backend client must be reachable for the UI to wire up the WS.
    r = client.get("/app/api.js")
    assert r.status_code == 200
    assert "streamQuery" in r.text


def test_query_citation_includes_excerpt(client: TestClient) -> None:
    token = _register_and_token(client, username="exuser")
    r = client.post(
        "/query",
        json={"query": "What about the Fed?", "k": 2},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200, r.text
    assert "excerpt" in r.json()["citations"][0]


def test_rate_limit_enforced() -> None:
    """Rate limiting returns 429 once the window is exceeded.

    Uses a dedicated app with its own fresh Limiter (same wiring as create_app:
    app.state.limiter + the slowapi exception handler + @limiter.limit). This is
    isolated from the module-level limiter so it can't be polluted by other tests
    sharing the single in-process "testclient" window.
    """
    lim = Limiter(key_func=get_remote_address, storage_uri="memory://")
    iso_app = FastAPI()
    iso_app.state.limiter = lim
    iso_app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]

    @iso_app.get("/ping")
    @lim.limit("3/minute")
    def ping(request: Request) -> dict[str, bool]:  # noqa: ARG001
        return {"ok": True}

    with TestClient(iso_app) as c:
        statuses = [c.get("/ping").status_code for _ in range(5)]

    assert statuses[:3] == [200, 200, 200]  # first 3 within the window
    assert 429 in statuses[3:]  # subsequent calls throttled
