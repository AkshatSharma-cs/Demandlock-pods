import { useCallback, useEffect, useRef, useState } from "react";
import { counts, listPending } from "./outbox";
import { syncNow as runSync } from "./sync";
export function useSync() {
  const [pendingCount, setPending] = useState(0), [needsReviewCount, setNeedsReview] = useState(0), [syncing, setSyncing] = useState(false), [lastSyncedAt, setLast] = useState<string>();
  const running = useRef(false);
  const refresh = useCallback(async () => { const value = await counts(); setPending(value.pending); setNeedsReview(value.needsReview); }, []);
  const syncNow = useCallback(async () => {
    if (running.current) return;
    running.current = true;
    setSyncing(true);
    try { await runSync(); await refresh(); setLast(new Date().toISOString()); }
    finally { running.current = false; setSyncing(false); }
  }, [refresh]);
  useEffect(() => {
    void refresh(); void syncNow();
    const online = () => void syncNow();
    const visible = () => { if (document.visibilityState === "visible") void syncNow(); };
    window.addEventListener("online", online); document.addEventListener("visibilitychange", visible);
    const timer = window.setInterval(async () => { if ((await listPending()).length) void syncNow(); }, 30000);
    return () => { window.removeEventListener("online", online); document.removeEventListener("visibilitychange", visible); window.clearInterval(timer); };
  }, [refresh, syncNow]);
  return { pendingCount, needsReviewCount, syncing, lastSyncedAt, syncNow };
}
