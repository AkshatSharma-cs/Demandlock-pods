import { OfflineBanner } from "./offline/OfflineBanner";
import { SyncStatus } from "./offline/SyncStatus";
import { useOnline } from "./offline/useOnline";
import { useSync } from "./offline/useSync";

export default function App() {
  const online = useOnline();
  const sync = useSync();
  return <main className="app-shell">
    <header><p className="eyebrow">DemandLock Pods</p><h1>Learn safely. Build evidence. Keep control offline.</h1><p className="intro">A teacher-run workspace for local demand and supervised practice.</p></header>
    {!online && <OfflineBanner />}
    <SyncStatus pendingCount={sync.pendingCount} needsReviewCount={sync.needsReviewCount} syncing={sync.syncing} onSync={sync.syncNow} />
    <section className="card"><h2>Welcome</h2><p>Your saved work remains available when the network is unavailable.</p><p className="muted">Use the voice tools and existing pod screens here as they are added.</p></section>
  </main>;
}
