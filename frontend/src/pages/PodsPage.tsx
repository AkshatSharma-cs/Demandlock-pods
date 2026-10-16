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
  return <section><div className="page-intro"><div><p className="eyebrow">Learning pathways</p><h2>Practice with purpose.</h2><p className="muted">Join supervised pods built around real local demand, source-backed skills, and practical evidence.</p></div><div className="page-mark">02</div></div><div className="feature-banner"><div className="feature-icon">◈</div><div><strong>Featured pathway</strong><h3>Automotive Assembly Assistant</h3><p>ASC/Q3607 · NSQF Level 2 · 256 training hours</p></div><span className="status-pill confirmed">Source-backed</span></div>{message && <p className="card" role="status">{message}</p>}<div className="section-heading"><div><p className="eyebrow">Available now</p><h3>Learning pods</h3></div><span className="muted">{pods.length} pathways</span></div><div className="grid">{pods.length ? pods.map(pod => { const allowed = pod.can_enrol !== false; const module = modules[pod.module_id]; return <article className="card pod-card" key={String(pod.id)}><div className="card-topline"><span className="status-pill confirmed">{String(pod.status)}</span><span className="muted">{pod.confirmed_slots || 0}/{pod.threshold_slots || 5} places</span></div><h3>{String(pod.name)}</h3><p className="pod-type">{String(pod.pod_mode).replace("_", " ")}</p><p>{String(pod.explanation || "Supervised practice; participation does not promise a job or income.")}</p><div className="progress"><span style={{ width: `${Math.min(100, ((pod.confirmed_slots || 0) / (pod.threshold_slots || 5)) * 100)}%` }} /></div><div className="claims">{(pod.claims?.claims || []).slice(0, 2).map((claim: any, index: number) => <small key={index}>✓ Source verified · <a href={claim.source_url} target="_blank" rel="noreferrer">View source</a></small>)}</div><button disabled={!allowed} onClick={() => void enrol(pod)}>{allowed ? t("join") : t("notEligible")}</button>{module?.content_json?.tasks?.[0] && user?.student_id && <form onSubmit={e => { e.preventDefault(); void submit(pod, (e.currentTarget.elements.namedItem("submission") as HTMLTextAreaElement).value); }}><p><b>{module.content_json.tasks[0].title}</b></p><textarea name="submission" placeholder="Describe what you practised" /><button className="primary-button">Submit task</button></form>}</article>; }) : <article className="card empty-state"><h3>Pathways are being prepared</h3><p className="muted">Your reference library is ready. A facilitator can turn a confirmed demand request into a supervised pod.</p></article>}</div></section>;
}
