import { useEffect, useState } from "react";
import { apiFetch } from "../offline/api";
export function ImpactPage() {
  const [data, setData] = useState<any>(); useEffect(() => { void apiFetch("/api/v1/dashboard/impact").then(r => r.ok ? r.json() : null).then(setData); }, []);
  return <section><h2>Impact dashboard</h2><article className="card"><strong>Data mode: {data?.data_mode || "loading"}</strong>{Object.entries(data?.outcomes || {}).map(([stage, levels]) => <div className="outcome-row" key={stage}><b>{stage}</b>{Object.entries(levels as Record<string, number>).map(([level, count]) => <span className="badge" key={level}>{level}: {count}</span>)}</div>)}</article></section>;
}
