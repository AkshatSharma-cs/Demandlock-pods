import { getDB, type OutboxItem, type SyncStatus } from "./db";
export async function enqueue(item: Omit<OutboxItem, "sync_status">) { await (await getDB()).put("outbox", { ...item, sync_status: "pending" }); return item.client_op_id; }
export async function listPending() { const items = await (await getDB()).getAllFromIndex("outbox", "by-created"); return items.filter((item) => item.sync_status === "pending" || item.sync_status === "syncing"); }
export async function listReview() { return (await (await getDB()).getAll("outbox")).filter((item) => item.sync_status === "needs_review"); }
export async function markStatus(id: string, sync_status: SyncStatus, reason?: string) { const db = await getDB(); const item = await db.get("outbox", id); if (item) await db.put("outbox", { ...item, sync_status, reason }); }
export async function remove(id: string) { await (await getDB()).delete("outbox", id); }
export async function counts() { const items = await (await getDB()).getAll("outbox"); return { pending: items.filter((item) => item.sync_status === "pending" || item.sync_status === "syncing").length, needsReview: items.filter((item) => item.sync_status === "needs_review").length }; }
