import { enqueue } from "./outbox";
const actorHeader = () => { const id = localStorage.getItem("demo_user_id"); return id ? { "X-Demo-User-Id": id } : {}; };
export async function apiFetch(input: RequestInfo | URL, init: RequestInit = {}) { const headers = new Headers(init.headers); Object.entries(actorHeader()).forEach(([key, value]) => headers.set(key, value)); return fetch(input, { ...init, headers }); }
export async function queueOrSend(action: string, entity_type: string, entity_id: string, payload: Record<string, unknown>, base_version?: number) {
  const operation = { client_op_id: crypto.randomUUID(), entity_type, action, entity_id, base_version, payload, client_occurred_at: new Date().toISOString() };
  if (navigator.onLine) { try { const path = entity_type === "demand_ticket" ? "demand-tickets" : `${entity_type}s`; const response = await apiFetch(`/api/v1/${path}`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload) }); if (response.ok) return { queued: false, id: entity_id, result: await response.json() }; } catch { /* durable fallback */ } }
  await enqueue(operation); return { queued: true, id: entity_id };
}
