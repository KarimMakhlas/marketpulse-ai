/* MarketPulse AI — live backend client.
 *
 * Bridges the UI kit to the real FastAPI backend:
 *   POST /auth/register      create a user
 *   POST /auth/token         OAuth2 password grant -> JWT (form-encoded)
 *   WS   /query/stream       ?token=  ->  {meta} -> {token}* -> {done|error}
 *
 * The UI is served same-origin by FastAPI (mounted at /app), so the API base is
 * just the current origin and the WebSocket uses the matching ws/wss scheme.
 */
window.MP = (function () {
  const TOKEN_KEY = "mp_token";

  // Served from /app/... -> strip the trailing path to reach the API root.
  const apiBase = window.location.origin;

  function wsBase() {
    const proto = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${proto}//${window.location.host}`;
  }

  function getToken() {
    try {
      return window.localStorage.getItem(TOKEN_KEY);
    } catch (_e) {
      return null;
    }
  }

  function setToken(tok) {
    try {
      if (tok) window.localStorage.setItem(TOKEN_KEY, tok);
      else window.localStorage.removeItem(TOKEN_KEY);
    } catch (_e) {
      /* localStorage unavailable (private mode) — token stays in-memory only */
    }
  }

  function clearToken() {
    setToken(null);
  }

  /* --- auth ---------------------------------------------------------------- */

  async function register(username, password) {
    const r = await fetch(`${apiBase}/auth/register`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password }),
    });
    if (r.status === 201) return { ok: true };
    if (r.status === 409) return { ok: false, error: "Username already taken." };
    if (r.status === 503)
      return { ok: false, error: "User store unavailable. Start Postgres (make stack-up)." };
    const detail = await safeDetail(r);
    return { ok: false, error: detail || `Registration failed (${r.status}).` };
  }

  async function login(username, password) {
    // OAuth2 password grant expects application/x-www-form-urlencoded.
    const body = new URLSearchParams({ username, password });
    const r = await fetch(`${apiBase}/auth/token`, {
      method: "POST",
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
      body,
    });
    if (r.status === 200) {
      const data = await r.json();
      setToken(data.access_token);
      return { ok: true, token: data.access_token };
    }
    if (r.status === 401) return { ok: false, error: "Incorrect username or password." };
    if (r.status === 503)
      return { ok: false, error: "User store unavailable. Start Postgres (make stack-up)." };
    const detail = await safeDetail(r);
    return { ok: false, error: detail || `Login failed (${r.status}).` };
  }

  async function safeDetail(r) {
    try {
      const j = await r.json();
      return typeof j.detail === "string" ? j.detail : null;
    } catch (_e) {
      return null;
    }
  }

  /* --- read endpoints (dashboard / history / sources / config) ------------- */

  function authHeaders() {
    const tok = getToken();
    return tok ? { Authorization: `Bearer ${tok}` } : {};
  }

  /** GET /health -> { version, model, default_k, db, redis } | null on failure. */
  async function health() {
    try {
      const r = await fetch(`${apiBase}/health`);
      return r.ok ? await r.json() : null;
    } catch (_e) {
      return null;
    }
  }

  /** GET /stats -> { articles_indexed, queries_today, sources_active, db_available } | null. */
  async function stats() {
    try {
      const r = await fetch(`${apiBase}/stats`);
      return r.ok ? await r.json() : null;
    } catch (_e) {
      return null;
    }
  }

  /** GET /sources -> [{ id, name, kind, credibility }] | null on failure. */
  async function sources() {
    try {
      const r = await fetch(`${apiBase}/sources`);
      return r.ok ? await r.json() : null;
    } catch (_e) {
      return null;
    }
  }

  /**
   * GET /queries (auth) -> { ok, rows } | { ok:false, error }.
   * Distinguishes "not signed in" (401) from "no DB / empty" so the UI can
   * show an honest state instead of a fake table.
   */
  async function queries(limit = 50) {
    if (!getToken()) return { ok: false, error: "auth", rows: [] };
    try {
      const r = await fetch(`${apiBase}/queries?limit=${encodeURIComponent(limit)}`, {
        headers: authHeaders(),
      });
      if (r.status === 401) {
        clearToken();
        return { ok: false, error: "auth", rows: [] };
      }
      if (!r.ok) return { ok: false, error: `http_${r.status}`, rows: [] };
      return { ok: true, rows: await r.json() };
    } catch (_e) {
      return { ok: false, error: "network", rows: [] };
    }
  }

  /* --- query stream -------------------------------------------------------- */

  /**
   * Open the live WebSocket and drive the callbacks as frames arrive.
   * Returns a handle with .stop() to abort early.
   *
   * callbacks: { onOpen, onMeta(meta), onToken(text), onDone(), onError(msg) }
   */
  function streamQuery({ query, k = 5, callbacks = {} }) {
    const token = getToken();
    if (!token) {
      callbacks.onError && callbacks.onError("Not authenticated. Sign in to run a query.");
      return { stop() {} };
    }

    const url = `${wsBase()}/query/stream?token=${encodeURIComponent(token)}`;
    const ws = new WebSocket(url);
    let closedByClient = false;

    ws.onopen = () => {
      callbacks.onOpen && callbacks.onOpen();
      ws.send(JSON.stringify({ query, k }));
    };

    ws.onmessage = (ev) => {
      let msg;
      try {
        msg = JSON.parse(ev.data);
      } catch (_e) {
        return;
      }
      if (msg.type === "meta") callbacks.onMeta && callbacks.onMeta(msg);
      else if (msg.type === "token") callbacks.onToken && callbacks.onToken(msg.data);
      else if (msg.type === "done") callbacks.onDone && callbacks.onDone();
      else if (msg.type === "error")
        callbacks.onError && callbacks.onError(msg.detail || "Generation failed.");
    };

    ws.onerror = () => {
      if (!closedByClient)
        callbacks.onError && callbacks.onError("Connection failed. Is the API running?");
    };

    ws.onclose = (ev) => {
      // 1008 = policy violation (bad/missing token); surface as an auth error.
      if (ev.code === 1008) {
        clearToken();
        callbacks.onError && callbacks.onError("Session expired. Sign in again.");
      }
    };

    return {
      stop() {
        closedByClient = true;
        try {
          ws.close();
        } catch (_e) {
          /* already closed */
        }
      },
    };
  }

  return {
    apiBase,
    getToken,
    setToken,
    clearToken,
    register,
    login,
    streamQuery,
    health,
    stats,
    sources,
    queries,
  };
})();
