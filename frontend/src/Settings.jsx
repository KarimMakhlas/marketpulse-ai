/* Settings screen — read-only runtime + compiled configuration.
 *
 * Runtime values (version, model, default k, DB/Redis) are fetched live from
 * GET /health. The rest are the actual compiled defaults from the backend
 * (retriever.py, indexer.py, security.py, app.py rate-limit decorators) shown
 * read-only — there is no config-write API, so there is no fake "Save". */

const { useState: useStateS, useEffect: useEffectS } = React;

const Field = ({ label, hint, value, suffix }) => (
  <div style={{
    display: "grid", gridTemplateColumns: "1fr 200px",
    alignItems: "center", gap: 24, padding: "12px 0",
    borderBottom: "1px solid var(--border-row)",
  }}>
    <div>
      <div style={{ fontSize: 14, fontWeight: 500, color: "var(--fg-primary)" }}>{label}</div>
      {hint && <div style={{ fontSize: 12, color: "var(--fg-tertiary)", marginTop: 2 }}>{hint}</div>}
    </div>
    <div className="input" style={{ height: 32, justifyContent: "space-between" }}>
      <span className="mono-data" style={{ fontSize: 13 }}>{value}</span>
      {suffix && <span className="mono-sm fg-tertiary">{suffix}</span>}
    </div>
  </div>
);

const Settings = () => {
  const [health, setHealth] = useStateS(null);
  const [loaded, setLoaded] = useStateS(false);

  useEffectS(() => {
    let alive = true;
    window.MP.health().then((h) => { if (alive) { setHealth(h); setLoaded(true); } });
    return () => { alive = false; };
  }, []);

  const v = (x) => (loaded ? (x == null ? "—" : x) : "…");

  return (
    <>
      <PageHead
        eyebrow="Admin"
        title="Settings"
        subtitle="Runtime status + compiled defaults · read-only (config is code/env-driven)"
        actions={<Pill tone="neutral" size="sm" upper>read-only</Pill>}
      />

      <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 20 }}>
        <Card title="Runtime" sub="live · GET /health">
          <Field label="API version" value={v(health && health.version)}/>
          <Field label="LLM model" hint="Routed via the LLMProvider abstraction." value={v(health && health.model)}/>
          <Field label="Default retrieval k" hint="Documents passed to synthesis." value={v(health && health.default_k)}/>
          <Field label="Database" hint="Postgres audit + user store." value={loaded ? (health && health.db ? "connected" : "offline") : "…"}/>
          <Field label="Redis" hint="Rate-limit backing store (else in-memory)." value={loaded ? (health && health.redis ? "configured" : "in-memory") : "…"}/>
        </Card>

        <Card title="Retrieval policy" sub="compiled · retriever.py">
          <Field label="Similarity weight" hint="Cosine similarity in the blend." value="0.60"/>
          <Field label="Recency weight" hint="Exponential age decay." value="0.25"/>
          <Field label="Credibility weight" hint="Per-source credibility." value="0.15"/>
          <Field label="MMR lambda" hint="0 = diversity, 1 = pure relevance." value="0.70"/>
          <Field label="Candidate pool" hint="Fetched before MMR re-rank." value="k × 4"/>
        </Card>

        <Card title="Embedding + chunking" sub="compiled · indexer.py">
          <Field label="Embedding model" value="bge-small-en-v1.5"/>
          <Field label="Vector space" hint="Paired with normalized embeddings." value="cosine"/>
          <Field label="Chunk size" value="800" suffix="chars"/>
          <Field label="Chunk overlap" value="120" suffix="chars"/>
        </Card>

        <Card title="Auth + rate limits" sub="compiled · security.py / app.py">
          <Field label="JWT expiry" hint="JWT_EXPIRE_MINUTES env (default)." value="60" suffix="min"/>
          <Field label="Query rate limit" value="30 / min"/>
          <Field label="Register rate limit" value="10 / min"/>
          <Field label="Login rate limit" value="20 / min"/>
        </Card>
      </div>
    </>
  );
};

window.Settings = Settings;
