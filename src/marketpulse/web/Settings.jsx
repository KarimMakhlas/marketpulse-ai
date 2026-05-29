/* Settings screen — concise admin form */

const Settings = () => {
  const Field = ({ label, hint, value, mono, suffix, lock }) => (
    <div style={{
      display: "grid", gridTemplateColumns: "1fr 220px",
      alignItems: "center", gap: 24, padding: "14px 0",
      borderBottom: "1px solid var(--border-row)",
    }}>
      <div>
        <div style={{ fontSize: 14, fontWeight: 500, color: "var(--fg-primary)" }}>{label}</div>
        <div style={{ fontSize: 12, color: "var(--fg-tertiary)", marginTop: 2 }}>{hint}</div>
      </div>
      <div className="input" style={{ height: 32, justifyContent: "space-between" }}>
        <span className={mono ? "mono-data" : ""} style={{ fontSize: 13 }}>{value}</span>
        {suffix && <span className="mono-sm fg-tertiary">{suffix}</span>}
        {lock && <Icon name="settings" size={12} className="fg-tertiary"/>}
      </div>
    </div>
  );
  return (
    <>
      <PageHead
        eyebrow="Admin"
        title="Settings"
        subtitle="Retrieval, evaluation, source weighting, model + rate limits"
        actions={<>
          <Button>Discard</Button>
          <Button variant="ai">Save changes</Button>
        </>}
      />

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        <Card title="Retrieval" sub="ChromaDB · text-embed-3">
          <Field label="Max source age" hint="Drop sources older than this." mono value="30 days"/>
          <Field label="Initial retrieval k" hint="Documents pulled from vector store before critique." mono value="12"/>
          <Field label="Final reranked documents" hint="Documents passed to Synthesis Agent." mono value="5"/>
          <Field label="Minimum credible sources" hint="Below this, surface 'Evidence insufficient'." mono value="2"/>
        </Card>

        <Card title="Evaluation" sub="RAGAS · Langfuse">
          <Field label="Faithfulness alert threshold" hint="Fires PagerDuty when 5 m avg below this." mono value="0.80"/>
          <Field label="Hallucination alert threshold" hint="Fires when 5 m rate exceeds this." mono value="10%"/>
          <Field label="Min confidence to ship" hint="Below this, append 'verify with cited sources'." mono value="0.55"/>
          <Field label="Eval rolling window" hint="RAGAS window for headline scores." mono value="24 h"/>
        </Card>

        <Card title="Models" sub="provider · routing">
          <Field label="Router" hint="Intent classification." mono value="haiku-4-5"/>
          <Field label="Critique + Grader" hint="Self-RAG critique + faithfulness scoring." mono value="haiku-4-5"/>
          <Field label="Synthesis" hint="Answer generation." mono value="sonnet-4-5"/>
          <Field label="User rate limit" hint="Queries per minute, per user." mono value="60 / min"/>
        </Card>

        <Card title="Source weighting" sub="multiplier applied at retrieval rerank">
          <Field label="Reuters" mono value="0.95×" hint="Newswire · verified."/>
          <Field label="Bloomberg" mono value="0.94×" hint="Newswire · verified."/>
          <Field label="SEC EDGAR" mono value="0.99×" hint="Primary filings."/>
          <Field label="Reddit · X" mono value="0.35×" hint="Down-weighted social signals."/>
        </Card>
      </div>
    </>
  );
};

window.Settings = Settings;
