import { OfflineBanner } from "./offline/OfflineBanner";
import { SyncStatus } from "./offline/SyncStatus";
import { useOnline } from "./offline/useOnline";
import { useSync } from "./offline/useSync";
import { useEffect, useState } from "react";
import { apiFetch } from "./offline/api";
import { DemandPage } from "./pages/DemandPage";
import { PodsPage } from "./pages/PodsPage";
import { CohortPage } from "./pages/CohortPage";
import { OutcomesPage } from "./pages/OutcomesPage";
import { ImpactPage } from "./pages/ImpactPage";
import { useT } from "./i18n/useT";
import { AuthScreen } from "./auth/AuthScreen";

export default function App() {
  const online = useOnline();
  const sync = useSync();
  const t = useT();
  const [tab, setTab] = useState("demand");
  const [users, setUsers] = useState<Array<{id: string; name: string; role: string}>>([]);
  const [demoMode, setDemoMode] = useState(localStorage.getItem("demo_mode") === "true");
  const [actor, setActor] = useState(localStorage.getItem("demo_user_id") || "");
  const [user, setUser] = useState<{ id: string; name: string; role: string } | null>(null);
  useEffect(() => {
    void fetch("/health").then(response => response.json()).then(health => {
      setDemoMode(Boolean(health.demo_mode)); localStorage.setItem("demo_mode", String(Boolean(health.demo_mode)));
      if (health.demo_mode) void apiFetch("/api/v1/demo/users").then(r => r.ok ? r.json() : []).then(setUsers);
    });
    const expired = () => { localStorage.removeItem("auth_token"); setUser(null); };
    window.addEventListener("auth-expired", expired);
    return () => window.removeEventListener("auth-expired", expired);
  }, []);
  useEffect(() => { if (!demoMode && !localStorage.getItem("auth_token")) setUser(null); }, [demoMode]);
  const selected = users.find(user => user.id === actor);
  if (!demoMode && !user && !localStorage.getItem("auth_token")) return <main className="app-shell"><p className="eyebrow">{t("appName")}</p><AuthScreen onLogin={setUser} /></main>;
  const Page = tab === "pods" ? PodsPage : tab === "cohort" ? CohortPage : tab === "outcomes" ? OutcomesPage : tab === "impact" ? ImpactPage : DemandPage;
  return <main className="app-shell">
    <header><p className="eyebrow">{t("appName")}</p><h1>Learn safely. Build evidence. Keep control offline.</h1><p className="intro">A teacher-run workspace for local demand and supervised practice.</p>
      <div className="toolbar">{demoMode && <select aria-label="Demo user" value={actor} onChange={event => { localStorage.setItem("demo_user_id", event.target.value); setActor(event.target.value); }}><option value="">Choose demo user</option>{users.map(user => <option value={user.id} key={user.id}>{user.name}</option>)}</select>}<span className="badge">{demoMode ? (selected?.role || "guest") : (user?.role || "user")}</span><span className="badge">{demoMode ? "DEMO DATA - SIMULATED" : "LIVE"}</span>{!demoMode && <button className="link-button" onClick={() => { localStorage.removeItem("auth_token"); setUser(null); }}>Logout</button>}<select aria-label="Language" defaultValue={localStorage.getItem("lang") || "en"} onChange={event => { localStorage.setItem("lang", event.target.value); window.location.reload(); }}><option value="en">English</option><option value="hi">हिन्दी</option><option value="ta">தமிழ்</option></select></div>
    </header>
    {!online && <OfflineBanner />}
    <SyncStatus pendingCount={sync.pendingCount} needsReviewCount={sync.needsReviewCount} syncing={sync.syncing} onSync={sync.syncNow} />
    <nav className="tabs">{(["demand", "pods", "cohort", "outcomes", "impact"] as const).map(name => <button className={tab === name ? "active" : ""} onClick={() => setTab(name)} key={name}>{t(name)}</button>)}</nav>
    <Page />
  </main>;
}
