/* LLMOps Monitoring screen.
 *
 * Quality metrics (RAGAS faithfulness/relevancy/precision, latency, cost) are
 * NOT streamed to the API yet, so this screen does not fabricate charts. It
 * explains what exists today and what each panel needs to go live. When an
 * eval/metrics endpoint lands, the placeholders here become real charts. */

const Monitoring = () => {
  return (
    <>
      <PageHead
        eyebrow="LLMOps"
        title="AI quality monitoring"
        subtitle="Evaluation + observability · not yet streamed to the dashboard"
        actions={<Pill tone="caution" size="sm" dot>Not wired</Pill>}
      />

      <div className="kpi-grid" style={{ marginBottom: 20 }}>
        <Kpi label="Faithfulness" value="—" delta="RAGAS · run `make eval`" deltaTone="tertiary" accessory={<Pill tone="ai" size="sm">RAGAS</Pill>}/>
        <Kpi label="Answer relevancy" value="—" delta="RAGAS · run `make eval`" deltaTone="tertiary" accessory={<Pill tone="ai" size="sm">RAGAS</Pill>}/>
        <Kpi label="Context precision" value="—" delta="RAGAS · run `make eval`" deltaTone="tertiary" accessory={<Pill tone="ai" size="sm">RAGAS</Pill>}/>
        <Kpi label="Refusals logged" value="—" delta="alerts table · no endpoint yet" deltaTone="tertiary"/>
      </div>

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20, marginBottom: 20 }}>
        <Card title="RAGAS evaluation" sub="scripts/evaluate.py">
          <EmptyState
            icon="info"
            title="Run on demand, not streamed"
            line="RAGAS scores are produced by `make eval` against a fixed question set and printed to the terminal. Wiring a periodic eval job + a /metrics endpoint would make these charts live."
          />
        </Card>
        <Card title="Tracing" sub="Langfuse @observe">
          <EmptyState
            icon="info"
            title="Active only with credentials"
            line="The grader and answer nodes are wrapped with Langfuse @observe. Set LANGFUSE_* env vars to send traces; otherwise it is a transparent no-op and nothing surfaces here."
          />
        </Card>
      </div>

      <Card title="What's needed to light this up" sub="roadmap">
        <div style={{ display: "flex", flexDirection: "column", gap: 0 }}>
          <Step n="1" title="Periodic eval job" line="Schedule scripts/evaluate.py and persist scores (e.g. an eval_runs table)."/>
          <Step n="2" title="GET /metrics endpoint" line="Expose the latest eval scores + refusal counts (alerts table) over the API."/>
          <Step n="3" title="Wire charts" line="Replace these placeholders with the live series, same as the Query Console."/>
        </div>
      </Card>
    </>
  );
};

const Step = ({ n, title, line }) => (
  <div style={{ display: "flex", gap: 12, alignItems: "flex-start", padding: "12px 0", borderBottom: "1px solid var(--border-row)" }}>
    <span style={{
      flexShrink: 0, width: 22, height: 22, borderRadius: 999,
      display: "inline-flex", alignItems: "center", justifyContent: "center",
      background: "var(--accent-ai-bg)", border: "1px solid var(--accent-ai-ring)",
      color: "var(--accent-ai)", fontFamily: "var(--font-mono)", fontSize: 11, fontWeight: 600,
    }}>{n}</span>
    <div>
      <div style={{ fontSize: 14, fontWeight: 500, color: "var(--fg-primary)" }}>{title}</div>
      <div style={{ fontSize: 13, color: "var(--fg-tertiary)", marginTop: 2 }}>{line}</div>
    </div>
  </div>
);

window.Monitoring = Monitoring;
