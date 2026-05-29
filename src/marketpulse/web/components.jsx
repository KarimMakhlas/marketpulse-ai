/* Shared components for MarketPulse AI Web UI Kit.
   All exported to window for cross-Babel-file access. */

const { useState, useEffect, useRef, useMemo } = React;

/* -- tiny inline icon helper. Stroke-based, Lucide-style. -- */
const Icon = ({ name, size = 16, stroke = 1.5, ...rest }) => {
  const paths = {
    search: <><circle cx="11" cy="11" r="7"/><path d="M21 21l-4.3-4.3"/></>,
    bell:   <><path d="M6 8a6 6 0 0 1 12 0c0 7 3 9 3 9H3s3-2 3-9"/><path d="M10 21a2 2 0 0 0 4 0"/></>,
    settings: <><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 1 1-4 0v-.09a1.65 1.65 0 0 0-1-1.51 1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 1 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 1 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 1 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z"/></>,
    grid:   <><rect x="3" y="3" width="7" height="7"/><rect x="14" y="3" width="7" height="7"/><rect x="3" y="14" width="7" height="7"/><rect x="14" y="14" width="7" height="7"/></>,
    sparkles: <><path d="M12 3v18M3 12h18M5 5l14 14M19 5L5 19"/></>,
    activity: <path d="M22 12h-4l-3 9L9 3l-3 9H2"/>,
    layers: <><polygon points="12 2 2 7 12 12 22 7 12 2"/><polyline points="2 17 12 22 22 17"/><polyline points="2 12 12 17 22 12"/></>,
    database: <><ellipse cx="12" cy="5" rx="9" ry="3"/><path d="M3 5v14a9 3 0 0 0 18 0V5"/><path d="M3 12a9 3 0 0 0 18 0"/></>,
    history: <><path d="M3 12a9 9 0 1 0 3-6.7L3 8"/><polyline points="3 3 3 8 8 8"/><polyline points="12 7 12 12 16 14"/></>,
    chevron: <polyline points="6 9 12 15 18 9"/>,
    chevronRight: <polyline points="9 18 15 12 9 6"/>,
    arrowRight: <><path d="M5 12h14"/><path d="M12 5l7 7-7 7"/></>,
    arrowUp: <><path d="M12 19V5"/><path d="M5 12l7-7 7 7"/></>,
    arrowDown: <><path d="M12 5v14"/><path d="M19 12l-7 7-7-7"/></>,
    send: <><path d="M22 2L11 13"/><path d="M22 2l-7 20-4-9-9-4 20-7z"/></>,
    check: <polyline points="20 6 9 17 4 12"/>,
    x: <><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></>,
    alert: <><path d="M10.29 3.86L1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z"/><line x1="12" y1="9" x2="12" y2="13"/><line x1="12" y1="17" x2="12.01" y2="17"/></>,
    external: <><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></>,
    user: <><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></>,
    info: <><circle cx="12" cy="12" r="10"/><line x1="12" y1="16" x2="12" y2="12"/><line x1="12" y1="8" x2="12.01" y2="8"/></>,
    filter: <polygon points="22 3 2 3 10 12.46 10 19 14 21 14 12.46 22 3"/>,
    download: <><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></>,
    refresh: <><polyline points="23 4 23 10 17 10"/><polyline points="1 20 1 14 7 14"/><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/></>,
    pulse: <polyline points="22 12 18 12 15 21 9 3 6 12 2 12"/>,
    eye: <><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></>,
    plug: <><path d="M9 2v6M15 2v6M6 8h12v4a6 6 0 0 1-12 0V8zM12 18v4"/></>,
  };
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none"
         stroke="currentColor" strokeWidth={stroke}
         strokeLinecap="round" strokeLinejoin="round" {...rest}>
      {paths[name] || null}
    </svg>
  );
};

/* -------------------- Pill -------------------- */
const Pill = ({ tone = "neutral", size = "md", dot, upper, children, style }) => (
  <span className={`pill ${tone} ${size === "sm" ? "sm" : ""} ${upper ? "upper" : ""}`} style={style}>
    {dot && <span className="dot"/>}
    {children}
  </span>
);

/* -------------------- Button -------------------- */
const Button = ({ variant = "secondary", size, leading, trailing, onClick, children, style }) => (
  <button className={`btn ${variant} ${size || ""}`} onClick={onClick} style={style}>
    {leading}
    {children}
    {trailing}
  </button>
);

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

/* -------------------- KPI Card -------------------- */
const Spark = ({ points, color = "#00E08F", height = 24 }) => {
  // points = [n1, n2, ...] 0..1 floats
  const W = 240, H = height;
  const step = W / (points.length - 1);
  const path = points.map((v, i) => `${i === 0 ? "M" : "L"}${i * step},${H - v * H}`).join(" ");
  const area = `M0,${H} L${path.replace(/^M/, "")} L${W},${H} Z`;
  const id = `spk-${color.replace("#","")}`;
  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none">
      <defs>
        <linearGradient id={id} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stopColor={color} stopOpacity="0.28"/>
          <stop offset="1" stopColor={color} stopOpacity="0"/>
        </linearGradient>
      </defs>
      <path d={area} fill={`url(#${id})`}/>
      <path d={path} fill="none" stroke={color} strokeWidth="1.5"/>
    </svg>
  );
};

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

/* -------------------- Chart: area + line -------------------- */
const AreaChart = ({ data, color = "#00E08F", height = 160, yMin = 0, yMax = 1, threshold }) => {
  const W = 600, H = height;
  const padTop = 12, padBot = 22, padL = 38, padR = 12;
  const innerW = W - padL - padR;
  const innerH = H - padTop - padBot;
  const step = innerW / (data.length - 1);
  const norm = (v) => padTop + innerH - ((v - yMin) / (yMax - yMin)) * innerH;
  const path = data.map((v, i) => `${i === 0 ? "M" : "L"}${padL + i * step},${norm(v)}`).join(" ");
  const area = `${path} L${padL + (data.length - 1) * step},${H - padBot} L${padL},${H - padBot} Z`;
  const id = `area-${color.replace("#","")}`;
  const yTicks = [yMin, yMin + (yMax - yMin) / 2, yMax];
  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" style={{ height }}>
      <defs>
        <linearGradient id={id} x1="0" x2="0" y1="0" y2="1">
          <stop offset="0" stopColor={color} stopOpacity="0.22"/>
          <stop offset="1" stopColor={color} stopOpacity="0"/>
        </linearGradient>
      </defs>
      {/* y-axis ticks */}
      {yTicks.map((t, i) => (
        <g key={i}>
          <line x1={padL} y1={norm(t)} x2={W - padR} y2={norm(t)} stroke="rgba(255,255,255,0.04)" strokeDasharray="2 4"/>
          <text x={padL - 6} y={norm(t) + 3} textAnchor="end" fontFamily="Geist Mono, monospace" fontSize="10" fill="#6B7280">{t.toFixed(2)}</text>
        </g>
      ))}
      {/* threshold line */}
      {threshold !== undefined && (
        <line x1={padL} y1={norm(threshold)} x2={W - padR} y2={norm(threshold)} stroke="#FFB020" strokeDasharray="4 4" strokeWidth="1"/>
      )}
      <path d={area} fill={`url(#${id})`}/>
      <path d={path} fill="none" stroke={color} strokeWidth="1.5"/>
      {/* last point dot */}
      <circle cx={padL + (data.length - 1) * step} cy={norm(data[data.length - 1])} r="3" fill={color}/>
      {/* x-axis labels (sparse) */}
      <text x={padL} y={H - 6} fontFamily="Geist Mono, monospace" fontSize="10" fill="#6B7280">−24h</text>
      <text x={W - padR} y={H - 6} textAnchor="end" fontFamily="Geist Mono, monospace" fontSize="10" fill="#6B7280">now</text>
    </svg>
  );
};

const MultiLineChart = ({ series, height = 160, yMin = 0, yMax = 1 }) => {
  // series = [{ label, color, data: [...] }]
  const W = 600, H = height;
  const padTop = 12, padBot = 22, padL = 38, padR = 12;
  const innerW = W - padL - padR;
  const innerH = H - padTop - padBot;
  const len = series[0].data.length;
  const step = innerW / (len - 1);
  const norm = (v) => padTop + innerH - ((v - yMin) / (yMax - yMin)) * innerH;
  const yTicks = [yMin, yMin + (yMax - yMin) / 2, yMax];
  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" style={{ height }}>
      {yTicks.map((t, i) => (
        <g key={i}>
          <line x1={padL} y1={norm(t)} x2={W - padR} y2={norm(t)} stroke="rgba(255,255,255,0.04)" strokeDasharray="2 4"/>
          <text x={padL - 6} y={norm(t) + 3} textAnchor="end" fontFamily="Geist Mono, monospace" fontSize="10" fill="#6B7280">{t.toFixed(2)}</text>
        </g>
      ))}
      {series.map((s, idx) => {
        const path = s.data.map((v, i) => `${i === 0 ? "M" : "L"}${padL + i * step},${norm(v)}`).join(" ");
        return <path key={idx} d={path} fill="none" stroke={s.color} strokeWidth="1.5"/>;
      })}
      <text x={padL} y={H - 6} fontFamily="Geist Mono, monospace" fontSize="10" fill="#6B7280">−24h</text>
      <text x={W - padR} y={H - 6} textAnchor="end" fontFamily="Geist Mono, monospace" fontSize="10" fill="#6B7280">now</text>
    </svg>
  );
};

const BarChart = ({ data, color = "#FFB020", height = 160, yMax }) => {
  const W = 600, H = height;
  const padTop = 12, padBot = 22, padL = 38, padR = 12;
  const innerW = W - padL - padR;
  const innerH = H - padTop - padBot;
  const max = yMax || Math.max(...data) * 1.2;
  const barW = innerW / data.length - 2;
  const yTicks = [0, max / 2, max];
  return (
    <svg viewBox={`0 0 ${W} ${H}`} preserveAspectRatio="none" style={{ height }}>
      {yTicks.map((t, i) => (
        <g key={i}>
          <line x1={padL} y1={padTop + innerH - (t / max) * innerH} x2={W - padR} y2={padTop + innerH - (t / max) * innerH} stroke="rgba(255,255,255,0.04)" strokeDasharray="2 4"/>
          <text x={padL - 6} y={padTop + innerH - (t / max) * innerH + 3} textAnchor="end" fontFamily="Geist Mono, monospace" fontSize="10" fill="#6B7280">{t.toFixed(1)}%</text>
        </g>
      ))}
      {data.map((v, i) => {
        const h = (v / max) * innerH;
        return <rect key={i} x={padL + i * (innerW / data.length) + 1} y={padTop + innerH - h} width={barW} height={h} fill={color} rx="1"/>;
      })}
      <text x={padL} y={H - 6} fontFamily="Geist Mono, monospace" fontSize="10" fill="#6B7280">−24h</text>
      <text x={W - padR} y={H - 6} textAnchor="end" fontFamily="Geist Mono, monospace" fontSize="10" fill="#6B7280">now</text>
    </svg>
  );
};

/* -------------------- Sidebar + Header -------------------- */
const Sidebar = ({ active, onNavigate, alerts = 0 }) => {
  const navItem = (key, icon, label, badge) => (
    <div className={`nav-item ${active === key ? "active" : ""}`} onClick={() => onNavigate(key)}>
      <Icon name={icon} size={16} className="ico"/>
      <span>{label}</span>
      {badge}
    </div>
  );
  return (
    <aside className="sidebar">
      <div className="group-label">Workspace</div>
      {navItem("dashboard", "grid", "Dashboard")}
      {navItem("query", "sparkles", "Query console")}
      {navItem("history", "history", "Query history", <span className="badge">2,481</span>)}

      <div className="group-label">LLMOps</div>
      {navItem("monitoring", "activity", "Monitoring", alerts > 0 ? <span className="badge alert">{alerts}</span> : null)}
      {navItem("traces", "layers", "Traces")}
      {navItem("evals", "pulse", "Evaluations")}

      <div className="group-label">Data</div>
      {navItem("sources", "database", "Sources", <span className="badge">9</span>)}
      {navItem("pipelines", "plug", "Pipelines")}

      <div className="group-label">Admin</div>
      {navItem("settings", "settings", "Settings")}

      <div className="footer">
        <div className="row"><span>API</span><span className="fg-signal">● 99.94%</span></div>
        <div className="row"><span>Kafka lag</span><span>4 ms</span></div>
        <div className="row"><span>Build</span><span>v2.4.0</span></div>
      </div>
    </aside>
  );
};

const Header = () => (
  <header className="header">
    <div className="brand">
      <svg width="22" height="22" viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="square">
        <path d="M2 18 L8 18 L10 10 L13 24 L16 14 L19 20 L22 18 L30 18"/>
      </svg>
      <span className="brand-name">MarketPulse</span>
      <span className="brand-ai">AI</span>
    </div>
    <span className="env-pill">● Prod</span>
    <span className="ws-status"><span className="dot"/>WS /query/stream</span>
    <div className="cmdk" style={{ marginLeft: 16 }}>
      <Icon name="search" size={14}/>
      <span>Search queries, traces, sources…</span>
      <span className="kbd">⌘K</span>
    </div>
    <div className="actions">
      <button className="icon-btn"><Icon name="refresh" size={16}/></button>
      <button className="icon-btn"><Icon name="bell" size={16}/><span className="bell-dot"/></button>
      <button className="icon-btn"><Icon name="settings" size={16}/></button>
      <div className="avatar">AK</div>
    </div>
  </header>
);

/* -------------------- App Shell -------------------- */
const AppShell = ({ active, onNavigate, alerts, children }) => (
  <div className="app">
    <Header/>
    <Sidebar active={active} onNavigate={onNavigate} alerts={alerts}/>
    <main className="main">
      <div className="main-inner">{children}</div>
    </main>
  </div>
);

const PageHead = ({ eyebrow, title, subtitle, actions }) => (
  <div className="page-head">
    <div className="title-block">
      {eyebrow && <span className="eyebrow">{eyebrow}</span>}
      <h1>{title}</h1>
      {subtitle && <span className="subtitle">{subtitle}</span>}
    </div>
    {actions && <div className="actions">{actions}</div>}
  </div>
);

Object.assign(window, {
  Icon, Pill, Button, Card, Kpi, Spark,
  AgentStep, AGENTS, SourceCard, renderAnswer,
  AreaChart, MultiLineChart, BarChart,
  Sidebar, Header, AppShell, PageHead,
});
