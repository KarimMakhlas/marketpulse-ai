/* LLMOps Monitoring screen */

const faith24h = Array.from({length: 48}, (_, i) => 0.85 + Math.sin(i / 4) * 0.04 + Math.random() * 0.02);
const rel24h   = Array.from({length: 48}, (_, i) => 0.82 + Math.sin(i / 5 + 1) * 0.03 + Math.random() * 0.02);
const prec24h  = Array.from({length: 48}, (_, i) => 0.80 + Math.cos(i / 4) * 0.03 + Math.random() * 0.02);
const halluc24h = [4.2, 3.8, 4.5, 5.1, 4.9, 5.4, 6.1, 5.8, 6.3, 7.2, 7.8, 7.1, 6.4, 5.9, 6.7, 7.4, 8.1, 7.6, 6.9, 7.2, 7.8, 7.4, 6.8, 7.4];

const Monitoring = () => {
  return (
    <>
      <PageHead
        eyebrow="LLMOps"
        title="AI quality monitoring"
        subtitle="RAGAS evaluations on a rolling 24 h window · 2,481 queries · alerts fire when faithfulness < 0.80"
        actions={
          <>
            <div className="input" style={{ width: 160, height: 32 }}>
              <Icon name="filter" size={12} className="fg-tertiary"/>
              <span className="mono-sm">last 24 h</span>
              <Icon name="chevron" size={10} className="fg-tertiary"/>
            </div>
            <Button leading={<Icon name="refresh" size={14}/>}>Refresh</Button>
            <Button variant="ai" leading={<Icon name="alert" size={14}/>}>Configure alerts</Button>
          </>
        }
      />

      {/* Headline KPIs */}
      <div className="kpi-grid" style={{ marginBottom: 20 }}>
        <Kpi label="Faithfulness" value="0.89"
             accessory={<Pill tone="ai" size="sm">RAGAS</Pill>}
             delta="↑ +0.02" deltaTone="signal" spark={faith24h.map(v => (v - 0.7) / 0.3)} sparkColor="#00E08F"/>
        <Kpi label="Answer relevancy" value="0.84"
             accessory={<Pill tone="ai" size="sm">RAGAS</Pill>}
             delta="↑ +0.01" deltaTone="signal" spark={rel24h.map(v => (v - 0.7) / 0.3)} sparkColor="#7C5CFF"/>
        <Kpi label="Context precision" value="0.81"
             accessory={<Pill tone="ai" size="sm">RAGAS</Pill>}
             delta="− flat" deltaTone="tertiary" spark={prec24h.map(v => (v - 0.7) / 0.3)} sparkColor="#4DA3FF"/>
        <Kpi label="Hallucination rate" value="7.4" unit="%"
             delta="↑ +1.2 pts" deltaTone="caution" spark={halluc24h.map(v => v / 10)} sparkColor="#FFB020"/>
      </div>

      {/* Big charts */}
      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>
        <Card
          title="RAGAS metrics · 24 h"
          sub="three series, shared y-axis"
          right={<div className="chart-legend">
            <span className="item"><span className="swatch" style={{ background: "#00E08F" }}/>Faithfulness</span>
            <span className="item"><span className="swatch" style={{ background: "#7C5CFF" }}/>Relevancy</span>
            <span className="item"><span className="swatch" style={{ background: "#4DA3FF" }}/>Precision</span>
          </div>}>
          <MultiLineChart
            series={[
              { label: "Faithfulness", color: "#00E08F", data: faith24h },
              { label: "Relevancy",    color: "#7C5CFF", data: rel24h },
              { label: "Precision",    color: "#4DA3FF", data: prec24h },
            ]}
            height={220} yMin={0.7} yMax={1.0}
          />
        </Card>
        <Card title="Hallucination rate · 24 h" sub="% of queries flagged · threshold 5%"
              right={<><span>min 3.8%</span><span>max 8.1%</span><span className="fg-caution">avg 6.4%</span></>}>
          <BarChart data={halluc24h} color="#FFB020" height={220} yMax={10}/>
        </Card>
      </div>

      {/* Latency per agent */}
      <div style={{ display: "grid", gridTemplateColumns: "1.4fr 1fr", gap: 20, marginBottom: 20 }}>
        <Card title="Latency per agent · p50 / p95 / p99"
              sub="last 24 h · 2,481 queries"
              right={<Pill tone="signal" dot size="sm">All under SLO</Pill>}>
          <AgentLatencyTable/>
        </Card>
        <Card title="Cost per query · 24 h"
              sub="claude-haiku-4-5"
              right={<>
                <span>min $0.0029</span>
                <span>max $0.0061</span>
                <span className="fg-ai">avg $0.0042</span>
              </>}>
          <CostChart/>
        </Card>
      </div>

      {/* Alerts feed */}
      <Card title="Active alerts" sub="last 7 days"
            right={<><Pill tone="loss" size="sm" dot>2 firing</Pill><Pill tone="caution" size="sm" dot>1 warn</Pill></>}>
        <AlertsTable/>
      </Card>
    </>
  );
};

const AgentLatencyTable = () => {
  const rows = [
    { agent: "Router",    p50: 110, p95: 140, p99: 180, share: 0.07 },
    { agent: "Retrieval", p50: 220, p95: 310, p99: 410, share: 0.13 },
    { agent: "Critique",  p50: 380, p95: 480, p99: 540, share: 0.22 },
    { agent: "Synthesis", p50: 920, p95: 1380, p99: 1820, share: 0.51 },
    { agent: "Grader",    p50: 130, p95: 180, p99: 230, share: 0.07 },
  ];
  return (
    <table className="tbl">
      <thead><tr>
        <th>Agent</th><th>p50</th><th>p95</th><th>p99</th><th>Share</th><th></th>
      </tr></thead>
      <tbody>
        {rows.map(r => (
          <tr key={r.agent}>
            <td><Pill tone="ai" size="sm" upper>{r.agent}</Pill></td>
            <td className="num">{r.p50} ms</td>
            <td className="num">{r.p95} ms</td>
            <td className="num">{r.p99} ms</td>
            <td className="num fg-secondary">{(r.share * 100).toFixed(0)}%</td>
            <td style={{ width: 160 }}>
              <div style={{ height: 6, background: "var(--bg-inset)", borderRadius: 999, overflow: "hidden" }}>
                <div style={{ height: "100%", width: `${r.share * 100}%`, background: "var(--accent-ai)" }}/>
              </div>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

const CostChart = () => {
  // small line chart inline
  const data = Array.from({length: 24}, (_, i) => 0.0035 + Math.sin(i / 3) * 0.0008 + Math.random() * 0.0006);
  return <AreaChart data={data} color="#7C5CFF" height={220} yMin={0.002} yMax={0.007}/>;
};

const AlertsTable = () => {
  const rows = [
    { tone: "loss",    sev: "Critical", t: "2 min ago",  rule: "Faithfulness < 0.80",      val: "0.78", scope: "global · last 5 m" },
    { tone: "loss",    sev: "Critical", t: "14 min ago", rule: "Hallucination rate > 10%", val: "11.2%", scope: "synthesis" },
    { tone: "caution", sev: "Warn",     t: "1 h ago",    rule: "Avg latency > 2.5 s",       val: "2.7 s", scope: "p95" },
  ];
  return (
    <table className="tbl">
      <thead><tr>
        <th>Severity</th><th>Triggered</th><th>Rule</th><th>Value</th><th>Scope</th><th></th>
      </tr></thead>
      <tbody>
        {rows.map((r, i) => (
          <tr key={i}>
            <td><Pill tone={r.tone} size="sm" upper>{r.sev}</Pill></td>
            <td className="num fg-tertiary">{r.t}</td>
            <td>{r.rule}</td>
            <td className={`num fg-${r.tone}`}>{r.val}</td>
            <td className="fg-secondary">{r.scope}</td>
            <td style={{ textAlign: "right" }}>
              <Button size="sm" variant="ghost" trailing={<Icon name="arrowRight" size={11}/>}>Inspect</Button>
            </td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

window.Monitoring = Monitoring;
