/* Dashboard screen for MarketPulse AI.
 *
 * KPIs are wired to the live backend (GET /stats, GET /health). Metrics the
 * backend does not yet expose (RAGAS scores, latency, cost, Kafka lag) render
 * as "—" rather than fabricated numbers — see the honest-UI principle. The
 * query bar routes into the live QueryConsole. */

const { useState: useStateD, useEffect: useEffectD } = React;

const fmtInt = (n) => (typeof n === "number" ? n.toLocaleString() : "—");

const Dashboard = ({ onAskQuery }) => {
  const [query, setQuery] = useStateD("");
  const [stats, setStats] = useStateD(null);
  const [health, setHealth] = useStateD(null);
  const [loaded, setLoaded] = useStateD(false);

  useEffectD(() => {
    let alive = true;
    Promise.all([window.MP.stats(), window.MP.health()]).then(([s, h]) => {
      if (!alive) return;
      setStats(s);
      setHealth(h);
      setLoaded(true);
    });
    return () => { alive = false; };
  }, []);

  const submit = () => {
    if (query.trim()) onAskQuery(query.trim());
  };

  const suggestions = [
    "What did the financial press report this week about the Federal Reserve?",
    "What's happening with AI chip stocks?",
    "Any major news about European markets?",
    "Summarize recent SEC 8-K filings",
  ];

  const dbOnline = !!(stats && stats.db_available);
  const articles = stats ? stats.articles_indexed : null;
  const queriesToday = stats ? stats.queries_today : null;
  const sourcesActive = stats ? stats.sources_active : null;

  return (
    <>
      <PageHead
        title="Dashboard"
        subtitle="Self-RAG over the indexed financial-news corpus · live counters from the API"
        actions={
          <>
            <Pill tone={dbOnline ? "signal" : "caution"} dot>{dbOnline ? "DB online" : "DB offline"}</Pill>
            <Button variant="ai" leading={<Icon name="sparkles" size={14}/>} onClick={() => onAskQuery("")}>Ask a query</Button>
          </>
        }
      />

      {/* KPI row — real values from /stats, "—" where the API has no metric yet */}
      <div className="kpi-grid" style={{ marginBottom: 20 }}>
        <Kpi
          label="Articles indexed"
          value={loaded ? fmtInt(articles) : "…"}
          delta={dbOnline ? "ChromaDB · live" : "Chroma unreachable"}
          deltaTone={articles == null ? "caution" : "signal"}
        />
        <Kpi
          label="Queries today"
          value={loaded ? fmtInt(queriesToday) : "…"}
          delta={queriesToday == null ? "Postgres not configured" : "since 00:00 UTC"}
          deltaTone={queriesToday == null ? "tertiary" : "signal"}
        />
        <Kpi
          label="Active sources"
          value={loaded ? fmtInt(sourcesActive) : "…"}
          delta="ingestion feeds"
          deltaTone="signal"
        />
        <Kpi
          label="Model"
          value={health ? health.model : "…"}
          delta={health ? `k = ${health.default_k} · v${health.version}` : "—"}
          deltaTone="ai"
          accessory={<Pill tone="ai" size="sm">LLM</Pill>}
        />
      </div>

      {/* Live query bar — routes into the streaming QueryConsole */}
      <Card
        title="Live market intelligence"
        sub="WebSocket /query/stream"
        right={<Pill tone="ai" size="sm" upper>Self-RAG</Pill>}
        style={{ marginBottom: 20 }}
      >
        <div className="query-console" style={{ padding: 0, background: "transparent", border: "none", boxShadow: "none" }}>
          <div className="input lg">
            <Icon name="sparkles" size={16} className="fg-ai"/>
            <input
              placeholder='Ask: "Did the Fed signal a rate change this week?"'
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={(e) => { if (e.key === "Enter") submit(); }}
            />
            <Button variant="ai" trailing={<Icon name="arrowRight" size={14}/>} onClick={submit}>
              Send query
            </Button>
          </div>
          <div className="qc-suggestions">
            {suggestions.map((s) => (
              <span key={s} className="qc-suggestion" onClick={() => setQuery(s)}>{s}</span>
            ))}
          </div>
        </div>
      </Card>

      {/* Quality monitoring — honest "not yet wired" state */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        <Card title="Evaluation" sub="RAGAS">
          <NotWired
            line="RAGAS scores are produced on demand by `make eval`, not streamed to the dashboard yet."
            hint="Faithfulness · answer relevancy · context precision"
          />
        </Card>
        <Card title="Pipeline health" sub="ingestion">
          <NotWired
            line="Per-source freshness and Kafka lag are not exposed by the API yet."
            hint={dbOnline ? `${fmtInt(articles)} chunks currently indexed` : "Run `make ingest` to populate the index"}
          />
        </Card>
      </div>
    </>
  );
};

/* Honest placeholder for sections with no backing endpoint yet. */
const NotWired = ({ line, hint }) => (
  <div style={{ display: "flex", flexDirection: "column", gap: 8, padding: "8px 0" }}>
    <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
      <Icon name="info" size={14} className="fg-tertiary"/>
      <span className="mono-sm fg-tertiary" style={{ fontSize: 12 }}>Not yet wired</span>
    </div>
    <span style={{ fontSize: 13, color: "var(--fg-secondary)" }}>{line}</span>
    {hint && <span className="mono-sm fg-tertiary" style={{ fontSize: 11 }}>{hint}</span>}
  </div>
);

window.Dashboard = Dashboard;
