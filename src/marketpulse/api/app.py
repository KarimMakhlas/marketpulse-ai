"""FastAPI application factory for MarketPulse AI (v0.4).

Routes:
  GET  /health                  liveness probe (no auth)
  POST /auth/register           create a user
  POST /auth/token              OAuth2 password grant -> JWT
  POST /query                   authenticated RAG answer (JSON)
  WS   /query/stream            authenticated token-streaming answer

All LLM access goes through the injected LLMProvider (architecture rule), so the
API never touches an SDK directly and tests can swap in a fake.
"""

from __future__ import annotations

import json
import logging
from collections.abc import AsyncIterator, Iterator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Annotated, Any

import jwt
from fastapi import Depends, FastAPI, HTTPException, Request, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from starlette.concurrency import run_in_threadpool

from .. import __version__
from ..db import (
    DBUnavailableError,
    UserAlreadyExistsError,
    create_user,
    ensure_schema,
    get_user,
)
from ..llm.provider import LLMProvider
from ..synthesis.answer import AnswerStream, answer
from .deps import CurrentUser, Provider, get_provider, limiter
from .schemas import CitationOut, QueryRequest, QueryResponse, Token, UserCreate, UserOut
from .security import create_access_token, decode_access_token, hash_password, verify_password

logger = logging.getLogger(__name__)

# Vendored design-system web UI (src/marketpulse/web/). Mounted at /app when present.
WEB_DIR = Path(__file__).resolve().parent.parent / "web"


def _is_quota_error(msg: str) -> bool:
    return "429" in msg or "RESOURCE_EXHAUSTED" in msg


def _is_overloaded_error(msg: str) -> bool:
    return "503" in msg or "UNAVAILABLE" in msg


def _map_llm_error(exc: Exception) -> HTTPException:
    """Translate a provider error into an HTTP status the client can act on."""
    msg = str(exc)
    if _is_quota_error(msg):
        return HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="LLM free-tier quota exhausted (429). Try again after the daily reset.",
        )
    if _is_overloaded_error(msg):
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM temporarily overloaded (503). Retry in a few seconds.",
        )
    return HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Generation failed: {msg}",
    )


@asynccontextmanager
async def _lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Establish the DB connection / schema once at startup.
    ensure_schema()
    yield


def create_app() -> FastAPI:
    app = FastAPI(
        title="MarketPulse AI",
        version=__version__,
        description="Financial-news Self-RAG API.",
        lifespan=_lifespan,
    )
    app.state.limiter = limiter
    # slowapi types its handler as (Request, RateLimitExceeded); Starlette wants
    # (Request, Exception). The runtime contract holds — narrow the type for mypy.
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore[arg-type]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "version": __version__}

    @app.post("/auth/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
    @limiter.limit("10/minute")
    def register(request: Request, body: UserCreate) -> UserOut:
        try:
            user = create_user(body.username, hash_password(body.password))
        except UserAlreadyExistsError as exc:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT, detail="Username already taken"
            ) from exc
        except DBUnavailableError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="User store unavailable — DATABASE_URL not configured.",
            ) from exc
        return UserOut(id=user.id, username=user.username)

    @app.post("/auth/token", response_model=Token)
    @limiter.limit("20/minute")
    def login(
        request: Request,
        form: Annotated[OAuth2PasswordRequestForm, Depends()],
    ) -> Token:
        user = get_user(form.username)
        if user is None or not verify_password(form.password, user.password_hash):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return Token(access_token=create_access_token(user.username))

    @app.post("/query", response_model=QueryResponse)
    @limiter.limit("30/minute")
    def query(
        request: Request,
        body: QueryRequest,
        user: CurrentUser,
        provider: Provider,
    ) -> QueryResponse:
        result = answer(body.query, provider=provider, k=body.k)
        citations = [CitationOut.from_citation(c) for c in result.citations]
        try:
            text = "".join(result.tokens)
        except Exception as exc:  # noqa: BLE001 — map provider failures to HTTP
            raise _map_llm_error(exc) from exc
        return QueryResponse(
            answer=text,
            refused=result.refused,
            doc_grade=result.doc_grade,
            citations=citations,
        )

    @app.websocket("/query/stream")
    async def query_stream(websocket: WebSocket) -> None:
        await _serve_stream(websocket)

    # Serve the vendored design-system web UI (same origin -> WebSocket just works).
    # html=True makes /app/ resolve to index.html. Mounted last so it never shadows
    # the API routes above. Absent dir (e.g. trimmed deploy) simply skips the mount.
    if WEB_DIR.is_dir():

        @app.get("/", include_in_schema=False)
        def _root() -> RedirectResponse:
            return RedirectResponse(url="/app/")

        app.mount("/app", StaticFiles(directory=WEB_DIR, html=True), name="web")

    return app


async def _authenticate_ws(websocket: WebSocket) -> str | None:
    """Validate the `?token=` query param. Returns username or None (already closed)."""
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="missing token")
        return None
    try:
        username = decode_access_token(token)
    except jwt.InvalidTokenError:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="invalid token")
        return None
    if get_user(username) is None:
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="unknown user")
        return None
    return username


async def _drain(gen: Iterator[str], websocket: WebSocket) -> None:
    """Stream a sync token generator over the socket without blocking the loop.

    Each `next()` may trigger a blocking network read from the LLM, so it runs in
    a threadpool. Iteration stops on StopIteration; provider errors are surfaced
    as a typed `error` frame.
    """
    sentinel = object()
    while True:
        token = await run_in_threadpool(next, gen, sentinel)
        if token is sentinel:
            return
        await websocket.send_text(json.dumps({"type": "token", "data": token}))


async def _serve_stream(websocket: WebSocket) -> None:
    await websocket.accept()
    username = await _authenticate_ws(websocket)
    if username is None:
        return
    try:
        raw = await websocket.receive_text()
        payload: dict[str, Any] = json.loads(raw)
        req = QueryRequest(**payload)
    except (WebSocketDisconnect, json.JSONDecodeError, ValueError, TypeError):
        await websocket.close(code=status.WS_1003_UNSUPPORTED_DATA, reason="bad request")
        return

    provider: LLMProvider = get_provider()
    result: AnswerStream = await run_in_threadpool(answer, req.query, provider=provider, k=req.k)
    citations = [CitationOut.from_citation(c).model_dump(mode="json") for c in result.citations]
    await websocket.send_text(
        json.dumps(
            {
                "type": "meta",
                "refused": result.refused,
                "doc_grade": result.doc_grade,
                "citations": citations,
            }
        )
    )
    try:
        await _drain(result.tokens, websocket)
    except WebSocketDisconnect:
        return
    except Exception as exc:  # noqa: BLE001 — report provider failure then close
        mapped = _map_llm_error(exc)
        await websocket.send_text(
            json.dumps({"type": "error", "status": mapped.status_code, "detail": mapped.detail})
        )
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return
    await websocket.send_text(json.dumps({"type": "done"}))
    await websocket.close()
