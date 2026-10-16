import { apiFetch } from "./api";
import { getDB } from "./db";
import { listPending, markStatus, remove } from "./outbox";
let active = false;
export async function syncNow() {
  if (active || !navigator.onLine) return; active = true;
  try {
    const pending = await listPending();
    const db = await getDB();
    const audio = await db.getAll("pending_audio");
    if (pending.length) try {
      const response = await apiFetch("/api/v1/sync/push", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ops: pending }) });
      if (response.ok) for (const result of (await response.json()).results as Array<{ client_op_id: string; status: string; reason?: string }>) {
        if (result.status === "applied" || result.status === "duplicate") await remove(result.client_op_id);
        else if (result.status === "conflict") await markStatus(result.client_op_id, "needs_review", result.reason);
        else if (result.status === "rejected") await markStatus(result.client_op_id, "failed", result.reason);
      }
    } catch { /* retain pending */ }
    for (const item of audio) try {
      const form = new FormData(); form.append("file", item.blob, `${item.ticket_id}.audio`);
      if ((await apiFetch(`/api/v1/demand-tickets/${item.ticket_id}/audio`, { method: "POST", body: form })).ok) await db.delete("pending_audio", item.ticket_id);
    } catch { /* retain audio */ }
    try {
      const actor = localStorage.getItem("demo_user_id");
      const suffix = actor ? `?as=${encodeURIComponent(actor)}` : "";
      const pods = await apiFetch(`/api/v1/pods${suffix}`);
      if (pods.ok) for (const pod of await pods.json()) await db.put("cached_pods", pod, pod.id);
      const modules = await apiFetch(`/api/v1/modules${suffix}`);
      if (modules.ok) for (const module of await modules.json()) await db.put("cached_modules", module, module.id);
      await db.put("sync_metadata", new Date().toISOString(), "lastSyncedAt");
    } catch { /* retain local state when refresh is unavailable */ }
  } finally { active = false; }
}
