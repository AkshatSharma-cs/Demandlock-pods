import { apiFetch } from "../offline/api";
import { getDB } from "../offline/db";
export async function getJson<T>(path: string): Promise<T> {
  const response = await apiFetch(path);
  if (!response.ok) throw new Error(`Request failed: ${response.status}`);
  return response.json() as Promise<T>;
}
export async function cachedGet<T>(path: string, store: "cached_pods" | "cached_modules"): Promise<T> {
  try { return await getJson<T>(path); }
  catch {
    const rows = await (await getDB()).getAll(store);
    return rows as T;
  }
}
