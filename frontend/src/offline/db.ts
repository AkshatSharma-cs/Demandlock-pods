import { openDB, type DBSchema, type IDBPDatabase } from "idb";
export type SyncStatus = "pending" | "syncing" | "needs_review" | "failed";
export interface OutboxItem { client_op_id: string; entity_type: string; action: string; entity_id?: string; base_version?: number; payload: Record<string, unknown>; client_occurred_at: string; sync_status: SyncStatus; reason?: string; }
interface DemandlockDB extends DBSchema {
  cached_pods: { key: string; value: Record<string, unknown> };
  cached_modules: { key: string; value: Record<string, unknown> };
  local_drafts: { key: string; value: Record<string, unknown> };
  outbox: { key: string; value: OutboxItem; indexes: { "by-status": SyncStatus; "by-created": string } };
  pending_audio: { key: string; value: { ticket_id: string; blob: Blob; mimeType: string } };
  sync_metadata: { key: string; value: string };
}
let database: Promise<IDBPDatabase<DemandlockDB>> | undefined;
export function getDB() {
  database ??= openDB<DemandlockDB>("demandlock", 1, { upgrade(db) {
    db.createObjectStore("cached_pods"); db.createObjectStore("cached_modules"); db.createObjectStore("local_drafts");
    const outbox = db.createObjectStore("outbox", { keyPath: "client_op_id" }); outbox.createIndex("by-status", "sync_status"); outbox.createIndex("by-created", "client_occurred_at");
    db.createObjectStore("pending_audio", { keyPath: "ticket_id" }); db.createObjectStore("sync_metadata");
  }});
  return database;
}
