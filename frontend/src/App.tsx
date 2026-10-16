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

export default function App() {
  const online = useOnline();
  const sync = useSync();
  const t = useT();
  const [tab, setTab] = useState("demand");
  const [users, setUsers] = useState<Array<{id: string; name: string; role: string}>>([]);
  const [actor, setActor] = useState(localStorage.getItem("demo_user_id") || "");
  useEffect(() => { void apiFetch("/api/v1/demo/users").then(r => r.ok ? r.json() : []).then(setUsers); }, []);
  const selected = users.find(user => user.id === actor);
  const Page = tab === "pods" ? PodsPage : tab === "cohort" ? CohortPage : tab === "outcomes" ? OutcomesPage : tab === "impact" ? ImpactPage : DemandPage;
  return <main className="app-shell">
    <header><p className="eyebrow">{t("appName")}</p><h1>Learn safely. Build evidence. Keep control offline.</h1><p className="intro">A teacher-run workspace for local demand and supervised practice.</p>
      <div className="toolbar"><select aria-label="Demo user" value={actor} onChange={event => { localStorage.setItem("demo_user_id", event.target.value); setActor(event.target.value); }}><option value="">Choose demo user</option>{users.map(user => <option value={user.id} key={user.id}>{user.name}</option>)}</select><span className="badge">{selected?.role || "guest"}</span><span className="badge">{t("simulated")}</span><select aria-label="Language" defaultValue={localStorage.getItem("lang") || "en"} onChange={event => { localStorage.setItem("lang", event.target.value); window.location.reload(); }}><option value="en">English</option><option value="hi">हिन्दी</option><option value="ta">தமிழ்</option></select></div>
    </header>
    {!online && <OfflineBanner />}
    <SyncStatus pendingCount={sync.pendingCount} needsReviewCount={sync.needsReviewCount} syncing={sync.syncing} onSync={sync.syncNow} />
    <nav className="tabs">{(["demand", "pods", "cohort", "outcomes", "impact"] as const).map(name => <button className={tab === name ? "active" : ""} onClick={() => setTab(name)} key={name}>{t(name)}</button>)}</nav>
    <Page />
  </main>;
}
