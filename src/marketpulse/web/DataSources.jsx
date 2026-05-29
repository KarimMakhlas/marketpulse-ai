/* Data Sources screen */

const SOURCES_LIST = [
  { id: "reuters",   name: "Reuters",          logo: "../../assets/icons/source-reuters.svg",   status: "active",  cred: 0.95, last: "2 min ago",  today: 4230, kafka: "raw.articles" },
  { id: "bloomberg", name: "Bloomberg",        logo: "../../assets/icons/source-bloomberg.svg", status: "active",  cred: 0.94, last: "1 min ago",  today: 3940, kafka: "raw.articles" },
  { id: "ft",        name: "Financial Times",  logo: "../../assets/icons/source-ft.svg",        status: "active",  cred: 0.93, last: "4 min ago",  today: 1820, kafka: "raw.articles" },
  { id: "wsj",       name: "Wall Street Journal", logo: "../../assets/icons/source-wsj.svg",    status: "active",  cred: 0.92, last: "3 min ago",  today: 1480, kafka: "raw.articles" },
  { id: "yahoo",     name: "Yahoo Finance",    logo: "../../assets/icons/source-yahoo.svg",     status: "active",  cred: 0.78, last: "1 min ago",  today: 9210, kafka: "raw.articles" },
  { id: "sec",       name: "SEC EDGAR",        logo: "../../assets/icons/source-sec.svg",       status: "active",  cred: 0.99, last: "8 min ago",  today: 320,  kafka: "raw.filings"  },
  { id: "reddit",    name: "Reddit",           logo: "../../assets/icons/source-reddit.svg",    status: "degraded",cred: 0.38, last: "12 min ago", today: 18420, kafka: "raw.social" },
  { id: "x",         name: "X / Twitter",      logo: "../../assets/icons/source-x.svg",         status: "active",  cred: 0.35, last: "<1 min ago", today: 22810, kafka: "raw.social" },
  { id: "newsapi",   name: "NewsAPI",          logo: "../../assets/icons/source-newsapi.svg",   status: "active",  cred: 0.71, last: "2 min ago",  today: 2180, kafka: "raw.articles" },
];

const DataSources = () => {
  return (
    <>
      <PageHead
        eyebrow="Data"
        title="Ingestion sources"
        subtitle="9 sources · 64,430 articles ingested today · weighted by credibility in retrieval"
        actions={
          <>
            <Button leading={<Icon name="refresh" size={14}/>}>Resync all</Button>
            <Button variant="ai" leading={<Icon name="plug" size={14}/>}>Connect source</Button>
          </>
        }
      />

      {/* Kafka pipeline hero */}
      <Card title="Streaming pipeline" sub="Kafka topics → vector store"
            right={<><Pill tone="signal" dot size="sm">Streaming</Pill><span>4 ms lag</span></>}>
        <PipelineViz/>
      </Card>

      <div style={{ height: 20 }}/>

      {/* Source cards grid */}
      <Card title="Sources" sub="ingestion + credibility per source"
            right={<>
              <span>active <span className="fg-signal">8</span></span>
              <span>degraded <span className="fg-caution">1</span></span>
              <span>total events 64,430</span>
            </>}>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
          {SOURCES_LIST.map(s => <SourceTile key={s.id} source={s}/>)}
        </div>
      </Card>
    </>
  );
};

const SourceTile = ({ source }) => {
  const toneByStatus = { active: "signal", degraded: "caution", offline: "loss" };
  const tone = toneByStatus[source.status];
  return (
    <div className="source-tile">
      <div className="st-top">
        <span className="st-logo"><img src={source.logo} alt={source.name}/></span>
        <span style={{ marginLeft: "auto" }}><Pill tone={tone} size="sm" dot>{source.status}</Pill></span>
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
        <span style={{ fontSize: 15, fontWeight: 500 }}>{source.name}</span>
        <span className="mono-sm fg-tertiary" style={{ fontSize: 11 }}>· {source.kafka}</span>
      </div>
      <div className="st-grid">
        <div>
          <span className="lbl">Credibility</span>
          <span className="val" style={{
            color: source.cred >= 0.85 ? "var(--accent-signal)" :
                   source.cred >= 0.55 ? "var(--accent-caution)" :
                                          "var(--accent-loss)"
          }}>{source.cred.toFixed(2)}</span>
        </div>
        <div>
          <span className="lbl">Events today</span>
          <span className="val">{source.today.toLocaleString()}</span>
        </div>
        <div>
          <span className="lbl">Last ingestion</span>
          <span className="val" style={{ fontSize: 12, color: "var(--fg-secondary)" }}>{source.last}</span>
        </div>
        <div>
          <span className="lbl">Weight in retrieval</span>
          <span className="val" style={{ fontSize: 12 }}>{(source.cred * 1.0).toFixed(2)}×</span>
        </div>
      </div>
      {/* mini rate chart */}
      <svg viewBox="0 0 240 28" preserveAspectRatio="none" style={{ width: "100%", height: 28 }}>
        <polyline
          points={Array.from({length: 24}, (_, i) => `${i * 10},${22 - Math.sin(i / 2 + source.id.length) * 6 - Math.random() * 4}`).join(" ")}
          fill="none"
          stroke={tone === "signal" ? "#00E08F" : tone === "caution" ? "#FFB020" : "#FF4D6D"}
          strokeWidth="1.3"
          opacity="0.7"
        />
      </svg>
    </div>
  );
};

const PipelineViz = () => {
  const Node = ({ name, count, rate, sink, warning }) => (
    <div style={{
      flex: 1,
      background: sink ? "var(--accent-info-bg)" : "var(--bg-inset)",
      border: `1px solid ${sink ? "var(--accent-info-ring)" : warning ? "var(--accent-caution-ring)" : "var(--border-subtle)"}`,
      borderRadius: 6, padding: "12px 14px",
      display: "flex", flexDirection: "column", gap: 4,
      fontFamily: "var(--font-mono)",
      position: "relative",
    }}>
      <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
        <span style={{ width: 6, height: 6, borderRadius: 999, background: warning ? "var(--accent-caution)" : "var(--accent-signal)" }}/>
        <span style={{ fontSize: 11, color: sink ? "var(--accent-info)" : warning ? "var(--accent-caution)" : "var(--fg-primary)", fontWeight: 600 }}>{name}</span>
      </div>
      <span style={{ fontSize: 20, color: "var(--fg-primary)", fontVariantNumeric: "tabular-nums", fontWeight: 500 }}>{count}</span>
      {rate && <span style={{ fontSize: 10, color: warning ? "var(--accent-caution)" : "var(--fg-tertiary)" }}>{rate}</span>}
    </div>
  );
  const Arrow = ({ rate }) => (
    <div style={{ width: 64, color: "var(--accent-info)", display: "flex", flexDirection: "column", alignItems: "center", gap: 2, padding: "0 4px" }}>
      <Icon name="arrowRight" size={14}/>
      <span className="mono-sm fg-tertiary" style={{ fontSize: 9 }}>{rate}</span>
    </div>
  );
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 0 }}>
      <Node name="ingest" count="9 sources" rate="↑ 137 evt/s"/>
      <Arrow rate="filter"/>
      <Node name="raw.articles" count="52,430" rate="↑ 47/s"/>
      <Arrow rate="dedup · normalize"/>
      <Node name="clean.articles" count="52,408" rate="↑ 47/s · 0.04% drop"/>
      <Arrow rate="embed · text-embed-3"/>
      <Node name="embedded.articles" count="52,401" rate="↑ 46/s"/>
      <Arrow rate="upsert"/>
      <Node name="ChromaDB" count="52,401" sink/>
    </div>
  );
};

window.DataSources = DataSources;
