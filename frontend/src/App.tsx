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
import { localizeDom } from "./i18n/localizeDom";

const navItems = [
  { id: "demand", label: "Demand desk", icon: "↗" },
  { id: "pods", label: "Learning pods", icon: "◈" },
  { id: "cohort", label: "Cohort review", icon: "◎" },
  { id: "outcomes", label: "Outcomes", icon: "↗" },
  { id: "impact", label: "Impact", icon: "▥" },
];

export default function App() {
  const online = useOnline();
  const sync = useSync();
  const t = useT();
  const [tab, setTab] = useState("demand");
  const [users, setUsers] = useState<Array<{id: string; name: string; role: string}>>([]);
  const [demoMode, setDemoMode] = useState(localStorage.getItem("demo_mode") === "true");
  const [language, setLanguage] = useState(localStorage.getItem("lang") || "en");
  const [actor, setActor] = useState(localStorage.getItem("demo_user_id") || "");
  const [user, setUser] = useState<{ id: string; name: string; role: string; student_id?: string } | null>(() => {
    try { return JSON.parse(localStorage.getItem("current_user") || "null"); } catch { return null; }
  });
  useEffect(() => {
    void fetch("/health").then(response => response.json()).then(health => {
      setDemoMode(Boolean(health.demo_mode)); localStorage.setItem("demo_mode", String(Boolean(health.demo_mode)));
      if (health.demo_mode) void apiFetch("/api/v1/demo/users").then(r => r.ok ? r.json() : []).then(setUsers);
    });
    const token = localStorage.getItem("auth_token");
    if (token) void apiFetch("/api/v1/me").then(response => response.ok ? response.json() : Promise.reject()).then(body => {
      const current = body.user; localStorage.setItem("current_user", JSON.stringify(current)); setUser(current);
    }).catch(() => { localStorage.removeItem("auth_token"); localStorage.removeItem("current_user"); setUser(null); });
    const expired = () => { localStorage.removeItem("auth_token"); localStorage.removeItem("current_user"); setUser(null); };
    window.addEventListener("auth-expired", expired);
    return () => window.removeEventListener("auth-expired", expired);
  }, []);
  useEffect(() => { if (!demoMode && !localStorage.getItem("auth_token")) setUser(null); }, [demoMode]);
  useEffect(() => {
    const root = document.getElementById("root");
    if (!root) return;
    const apply = () => localizeDom(root, language);
    apply();
    const observer = new MutationObserver(apply);
    observer.observe(root, { childList: true, subtree: true, characterData: true });
    return () => observer.disconnect();
  }, [language, tab, user?.id, demoMode]);
  const selected = users.find(user => user.id === actor);
  if (!demoMode && !user) return <main className="auth-shell"><div className="auth-brand"><span className="brand-mark">D</span><span>DemandLock <b>Pods</b></span></div><AuthScreen onLogin={next => { localStorage.setItem("lang", next.language); setLanguage(next.language); setUser(next); }} /></main>;
  const Page = tab === "pods" ? PodsPage : tab === "cohort" ? CohortPage : tab === "outcomes" ? OutcomesPage : tab === "impact" ? ImpactPage : DemandPage;
  const labels: Record<string, string> = { demand: t("demand"), pods: t("pods"), cohort: t("cohort"), outcomes: t("outcomes"), impact: t("impact") };
  return <main className="app-shell">
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark">D</span><span>DemandLock <b>Pods</b></span></div>
      <div className="workspace-label">Workspace</div>
      <nav className="side-nav">{navItems.map(item => <button className={tab === item.id ? "active" : ""} onClick={() => setTab(item.id)} key={item.id}><span className="nav-icon">{item.icon}</span>{labels[item.id]}</button>)}</nav>
      <div className="sidebar-footer"><span className="status-dot" /> <span>{online ? "Online & synced" : "Working offline"}</span></div>
    </aside>
    <section className="content">
      <header className="topbar">
        <div><p className="eyebrow">Community learning workspace</p><h1>{tab === "demand" ? "Good to see you, " : ""}{(demoMode ? selected?.name : user?.name) || "there"}</h1></div>
        <div className="toolbar">{demoMode && <select aria-label="Demo user" value={actor} onChange={event => { localStorage.setItem("demo_user_id", event.target.value); setActor(event.target.value); }}><option value="">Choose demo user</option>{users.map(user => <option value={user.id} key={user.id}>{user.name}</option>)}</select>}<span className="badge role-badge">{demoMode ? (selected?.role || "guest") : (user?.role || "user")}</span><span className="live-badge"><span className="status-dot" />{demoMode ? "Demo" : "Live"}</span><select aria-label="Language" value={language} onChange={event => { localStorage.setItem("lang", event.target.value); setLanguage(event.target.value); }}><option value="en">EN</option><option value="hi">हि</option><option value="ta">த</option></select><button className="avatar-button" aria-label="Log out" onClick={() => { localStorage.removeItem("auth_token"); localStorage.removeItem("current_user"); setUser(null); }}>{(demoMode ? selected?.name : user?.name)?.slice(0, 1).toUpperCase() || "U"}</button></div>
      </header>
      {!online && <OfflineBanner />}
      <SyncStatus pendingCount={sync.pendingCount} needsReviewCount={sync.needsReviewCount} syncing={sync.syncing} onSync={sync.syncNow} />
      <Page user={demoMode ? selected : user} />
    </section>
  </main>;
}
