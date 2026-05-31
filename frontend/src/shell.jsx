/* App chrome — Sidebar (live API status footer), Header, AppShell, PageHead.
   Depends on primitives (Icon). Exported to window. */

/* -------------------- Sidebar + Header -------------------- */
const Sidebar = ({ active, onNavigate, alerts = 0 }) => {
  const [health, setHealth] = React.useState(null);
  const [reachable, setReachable] = React.useState(null); // null = unknown, bool once known

  React.useEffect(() => {
    let alive = true;
    window.MP.health().then((h) => {
      if (!alive) return;
      setHealth(h);
      setReachable(!!h);
    });
    return () => { alive = false; };
  }, []);

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
      {navItem("history", "history", "Query history")}

      <div className="group-label">LLMOps</div>
      {navItem("monitoring", "activity", "Monitoring", alerts > 0 ? <span className="badge alert">{alerts}</span> : null)}

      <div className="group-label">Data</div>
      {navItem("sources", "database", "Sources")}

      <div className="group-label">Admin</div>
      {navItem("settings", "settings", "Settings")}

      <div className="footer">
        <div className="row">
          <span>API</span>
          <span className={reachable ? "fg-signal" : reachable === false ? "fg-loss" : "fg-tertiary"}>
            {reachable == null ? "…" : reachable ? "● online" : "● offline"}
          </span>
        </div>
        <div className="row"><span>Model</span><span className="fg-tertiary">{health ? health.model : "—"}</span></div>
        <div className="row"><span>Version</span><span>{health ? `v${health.version}` : "—"}</span></div>
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

Object.assign(window, { Sidebar, Header, AppShell, PageHead });
