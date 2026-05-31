/* Data Sources screen — wired to GET /sources.
 *
 * Lists exactly the sources the ingestion pipeline pulls from, with the
 * credibility weight applied at retrieval rerank. Per-source event counts and
 * freshness are not tracked by the API, so they are not shown. */

const { useState: useStateDS, useEffect: useEffectDS } = React;

const KIND_LABEL = { rss: "RSS feed", edgar: "SEC EDGAR", newsapi: "NewsAPI" };

const DataSources = () => {
  const [state, setState] = useStateDS("loading"); // loading | ok | error
  const [sources, setSources] = useStateDS([]);

  const load = () => {
    setState("loading");
    window.MP.sources().then((rows) => {
      if (!rows) { setState("error"); setSources([]); return; }
      setSources(rows);
      setState("ok");
    });
  };

  useEffectDS(() => { load(); }, []);

  return (
    <>
      <PageHead
        eyebrow="Data"
        title="Ingestion sources"
        subtitle="Feeds the pipeline pulls from · weighted by credibility at retrieval rerank"
        actions={<Button leading={<Icon name="refresh" size={14}/>} onClick={load}>Refresh</Button>}
      />

      <Card
        title="Sources"
        sub={state === "ok" ? `${sources.length} configured` : "ingestion"}
        right={<Pill tone="ai" size="sm" upper>credibility-weighted</Pill>}
      >
        {state === "loading" && (
          <div className="fg-muted" style={{ padding: "16px 0", fontSize: 13 }}>Loading…</div>
        )}
        {state === "error" && (
          <EmptyState
            icon="alert"
            title="Could not load sources"
            line="The API is unavailable. Start it with `make api`, then refresh."
          />
        )}
        {state === "ok" && (
          <div style={{ display: "grid", gridTemplateColumns: "repeat(3, 1fr)", gap: 12 }}>
            {sources.map((s) => <SourceTile key={s.id} source={s}/>)}
          </div>
        )}
      </Card>
    </>
  );
};

const SourceTile = ({ source }) => {
  const cred = source.credibility;
  const credColor =
    cred >= 0.85 ? "var(--accent-signal)" :
    cred >= 0.55 ? "var(--accent-caution)" :
                   "var(--accent-loss)";
  return (
    <div className="source-tile">
      <div className="st-top">
        <span className="st-logo" style={{
          display: "inline-flex", alignItems: "center", justifyContent: "center",
          width: 28, height: 28, borderRadius: 6,
          background: "var(--bg-inset)", border: "1px solid var(--border-subtle)",
          fontFamily: "var(--font-mono)", fontSize: 12, fontWeight: 600, color: "var(--fg-secondary)",
        }}>{source.name.charAt(0)}</span>
        <span style={{ marginLeft: "auto" }}>
          <Pill tone="info" size="sm">{KIND_LABEL[source.kind] || source.kind}</Pill>
        </span>
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 8, marginTop: 4 }}>
        <span style={{ fontSize: 15, fontWeight: 500 }}>{source.name}</span>
        <span className="mono-sm fg-tertiary" style={{ fontSize: 11 }}>· {source.id}</span>
      </div>
      <div className="st-grid" style={{ marginTop: 10 }}>
        <div>
          <span className="lbl">Credibility</span>
          <span className="val" style={{ color: credColor }}>{cred.toFixed(2)}</span>
        </div>
        <div>
          <span className="lbl">Retrieval weight</span>
          <span className="val" style={{ fontSize: 12 }}>{cred.toFixed(2)}×</span>
        </div>
      </div>
    </div>
  );
};

window.DataSources = DataSources;
