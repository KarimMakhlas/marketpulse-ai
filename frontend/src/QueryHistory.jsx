/* Query History screen — wired to GET /queries (authenticated).
 *
 * Shows only fields the backend's query_log actually stores: query text,
 * Self-RAG doc_grade, timestamp, and number of sources kept. Latency, cost,
 * confidence, and trace IDs are not persisted, so they are not shown (rather
 * than fabricated). Requires a token; prompts to sign in otherwise. */

const { useState: useStateH, useEffect: useEffectH } = React;

const fmtTs = (iso) => {
  if (!iso) return "—";
  const d = new Date(iso);
  return isNaN(d) ? String(iso).slice(0, 16) : d.toISOString().slice(0, 16).replace("T", " ");
};

const QueryHistory = ({ onOpenTrace }) => {
  const [state, setState] = useStateH("loading"); // loading | ok | auth | empty | error
  const [rows, setRows] = useStateH([]);

  const load = () => {
    setState("loading");
    window.MP.queries(100).then((res) => {
      if (!res.ok) {
        setState(res.error === "auth" ? "auth" : "error");
        setRows([]);
        return;
      }
      setRows(res.rows);
      setState(res.rows.length ? "ok" : "empty");
    });
  };

  useEffectH(() => { load(); }, []);

  return (
    <>
      <PageHead
        eyebrow="Workspace"
        title="Query history"
        subtitle="Logged queries from the Postgres audit store · newest first"
        actions={<Button leading={<Icon name="refresh" size={14}/>} onClick={load}>Refresh</Button>}
      />

      <Card
        title="Recent queries"
        sub={state === "ok" ? `${rows.length} shown` : "audit log"}
        right={<Pill tone="ai" size="sm" upper>query_log</Pill>}
      >
        {state === "loading" && (
          <div className="fg-muted" style={{ padding: "16px 0", fontSize: 13 }}>Loading…</div>
        )}

        {state === "auth" && (
          <EmptyState
            icon="user"
            title="Sign in to view history"
            line="The query log is behind authentication. Sign in from the Query Console, then refresh."
          />
        )}

        {state === "error" && (
          <EmptyState
            icon="alert"
            title="Could not load history"
            line="The API or Postgres audit store is unavailable. Start it with `make stack-up`, then refresh."
          />
        )}

        {state === "empty" && (
          <EmptyState
            icon="info"
            title="No queries logged yet"
            line="Run a query from the Console. Each answered query is recorded here (requires DATABASE_URL)."
          />
        )}

        {state === "ok" && (
          <div style={{ overflow: "auto" }}>
            <table className="tbl">
              <thead><tr>
                <th>Time (UTC)</th>
                <th>Query</th>
                <th>Doc grade</th>
                <th>Sources</th>
              </tr></thead>
              <tbody>
                {rows.map((r, i) => (
                  <tr key={i} onClick={() => onOpenTrace && onOpenTrace()}>
                    <td className="num fg-tertiary">{fmtTs(r.queried_at)}</td>
                    <td style={{ maxWidth: 460 }}>{r.query}</td>
                    <td>
                      <Pill tone={r.doc_grade === "sufficient" ? "signal" : r.doc_grade === "insufficient" ? "caution" : "neutral"} size="sm">
                        {r.doc_grade || "—"}
                      </Pill>
                    </td>
                    <td className="num fg-info">{r.sources_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
    </>
  );
};

window.QueryHistory = QueryHistory;
