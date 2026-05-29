/* Dashboard screen for MarketPulse AI. */

const { useState: useStateD, useEffect: useEffectD } = React;

/* sparkline data */
const sparkUp   = [0.20, 0.22, 0.26, 0.30, 0.28, 0.34, 0.40, 0.44, 0.48, 0.52, 0.58, 0.62];
const sparkFlat = [0.40, 0.44, 0.42, 0.46, 0.44, 0.48, 0.46, 0.50, 0.48, 0.52, 0.50, 0.54];
const sparkLat  = [0.30, 0.32, 0.34, 0.30, 0.36, 0.38, 0.32, 0.40, 0.44, 0.40, 0.46, 0.50];
const faithSeries = [0.82, 0.84, 0.85, 0.83, 0.86, 0.87, 0.85, 0.88, 0.89, 0.87, 0.89, 0.88, 0.89, 0.90, 0.89, 0.91, 0.88, 0.89, 0.87, 0.88, 0.89, 0.90, 0.89, 0.89];
const relSeries   = [0.78, 0.80, 0.81, 0.79, 0.82, 0.83, 0.81, 0.84, 0.85, 0.83, 0.85, 0.84, 0.85, 0.86, 0.84, 0.86, 0.83, 0.84, 0.83, 0.84, 0.85, 0.86, 0.84, 0.84];

const Dashboard = ({ onAskQuery }) => {
  const [query, setQuery] = useStateD("");
  const submit = () => {
    if (query.trim()) onAskQuery(query.trim());
  };

  const suggestions = [
    "Did NVIDIA beat earnings expectations?",
    "How did analysts react to NVIDIA's latest guidance?",
    "What changed in Apple's 10-Q filing?",
    "Risk factors in TSLA delivery miss?",
    "Summarize Fed minutes from this week",
  ];

  return (
    <>
      <PageHead
        title="Dashboard"
        subtitle="Real-time intelligence over 9 ingestion sources · evaluated by RAGAS on a rolling 24 h window"
        actions={
          <>
            <Pill tone="signal" dot>Live</Pill>
            <Button leading={<Icon name="download" size={14}/>}>Export run</Button>
            <Button variant="ai" leading={<Icon name="sparkles" size={14}/>} onClick={() => onAskQuery("")}>Ask a query</Button>
          </>
        }
      />

      {/* KPI row */}
      <div className="kpi-grid" style={{ marginBottom: 20 }}>
        <Kpi
          label="Articles today"
          value="52,430"
          delta="↑ +12% vs. 24h"
          deltaTone="signal"
          spark={sparkUp}
          sparkColor="#00E08F"
        />
        <Kpi
          label="RAGAS faithfulness"
          value="0.89"
          delta="↑ +0.02 vs. 24h"
          deltaTone="signal"
          spark={sparkFlat}
          sparkColor="#00E08F"
          accessory={<Pill tone="ai" size="sm">RAGAS</Pill>}
        />
        <Kpi
          label="Avg latency"
          value="1.8"
          unit="s"
          delta="↑ +0.2 s vs. 24h"
          deltaTone="caution"
          spark={sparkLat}
          sparkColor="#FFB020"
        />
        <Kpi
          label="Hallucination alerts"
          value="0"
          delta="last 24h · all clear"
          deltaTone="tertiary"
        />
      </div>

      <div className="kpi-grid" style={{ gridTemplateColumns: "repeat(4, 1fr)", marginBottom: 24 }}>
        <Kpi label="Active sources" value="9" delta="all healthy" deltaTone="signal"/>
        <Kpi label="Queries today" value="2,481" delta="↑ +18%" deltaTone="signal"/>
        <Kpi label="Avg cost / query" value="$0.0042" delta="−$0.0003" deltaTone="signal"/>
        <Kpi label="Kafka lag" value="4" unit="ms" delta="● ingestion healthy" deltaTone="signal"/>
      </div>

      {/* Live query bar */}
      <Card
        title="Live market intelligence"
        sub="WebSocket /query/stream"
        right={<><Pill tone="ai" size="sm" upper>Synthesis</Pill><span>5 agents online</span></>}
        style={{ marginBottom: 20 }}
      >
        <div className="query-console" style={{ padding: 0, background: "transparent", border: "none", boxShadow: "none" }}>
          <div className="input lg">
            <Icon name="sparkles" size={16} className="fg-ai"/>
            <input
              placeholder='Ask: "Did NVIDIA beat earnings expectations?"'
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
              <span key={s} className="qc-suggestion" onClick={() => { setQuery(s); }}>{s}</span>
            ))}
          </div>
        </div>
      </Card>

      {/* Quality monitoring charts */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>
        <Card
          title="RAGAS faithfulness · 24 h"
          sub="threshold 0.80"
          right={<><span>min 0.82</span><span>max 0.91</span><span className="fg-signal">avg 0.87</span></>}
        >
          <AreaChart data={faithSeries} color="#00E08F" height={180} yMin={0.7} yMax={1.0} threshold={0.80}/>
        </Card>
        <Card
          title="Answer relevancy · 24 h"
          sub="threshold 0.75"
          right={<><span>min 0.78</span><span>max 0.86</span><span className="fg-signal">avg 0.83</span></>}
        >
          <AreaChart data={relSeries} color="#7C5CFF" height={180} yMin={0.7} yMax={1.0} threshold={0.75}/>
        </Card>
      </div>

      {/* Ingestion + Latest eval row */}
      <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 20 }}>
        <Card title="Kafka ingestion" sub="raw → clean → embedded → ChromaDB" right={<Pill tone="signal" dot size="sm">Streaming</Pill>}>
          <DashboardKafkaPipeline/>
        </Card>
        <Card title="Latest evaluation run" sub="rolling 1 h"
              right={<a className="fg-ai" style={{ fontFamily: "var(--font-mono)", fontSize: 11 }}>tr_eval_4f8a → </a>}>
          <DashboardEvalRun/>
        </Card>
      </div>
    </>
  );
};

const DashboardKafkaPipeline = () => {
  const Topic = ({ name, count, rate, sink }) => (
    <div style={{
      flex: 1,
      background: sink ? "var(--accent-info-bg)" : "var(--bg-inset)",
      border: `1px solid ${sink ? "var(--accent-info-ring)" : "var(--border-subtle)"}`,
      borderRadius: 4, padding: "10px 12px",
      display: "flex", flexDirection: "column", gap: 4,
      fontFamily: "var(--font-mono)",
    }}>
      <span style={{ fontSize: 11, color: "var(--accent-info)", fontWeight: 600 }}>{name}</span>
      <span style={{ fontSize: 16, color: "var(--fg-primary)", fontVariantNumeric: "tabular-nums" }}>{count}</span>
      {rate && <span style={{ fontSize: 10, color: "var(--fg-tertiary)" }}>{rate}</span>}
    </div>
  );
  const Arrow = () => (
    <div style={{ width: 22, color: "var(--accent-info)", display: "flex", alignItems: "center", justifyContent: "center" }}>
      <Icon name="arrowRight" size={14}/>
    </div>
  );
  return (
    <div style={{ display: "flex", alignItems: "stretch", gap: 0 }}>
      <Topic name="raw.articles" count="52,430" rate="↑ 47/s"/>
      <Arrow/>
      <Topic name="clean.articles" count="52,408" rate="↑ 47/s · 0.04% drop"/>
      <Arrow/>
      <Topic name="embedded.articles" count="52,401" rate="↑ 46/s"/>
      <Arrow/>
      <Topic name="ChromaDB" count="52,401" sink/>
    </div>
  );
};

const DashboardEvalRun = () => {
  const M = ({ label, value, tone, last }) => (
    <div style={{
      display: "grid", gridTemplateColumns: "1fr auto",
      alignItems: "center",
      padding: "8px 0",
      borderBottom: last ? "none" : "1px solid var(--border-row)",
    }}>
      <span style={{ fontSize: 13, color: "var(--fg-secondary)" }}>{label}</span>
      <span className="mono-data" style={{ color: `var(--accent-${tone})` }}>{value}</span>
    </div>
  );
  return (
    <div>
      <M label="Faithfulness" value="0.89" tone="signal"/>
      <M label="Answer relevancy" value="0.84" tone="signal"/>
      <M label="Context precision" value="0.81" tone="signal"/>
      <M label="Hallucination rate" value="7.4%" tone="caution"/>
      <M label="Avg cost / query" value="$0.0042" tone="ai" last/>
    </div>
  );
};

window.Dashboard = Dashboard;
