import { enqueue } from "./outbox";
const actorHeader = () => { const id = localStorage.getItem("demo_user_id"); return id ? { "X-Demo-User-Id": id } : {}; };
export async function apiFetch(input: RequestInfo | URL, init: RequestInit = {}) {
  const headers = new Headers(init.headers);
  Object.entries(actorHeader()).forEach(([key, value]) => headers.set(key, value));
  const controller = new AbortController();
  const timer = window.setTimeout(() => controller.abort(), 10000);
  try { return await fetch(input, { ...init, headers, signal: init.signal ?? controller.signal }); }
  finally { window.clearTimeout(timer); }
}
export async function queueOrSend(action: string, entity_type: string, entity_id: string, payload: Record<string, unknown>, base_version?: number) {
  const operation = { client_op_id: crypto.randomUUID(), entity_type, action, entity_id, base_version, payload, client_occurred_at: new Date().toISOString() };
  if (navigator.onLine) {
    try {
      const paths: Record<string, string> = { demand_ticket: "demand-tickets", submission: `tasks/${String(payload.task_id ?? "")}/submissions`, outcome: "outcomes" };
      const response = await apiFetch(`/api/v1/${paths[entity_type] ?? `${entity_type}s`}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) });
      if (response.ok) return { queued: false, id: entity_id, result: await response.json() };
      if (response.status < 400 || response.status >= 500) await enqueue(operation);
      return { queued: false, id: entity_id, error: response.status };
    } catch { /* durable fallback */ }
  }
  await enqueue(operation); return { queued: true, id: entity_id };
}
