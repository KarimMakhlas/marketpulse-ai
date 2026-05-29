/* Query History screen */

const HISTORY_ROWS = [
  { date: "2026-04-12 14:32", query: "Did NVIDIA beat earnings expectations?", conf: 0.86, halluc: "no",  lat: "1.8 s", trace: "tr_8f3a91d2", model: "haiku-4-5", sources: 5 },
  { date: "2026-04-12 13:11", query: "What changed in Apple's 10-Q filing?",   conf: 0.74, halluc: "no",  lat: "2.4 s", trace: "tr_44e2c0a1", model: "haiku-4-5", sources: 7 },
  { date: "2026-04-12 11:48", query: "Risk factors in TSLA delivery miss?",    conf: 0.91, halluc: "low", lat: "1.4 s", trace: "tr_91c0f3b2", model: "haiku-4-5", sources: 4 },
  { date: "2026-04-12 10:14", query: "Summarize Fed minutes from this week",    conf: 0.82, halluc: "no",  lat: "2.1 s", trace: "tr_22d8a47e", model: "haiku-4-5", sources: 6 },
  { date: "2026-04-12 09:48", query: "Q1 earnings beat/miss for MSFT, GOOGL, META", conf: 0.88, halluc: "no", lat: "2.8 s", trace: "tr_77e3b91c", model: "haiku-4-5", sources: 9 },
  { date: "2026-04-12 09:22", query: "How are analysts revising AMZN price targets?", conf: 0.79, halluc: "no", lat: "1.9 s", trace: "tr_55a2d04f", model: "haiku-4-5", sources: 5 },
  { date: "2026-04-12 08:55", query: "What did Powell signal about rate path?",  conf: 0.69, halluc: "low",  lat: "2.6 s", trace: "tr_19c4f8a3", model: "haiku-4-5", sources: 3 },
  { date: "2026-04-12 08:31", query: "Recent M&A activity in semis",             conf: 0.84, halluc: "no",   lat: "2.0 s", trace: "tr_aa18b772", model: "haiku-4-5", sources: 6 },
  { date: "2026-04-12 08:02", query: "Why did Tencent ADR gap up overnight?",     conf: 0.62, halluc: "high",lat: "3.1 s", trace: "tr_b3e9c12d", model: "haiku-4-5", sources: 2, flag: true },
  { date: "2026-04-12 07:44", query: "Crude inventory data — Cushing storage",    conf: 0.93, halluc: "no",   lat: "1.6 s", trace: "tr_e7f2d8b4", model: "haiku-4-5", sources: 8 },
  { date: "2026-04-11 18:12", query: "Earnings calls flagged for guidance cuts",  conf: 0.81, halluc: "no",   lat: "2.3 s", trace: "tr_4c19a8d2", model: "haiku-4-5", sources: 7 },
  { date: "2026-04-11 17:36", query: "Compare COIN and HOOD Q4 trading volumes",  conf: 0.77, halluc: "no",   lat: "2.0 s", trace: "tr_6f8e44a1", model: "haiku-4-5", sources: 5 },
];

const QueryHistory = ({ onOpenTrace }) => {
  return (
    <>
      <PageHead
        eyebrow="Workspace"
        title="Query history"
        subtitle="2,481 queries · last 24 h · click any row to inspect the full trace"
        actions={
          <>
            <div className="input" style={{ width: 280, height: 32 }}>
              <Icon name="search" size={12} className="fg-tertiary"/>
              <input placeholder="Filter by query, trace ID, or source…" defaultValue=""/>
            </div>
            <div className="input" style={{ width: 160, height: 32 }}>
              <Icon name="filter" size={12} className="fg-tertiary"/>
              <span className="mono-sm">last 24 h</span>
              <Icon name="chevron" size={10} className="fg-tertiary"/>
            </div>
            <Button leading={<Icon name="download" size={14}/>}>Export CSV</Button>
          </>
        }
      />

      {/* Summary strip */}
      <div className="kpi-grid" style={{ gridTemplateColumns: "repeat(5, 1fr)", marginBottom: 20 }}>
        <Kpi label="Total queries" value="2,481" delta="↑ +18% vs. 24h" deltaTone="signal"/>
        <Kpi label="Avg confidence" value="0.83" delta="↑ +0.02" deltaTone="signal"/>
        <Kpi label="Flagged" value="14" delta="0.6% of total" deltaTone="caution"/>
        <Kpi label="Avg latency" value="2.1" unit="s" delta="↑ +0.3 s" deltaTone="caution"/>
        <Kpi label="Total cost" value="$10.42" delta="claude-haiku-4-5" deltaTone="ai"/>
      </div>

      <Card title="Recent queries" sub={`${HISTORY_ROWS.length} of 2,481 shown`}
            right={<>
              <Pill tone="ai" size="sm" upper>claude-haiku-4-5</Pill>
              <span>sorted by time, descending</span>
            </>}>
        <div style={{ overflow: "auto" }}>
          <table className="tbl">
            <thead><tr>
              <th>Date</th>
              <th>Query</th>
              <th>Conf</th>
              <th>Halluc</th>
              <th>Latency</th>
              <th>Sources</th>
              <th>Trace</th>
              <th></th>
            </tr></thead>
            <tbody>
              {HISTORY_ROWS.map((r, i) => (
                <tr key={i} onClick={() => onOpenTrace && onOpenTrace(r.trace)}>
                  <td className="num fg-tertiary">{r.date}</td>
                  <td style={{ maxWidth: 380 }}>
                    {r.flag && <span style={{ marginRight: 8, color: "var(--accent-loss)" }}>●</span>}
                    {r.query}
                  </td>
                  <td className={`num fg-${r.conf >= 0.80 ? "signal" : r.conf >= 0.65 ? "caution" : "loss"}`}>{r.conf.toFixed(2)}</td>
                  <td>
                    <Pill tone={r.halluc === "no" ? "signal" : r.halluc === "low" ? "caution" : "loss"} size="sm">
                      {r.halluc}
                    </Pill>
                  </td>
                  <td className="num">{r.lat}</td>
                  <td className="num fg-info">{r.sources}</td>
                  <td className="num fg-ai">{r.trace}</td>
                  <td style={{ textAlign: "right" }}>
                    <Icon name="chevronRight" size={12} className="fg-tertiary"/>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </>
  );
};

window.QueryHistory = QueryHistory;
