import { useEffect, useState } from "react";
import { cachedGet } from "../lib/api";
import { apiFetch } from "../offline/api";
import { useT } from "../i18n/useT";
import type { CurrentUser } from "../types";

export function PodsPage({ user }: { user?: CurrentUser | null }) {
  const t = useT(); const [pods, setPods] = useState<Array<Record<string, any>>>([]); const [modules, setModules] = useState<Record<string, any>>({}); const [message, setMessage] = useState("");
  const refresh = () => void cachedGet<Array<Record<string, any>>>("/api/v1/pods", "cached_pods").then(setPods);
  useEffect(() => { refresh(); void apiFetch("/api/v1/modules").then(r => r.ok ? r.json() : []).then(rows => setModules(Object.fromEntries(rows.map((row: any) => [row.id, row])))); }, []);
  const enrol = async (pod: Record<string, any>) => {
    if (!user?.student_id) { setMessage("Sign in as a student to enrol."); return; }
    const response = await apiFetch(`/api/v1/pods/${pod.id}/enrolments`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ student_id: user.student_id }) });
    setMessage(response.ok ? "Enrolled in supervised learning." : (await response.json()).detail || "Enrollment blocked.");
  };
  const submit = async (pod: any, text: string) => {
    const module = modules[pod.module_id]; if (!module || !user?.student_id) return;
    const response = await apiFetch(`/api/v1/tasks/${module.id}:0/submissions`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ pod_id: pod.id, student_id: user.student_id, submitted_text: text }) });
    setMessage(response.ok ? "Task submitted for teacher review." : (await response.json()).detail || "Submission failed.");
  };
  return <section><h2>{t("pods")}</h2>{message && <p className="card" role="status">{message}</p>}<div className="grid">{pods.map(pod => { const allowed = pod.can_enrol !== false; const module = modules[pod.module_id]; return <article className="card" key={String(pod.id)}><h3>{String(pod.name)}</h3><p>{String(pod.pod_mode)} · {String(pod.status)}</p><p>{String(pod.explanation || "Learning practice; participation does not promise a job or income.")}</p><div className="claims">{(pod.claims?.claims || []).map((claim: any, index: number) => <small key={index}>Source: <a href={claim.source_url} target="_blank" rel="noreferrer">{claim.source_url}</a> · checked {claim.last_checked_at}</small>)}</div><button disabled={!allowed} onClick={() => void enrol(pod)}>{allowed ? t("join") : t("notEligible")}</button>{module?.content_json?.tasks?.[0] && user?.student_id && <form onSubmit={e => { e.preventDefault(); void submit(pod, (e.currentTarget.elements.namedItem("submission") as HTMLTextAreaElement).value); }}><p><b>{module.content_json.tasks[0].title}</b></p><textarea name="submission" placeholder="Describe what you practised" /><button className="primary-button">Submit task</button></form>}</article>; })}</div></section>;
}
