/* Main App — nav state, click-through prototype */

const { useState: useStateApp } = React;

const App = () => {
  const [active, setActive] = useStateApp("dashboard");
  const [pendingQuery, setPendingQuery] = useStateApp(null);

  const askQuery = (q) => {
    setPendingQuery(q);
    setActive("query");
  };

  let screen = null;
  if (active === "dashboard")  screen = <Dashboard onAskQuery={askQuery}/>;
  else if (active === "query") screen = <QueryConsole initialQuery={pendingQuery} onClear={() => setPendingQuery(null)}/>;
  else if (active === "monitoring") screen = <Monitoring/>;
  else if (active === "sources")    screen = <DataSources/>;
  else if (active === "history")    screen = <QueryHistory onOpenTrace={() => setActive("query")}/>;
  else if (active === "settings")   screen = <Settings/>;
  else if (active === "traces")     screen = <QueryHistory/>;
  else if (active === "evals")      screen = <Monitoring/>;
  else if (active === "pipelines")  screen = <DataSources/>;

  return (
    <AppShell active={active} onNavigate={setActive} alerts={2}>
      {screen}
    </AppShell>
  );
};

const root = ReactDOM.createRoot(document.getElementById("root"));
root.render(<App/>);
