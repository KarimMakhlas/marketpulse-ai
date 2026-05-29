/* Query Console — LIVE streaming Q&A wired to the real FastAPI backend.
 *
 * Protocol (see api.js / api/app.py):
 *   WS /query/stream?token=  ->  {meta: refused, doc_grade, citations[]}
 *                            ->  {token: data}*  ->  {done} | {error}
 *
 * Everything shown here is real: citations, doc_grade, refusal, and a
 * client-measured round-trip latency. Metrics the API does not expose
 * (per-agent cost, trace id, token count) render as "—" rather than faked.
 */

const { useState: useStateQ, useEffect: useEffectQ, useRef: useRefQ } = React;

const DEFAULT_K = 5;

/* ISO timestamp -> YYYY-MM-DD for source cards. */
const citationDate = (iso) => {
  if (!iso) return "—";
  const d = new Date(iso);
  return isNaN(d) ? String(iso).slice(0, 10) : d.toISOString().slice(0, 10);
};

/* Map a backend citation (marker, source, title, url, similarity, recency,
   score, excerpt) onto SourceCard's shape. */
const toSource = (c) => ({
  name: c.source,
  date: citationDate(c.published_at),
  similarity: c.similarity,
  recency: c.recency,
  score: c.score,
  excerpt: c.excerpt || c.title,
  url: c.url,
  marker: c.marker,
});

const QueryConsole = ({ initialQuery, onClear }) => {
  const [query, setQuery] = useStateQ(initialQuery || "");
  const [phase, setPhase] = useStateQ("idle"); // idle | streaming | done | refused | error
  const [agents, setAgents] = useStateQ(() => initialAgents());
  const [streamed, setStreamed] = useStateQ("");
  const [citations, setCitations] = useStateQ([]);
  const [docGrade, setDocGrade] = useStateQ("");
  const [refused, setRefused] = useStateQ(false);
  const [errorMsg, setErrorMsg] = useStateQ("");
  const [elapsed, setElapsed] = useStateQ(null); // seconds, client round-trip
  const [showLogin, setShowLogin] = useStateQ(false);
  const streamRef = useRefQ(null);
  const startRef = useRefQ(0);
  const accRef = useRefQ("");

  function initialAgents() {
    return [
      { agent: "router", state: "pending", desc: "Awaiting query", duration: "—", cost: "—" },
      { agent: "retrieval", state: "pending", desc: "—", duration: "—", cost: "—" },
      { agent: "critique", state: "pending", desc: "—", duration: "—", cost: "—" },
      { agent: "synthesis", state: "pending", desc: "—", duration: "—", cost: "—" },
      { agent: "grader", state: "pending", desc: "—", duration: "—", cost: "—" },
    ];
  }

  const upd = (arr, idx, patch) => arr.map((a, i) => (i === idx ? { ...a, ...patch } : a));

  const reset = () => {
    if (streamRef.current) streamRef.current.stop();
    streamRef.current = null;
    accRef.current = "";
    setStreamed("");
    setCitations([]);
    setDocGrade("");
    setRefused(false);
    setErrorMsg("");
    setElapsed(null);
    setPhase("idle");
    setAgents(initialAgents());
  };

  const run = () => {
    const q = query.trim();
    if (!q) return;
    if (!window.MP.getToken()) {
      setShowLogin(true);
      return;
    }
    reset();
    setPhase("streaming");
    startRef.current = performance.now();
    setAgents((a) => upd(a, 0, { state: "active", desc: "Routing query…" }));

    streamRef.current = window.MP.streamQuery({
      query: q,
      k: DEFAULT_K,
      callbacks: {
        onOpen: () => {
          setAgents((a) => {
            let next = upd(a, 0, { state: "done", desc: "Routed to retrieval" });
            next = upd(next, 1, { state: "active", desc: `Querying ChromaDB · k = ${DEFAULT_K}…` });
            return next;
          });
        },
        onMeta: (meta) => {
          const cites = meta.citations || [];
          setCitations(cites);
          setDocGrade(meta.doc_grade || "");
          setRefused(!!meta.refused);
          setAgents((a) => {
            let next = upd(a, 1, {
              state: "done",
              desc: <>Retrieved <strong>{cites.length} kept</strong></>,
            });
            const gradeTone = meta.doc_grade === "sufficient" ? "fg-signal" : "fg-loss";
            next = upd(next, 2, {
              state: "done",
              desc: <>Grade <strong className={gradeTone}>{meta.doc_grade || "—"}</strong></>,
            });
            if (meta.refused) {
              next = upd(next, 3, { state: "error", desc: "Skipped — insufficient evidence" });
              next = upd(next, 4, {
                state: "done",
                desc: <span className="fg-loss">Refused</span>,
              });
            } else {
              next = upd(next, 3, { state: "active", desc: "Generating answer…" });
            }
            return next;
          });
        },
        onToken: (t) => {
          accRef.current += t;
          setStreamed(accRef.current);
        },
        onDone: () => {
          const secs = (performance.now() - startRef.current) / 1000;
          setElapsed(secs);
          setRefused((wasRefused) => {
            setPhase(wasRefused ? "refused" : "done");
            if (!wasRefused) {
              const chars = accRef.current.length;
              setAgents((a) => {
                let next = upd(a, 3, {
                  state: "done",
                  desc: <>Generated <strong>{chars} chars</strong></>,
                });
                next = upd(next, 4, {
                  state: "done",
                  desc: <>Graded <strong className="fg-signal">sufficient</strong></>,
                });
                return next;
              });
            }
            return wasRefused;
          });
          streamRef.current = null;
        },
        onError: (msg) => {
          setErrorMsg(msg);
          setPhase("error");
          setAgents((a) => a.map((ag) => (ag.state === "active" ? { ...ag, state: "error" } : ag)));
          if (/sign in|authenticated|expired/i.test(msg)) setShowLogin(true);
          streamRef.current = null;
        },
      },
    });
  };

  // Auto-run when arriving with a query from Dashboard / History.
  useEffectQ(() => {
    if (initialQuery) {
      setQuery(initialQuery);
      const t = setTimeout(run, 150);
      return () => clearTimeout(t);
    }
    return () => {
      if (streamRef.current) streamRef.current.stop();
    };
    // eslint-disable-next-line
  }, []);

  const sources = citations.map(toSource);
  const elapsedLabel = elapsed != null ? `${elapsed.toFixed(1)} s` : phase === "streaming" ? "in flight…" : "—";

  return (
    <>
      <PageHead
        eyebrow="Query Console"
        title="Live market intelligence"
        subtitle="Self-RAG over the indexed corpus · streamed live via /query/stream · graded before synthesis"
        actions={
          <>
            {window.MP.getToken() ? (
              <Button variant="secondary" onClick={() => { window.MP.clearToken(); reset(); }}>Sign out</Button>
            ) : (
              <Button variant="ai" onClick={() => setShowLogin(true)}>Sign in</Button>
            )}
            <Button variant="secondary" onClick={() => { setQuery(""); reset(); onClear && onClear(); }}>Clear</Button>
          </>
        }
      />

      {/* Query input */}
      <div className="query-console" style={{ marginBottom: 20 }}>
        <div className="input lg">
          <Icon name="sparkles" size={16} className="fg-ai" />
          <input
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => { if (e.key === "Enter") run(); }}
            placeholder='Ask: "What did the financial press report about the Fed this week?"'
          />
          {phase === "streaming"
            ? <Button variant="danger" onClick={reset}>Stop</Button>
            : <Button variant="ai" trailing={<Icon name="arrowRight" size={14} />} onClick={run}>Send query</Button>}
        </div>
        <div className="qc-suggestions">
          {[
            "What did the financial press report this week about the Federal Reserve?",
            "What's happening with AI chip stocks?",
            "Any major news about European markets?",
          ].map((s) => (
            <span key={s} className="qc-suggestion" onClick={() => setQuery(s)}>{s}</span>
          ))}
        </div>
      </div>

      {/* Error banner */}
      {phase === "error" && (
        <div className="card" style={{ marginBottom: 20, borderColor: "var(--accent-loss-ring)" }}>
          <div className="card-body" style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <Icon name="alert" size={16} className="fg-loss" />
            <span className="fg-loss" style={{ fontSize: 13 }}>{errorMsg}</span>
          </div>
        </div>
      )}

      {/* Two-column: answer + right rail */}
      <div className="two-col">
        <div className="section-stack">
          {/* Agent trace */}
          <Card title="Agent trace" sub="Self-RAG · LangGraph"
            right={<>
              <span>{elapsedLabel}</span>
              <Pill tone={phase === "done" ? "signal" : phase === "refused" ? "caution" : phase === "error" ? "loss" : phase === "streaming" ? "ai" : "neutral"} dot size="sm">
                {phase === "done" ? "Complete" : phase === "refused" ? "Refused" : phase === "error" ? "Error" : phase === "streaming" ? "Streaming" : "Idle"}
              </Pill>
            </>}>
            <div>
              {agents.map((a, i) => <AgentStep key={i} {...a} />)}
            </div>
            {phase === "streaming" && (
              <div className="progress-rail"><div className="bar" /></div>
            )}
          </Card>

          {/* Answer */}
          <Card
            title="Answer"
            sub={phase === "done" ? "graded · ready" : phase === "refused" ? "refused" : phase === "streaming" ? "streaming…" : "awaiting query"}
            right={phase === "done" ? <Pill tone="signal" dot size="sm">Evidence sufficient</Pill> : phase === "refused" ? <Pill tone="caution" dot size="sm">Evidence insufficient</Pill> : null}
          >
            {phase === "idle"
              ? <div className="fg-muted" style={{ padding: "12px 0", fontSize: 13 }}>Submit a query to begin. The graph retrieves, grades evidence, then streams a cited answer — or refuses if the sources are insufficient.</div>
              : (
                <div className="answer">
                  {renderAnswer(streamed)}
                  {phase === "streaming" && <span className="token-cursor" />}
                </div>
              )}

            {(phase === "done" || phase === "refused") && (
              <div className="answer-meta">
                <span className={refused ? "fg-loss" : "fg-signal"}>● {docGrade || "—"}</span>
                <span className="sep">·</span>
                <span>{elapsedLabel}</span>
                <span className="sep">·</span>
                <span>{sources.length} sources</span>
                <span className="sep">·</span>
                <span>{accRef.current.length} chars</span>
              </div>
            )}
          </Card>

          {/* Why this answer */}
          {(phase === "done" || phase === "refused") && (
            <Card title="Why this answer?" sub="Self-RAG transparency"
              right={<>
                <span>kept <span className="fg-signal">{sources.length}</span></span>
                <Pill tone={refused ? "caution" : "signal"} dot size="sm">{refused ? "Evidence insufficient" : "Evidence sufficient"}</Pill>
              </>}>
              {sources.length === 0 ? (
                <div className="fg-muted" style={{ fontSize: 13 }}>No sources were cited for this answer.</div>
              ) : (
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 10 }}>
                  {sources.map((s, i) => <SourceCard key={s.url || i} index={i + 1} source={s} />)}
                </div>
              )}
              <div style={{ marginTop: 14, paddingTop: 14, borderTop: "1px solid var(--border-row)" }}>
                <span className="mono-sm fg-tertiary">Rejected documents are filtered server-side and not exposed by the API.</span>
              </div>
            </Card>
          )}
        </div>

        {/* Right rail */}
        <div className="section-stack">
          <Card title="Evidence" sub="Self-RAG grader" dense>
            <EvidencePanel phase={phase} docGrade={docGrade} kept={sources.length} refused={refused} />
          </Card>
          <Card title="Trace meta" sub="round-trip" dense>
            <TraceMeta phase={phase} elapsedLabel={elapsedLabel} docGrade={docGrade} kept={sources.length} chars={accRef.current.length} />
          </Card>
          <Card title="Citations" sub={`${sources.length} cited`} dense>
            <CitationList sources={sources} />
          </Card>
        </div>
      </div>

      {showLogin && (
        <LoginModal
          onClose={() => setShowLogin(false)}
          onAuthed={() => { setShowLogin(false); setTimeout(run, 50); }}
        />
      )}
    </>
  );
};

/* -------------------- Evidence panel (real doc_grade, no fake score) ------- */
const EvidencePanel = ({ phase, docGrade, kept, refused }) => {
  const decided = phase === "done" || phase === "refused";
  const tone = !decided ? "neutral" : refused ? "caution" : "signal";
  const color = !decided ? "var(--fg-tertiary)" : refused ? "var(--accent-caution)" : "var(--accent-signal)";
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 12 }}>
      <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
        <span className="mono-display" style={{ color }}>{decided ? (docGrade || "—") : "—"}</span>
      </div>
      <div style={{ display: "flex", alignItems: "center", gap: 8, paddingTop: 6, borderTop: "1px solid var(--border-row)" }}>
        <Pill tone={tone} dot size="sm">{decided ? (refused ? "Insufficient" : "Sufficient") : "Awaiting"}</Pill>
        <span className="mono-sm fg-tertiary">{kept} sources kept</span>
      </div>
    </div>
  );
};

/* -------------------- Trace meta (only real fields) ------------------------ */
const TraceMeta = ({ phase, elapsedLabel, docGrade, kept, chars }) => {
  const decided = phase === "done" || phase === "refused";
  const Row = ({ k, v, last }) => (
    <div style={{
      display: "flex", justifyContent: "space-between", alignItems: "baseline",
      padding: "6px 0",
      borderBottom: last ? "none" : "1px solid var(--border-row)",
    }}>
      <span className="mono-sm fg-tertiary" style={{ fontSize: 11 }}>{k}</span>
      <span className="mono-data" style={{ fontSize: 12 }}>{v}</span>
    </div>
  );
  return (
    <div>
      <Row k="doc_grade" v={decided ? (docGrade || "—") : "…"} />
      <Row k="sources_kept" v={decided ? kept : "…"} />
      <Row k="answer_chars" v={decided ? chars : "…"} />
      <Row k="latency" v={elapsedLabel} />
      <Row k="trace_id" v={<span className="fg-tertiary">—</span>} last />
    </div>
  );
};

const CitationList = ({ sources }) => (
  <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
    {sources.length === 0 && <span className="mono-sm fg-tertiary">No citations yet.</span>}
    {sources.map((s, i) => (
      <a key={s.url || i} href={s.url || "#"} target="_blank" rel="noreferrer"
        style={{
          display: "flex", alignItems: "center", gap: 10, textDecoration: "none",
          padding: "6px 0",
          borderBottom: i < sources.length - 1 ? "1px solid var(--border-row)" : "none",
        }}>
        <span className="src-cite" style={{
          fontFamily: "var(--font-mono)", fontSize: 10, fontWeight: 600,
          color: "var(--accent-info)", background: "var(--accent-info-bg)",
          border: "1px solid var(--accent-info-ring)",
          padding: "1px 6px", borderRadius: 4, minWidth: 24, textAlign: "center",
        }}>S{i + 1}</span>
        <span style={{ fontSize: 12, color: "var(--fg-primary)", flex: 1, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{s.name}</span>
        <span className="mono-sm fg-tertiary" style={{ fontSize: 11 }}>{typeof s.score === "number" ? s.score.toFixed(2) : "—"}</span>
        <Icon name="external" size={12} className="fg-tertiary" />
      </a>
    ))}
  </div>
);

/* -------------------- Login / register modal ------------------------------ */
const { useState: useStateL } = React;

const LoginModal = ({ onClose, onAuthed }) => {
  const [mode, setMode] = useStateL("login"); // login | register
  const [username, setUsername] = useStateL("");
  const [password, setPassword] = useStateL("");
  const [busy, setBusy] = useStateL(false);
  const [err, setErr] = useStateL("");

  const submit = async () => {
    setErr("");
    if (username.length < 3) { setErr("Username must be at least 3 characters."); return; }
    if (password.length < 8) { setErr("Password must be at least 8 characters."); return; }
    setBusy(true);
    try {
      if (mode === "register") {
        const reg = await window.MP.register(username, password);
        if (!reg.ok) { setErr(reg.error); setBusy(false); return; }
      }
      const res = await window.MP.login(username, password);
      if (!res.ok) { setErr(res.error); setBusy(false); return; }
      onAuthed();
    } catch (_e) {
      setErr("Network error. Is the API running?");
      setBusy(false);
    }
  };

  return (
    <div onClick={onClose} style={{
      position: "fixed", inset: 0, zIndex: 50,
      background: "rgba(7,9,12,0.7)", backdropFilter: "blur(12px)",
      display: "flex", alignItems: "center", justifyContent: "center",
    }}>
      <div onClick={(e) => e.stopPropagation()} className="card" style={{ width: 380, padding: 0 }}>
        <div className="card-head">
          <span className="title">{mode === "login" ? "Sign in" : "Create account"}</span>
          <div className="right"><Pill tone="ai" size="sm" upper>JWT</Pill></div>
        </div>
        <div className="card-body" style={{ display: "flex", flexDirection: "column", gap: 12 }}>
          <div className="input">
            <Icon name="user" size={14} className="fg-tertiary" />
            <input autoFocus value={username} placeholder="username"
              onChange={(e) => setUsername(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") submit(); }} />
          </div>
          <div className="input">
            <Icon name="settings" size={14} className="fg-tertiary" />
            <input type="password" value={password} placeholder="password (min 8)"
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") submit(); }} />
          </div>
          {err && <span className="fg-loss" style={{ fontSize: 12 }}>{err}</span>}
          <Button variant="ai" onClick={submit}>
            {busy ? "Working…" : mode === "login" ? "Sign in" : "Create account & sign in"}
          </Button>
          <span className="mono-sm fg-tertiary" style={{ fontSize: 11, cursor: "pointer" }}
            onClick={() => { setMode(mode === "login" ? "register" : "login"); setErr(""); }}>
            {mode === "login" ? "No account? Create one." : "Have an account? Sign in."}
          </span>
        </div>
      </div>
    </div>
  );
};

window.QueryConsole = QueryConsole;
