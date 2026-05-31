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

  return (
    <AppShell active={active} onNavigate={setActive} alerts={0}>
      {screen}
    </AppShell>
  );
};

/* The UI kit + screens load as separate Babel-CDN scripts that compile
   asynchronously; App.jsx is last in document order but its render can still
   fire before every dependency has registered on `window`. Wait until the kit
   and all screens are defined before the first render so there is no transient
   "element type is invalid" flash. */
const REQUIRED = ["AppShell", "Dashboard", "QueryConsole", "Monitoring", "DataSources", "QueryHistory", "Settings"];
const root = ReactDOM.createRoot(document.getElementById("root"));

function mount() {
  if (REQUIRED.every((name) => typeof window[name] === "function")) {
    root.render(<App/>);
  } else {
    setTimeout(mount, 20);
  }
}
mount();
