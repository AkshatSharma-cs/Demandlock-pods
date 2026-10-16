import { beforeEach, describe, expect, it, vi } from "vitest";
import { enqueue, listPending, listReview } from "./outbox";
import { syncNow } from "./sync";
beforeEach(() => { indexedDB.deleteDatabase("demandlock"); vi.restoreAllMocks(); Object.defineProperty(navigator, "onLine", { configurable: true, value: true }); });
describe("offline outbox", () => {
  it("enqueues", async () => { await enqueue({ client_op_id: "one", entity_type: "outcome", action: "create", entity_id: "1", payload: {}, client_occurred_at: "2026-01-01T00:00:00Z" }); expect((await listPending()).map((item) => item.client_op_id)).toEqual(["one"]); });
  it("removes duplicates", async () => { await enqueue({ client_op_id: "one", entity_type: "outcome", action: "create", entity_id: "1", payload: {}, client_occurred_at: "2026-01-01T00:00:00Z" }); vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ results: [{ client_op_id: "one", status: "duplicate" }] }), { status: 200 }))); await syncNow(); expect(await listPending()).toEqual([]); });
  it("keeps conflicts for review", async () => { await enqueue({ client_op_id: "one", entity_type: "outcome", action: "create", entity_id: "1", payload: {}, client_occurred_at: "2026-01-01T00:00:00Z" }); vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ results: [{ client_op_id: "one", status: "conflict", reason: "stale" }] }), { status: 200 }))); await syncNow(); expect((await listReview()).length).toBe(1); });
  it("keeps pending on network failure", async () => { await enqueue({ client_op_id: "one", entity_type: "outcome", action: "create", entity_id: "1", payload: {}, client_occurred_at: "2026-01-01T00:00:00Z" }); vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline"))); await syncNow(); expect((await listPending()).length).toBe(1); });
});
