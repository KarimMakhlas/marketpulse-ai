/* Cards + content blocks — Card, EmptyState, Kpi, AgentStep, SourceCard,
   and the inline citation renderer. Depend on primitives (Icon) and charts
   (Spark), both loaded earlier. Exported to window. */

/* -------------------- Card -------------------- */
const Card = ({ title, sub, right, dense, children, style }) => (
  <div className="card" style={style}>
    {(title || right) && (
      <div className="card-head">
        {title && <span className="title">{title}</span>}
        {sub && <span className="sub">{sub}</span>}
        {right && <div className="right">{right}</div>}
      </div>
    )}
    <div className={`card-body ${dense ? "dense" : ""}`}>{children}</div>
  </div>
);

/* -------------------- Empty / auth / error state -------------------- */
/* Shared placeholder for data-backed screens with no rows, no auth, or a
   failed fetch. Keeps "no data" visually distinct from fabricated data. */
const EmptyState = ({ icon, title, line }) => (
  <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 8, padding: "32px 16px", textAlign: "center" }}>
    <Icon name={icon} size={20} className="fg-tertiary"/>
    <span style={{ fontSize: 14, fontWeight: 500, color: "var(--fg-primary)" }}>{title}</span>
    <span style={{ fontSize: 13, color: "var(--fg-tertiary)", maxWidth: 420 }}>{line}</span>
  </div>
);

/* -------------------- KPI Card -------------------- */
const Kpi = ({ label, value, unit, deltaTone = "signal", delta, spark, sparkColor, accessory }) => (
  <div className="kpi">
    <div className="kpi-eyebrow">
      <span className="label">{label}</span>
      {accessory}
    </div>
    <div className="kpi-num">{value}{unit && <span className="unit">{unit}</span>}</div>
    {delta && <div className={`kpi-delta fg-${deltaTone}`}>{delta}</div>}
    {spark && <div className="kpi-spark"><Spark points={spark} color={sparkColor}/></div>}
  </div>
);

/* -------------------- Agent Step -------------------- */
const AGENTS = {
  router:     { label: "Router",     ico: "/projects/this/assets/icons/agent-router.svg" },
  retrieval:  { label: "Retrieval",  ico: "agent-retrieval" },
  critique:   { label: "Critique",   ico: "agent-critique" },
  synthesis:  { label: "Synthesis",  ico: "agent-synthesis" },
  grader:     { label: "Grader",     ico: "agent-grader" },
};

const AgentIco = ({ which, state }) => {
  if (state === "active") {
    return <Icon name="sparkles" size={14} stroke={1.8} className="spin"/>;
  }
  if (state === "done") {
    return <Icon name="check" size={14} stroke={2.5}/>;
  }
  if (state === "error") {
    return <Icon name="x" size={14} stroke={2.5}/>;
  }
  // pending — small dot
  return <span style={{ width: 6, height: 6, borderRadius: 999, background: "currentColor", opacity: 0.4 }}/>;
};

const AgentStep = ({ agent, state, desc, duration, cost }) => (
  <div className={`agent-step ${state}`}>
    <div className="ico"><AgentIco state={state}/></div>
    <span className="label">{AGENTS[agent].label}</span>
    <span className="desc">{desc}</span>
    <span className="dur">{duration || "—"}</span>
    <span className="cost">{cost || "—"}</span>
  </div>
);

/* -------------------- Source Card -------------------- */
// Tolerant numeric format: backend citations expose similarity/recency/score;
// fixture data used credibility/relevance. Show whatever is present, never fake.
const fmtMetric = (v) => (typeof v === "number" ? v.toFixed(2) : "—");

const SourceCard = ({ index, source, rejected }) => {
  const sim = source.similarity ?? source.relevance;
  const score = source.score ?? source.credibility;
  return (
    <div className={`source ${rejected ? "rejected" : ""}`}>
      <div className="src-top">
        <span className="src-cite">{rejected ? "✕" : `S${index}`}</span>
        <span className="src-name">{source.name}</span>
        <span className="src-date">{source.date}</span>
      </div>
      <div className="src-meta">
        <span>sim <span className="strong">{fmtMetric(sim)}</span></span>
        <span>recency {fmtMetric(source.recency)}</span>
        <span>score {fmtMetric(score)}</span>
      </div>
      <p className="src-excerpt">{rejected ? source.rejectReason : source.excerpt}</p>
    </div>
  );
};

/* -------------------- Cite-rendering helper -------------------- */
// turns "text [S1][S2]" into spans
const renderAnswer = (text, onCiteClick) => {
  const parts = text.split(/(\[S\d+\])/g);
  return parts.map((p, i) => {
    const m = p.match(/^\[S(\d+)\]$/);
    if (m) return <span key={i} className="cite-mark" onClick={() => onCiteClick && onCiteClick(+m[1])}>S{m[1]}</span>;
    return <span key={i}>{p}</span>;
  });
};

Object.assign(window, { Card, EmptyState, Kpi, AgentStep, AGENTS, SourceCard, renderAnswer });
