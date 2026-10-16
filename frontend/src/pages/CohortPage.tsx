import { useEffect, useState } from "react";
import { apiFetch } from "../offline/api";
import type { CurrentUser } from "../types";
import { buildModuleAttachmentPayload, buildPodEvaluationPayload, reviewAction } from "../workflowActions";

type Block = { code: string; name?: string; district?: string; state?: string };

async function errorDetail(response: Response, fallback: string) {
  try {
    const body = await response.json();
    return body.detail || fallback;
  } catch {
    return fallback;
  }
}

export function CohortPage({ user }: { user?: CurrentUser | null }) {
  const [pods, setPods] = useState<any[]>([]);
  const [submissions, setSubmissions] = useState<any[]>([]);
  const [modules, setModules] = useState<any[]>([]);
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [message, setMessage] = useState("");
  const [evaluation, setEvaluation] = useState({ block_code: "", skill_family_id: "mobile_repair", pod_mode: "supervised_practice" });
  const [module, setModule] = useState({ title: "", skill_family_id: "mobile_repair", pricing_model: "free", price_minor: "" });
  const isFacilitator = user?.role === "facilitator" || user?.role === "admin";

  const load = async () => {
    const podResponse = await apiFetch("/api/v1/pods");
    const rows = podResponse.ok ? await podResponse.json() : [];
    setPods(rows);
    const all: any[] = [];
    if (isFacilitator) {
      for (const pod of rows) {
        const response = await apiFetch(`/api/v1/pods/${pod.id}/submissions`);
        if (response.ok) all.push(...await response.json());
      }
    }
    setSubmissions(all);
    const moduleResponse = await apiFetch("/api/v1/modules");
    setModules(moduleResponse.ok ? await moduleResponse.json() : []);
  };

  useEffect(() => {
    void load();
    void apiFetch("/api/v1/blocks").then(r => r.ok ? r.json() : []).then((rows: Block[]) => {
      setBlocks(rows);
      if (rows[0]) setEvaluation(current => ({ ...current, block_code: current.block_code || rows[0].code }));
    });
  }, [isFacilitator]);

  const evaluate = async () => {
    const response = await apiFetch("/api/v1/pods/evaluate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildPodEvaluationPayload(evaluation.block_code, evaluation.skill_family_id, evaluation.pod_mode)),
    });
    setMessage(response.ok ? "Demand evaluated with the selected pod mode." : await errorDetail(response, "Demand evaluation failed."));
    if (response.ok) await load();
  };

  const attachModule = async (podId: string, moduleId: string) => {
    if (!moduleId) return;
    const response = await apiFetch(`/api/v1/pods/${podId}/module`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildModuleAttachmentPayload(moduleId)),
    });
    setMessage(response.ok ? "Published module attached to the pod." : await errorDetail(response, "Module attachment failed."));
    if (response.ok) await load();
  };

  const review = async (submission: any) => {
    const action = reviewAction(user?.role || "", submission.age_band);
    if (!action) {
      setMessage("Employer review is available only for adult submissions.");
      return;
    }
    const response = await apiFetch(`/api/v1/submissions/${submission.id}/${action.path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(action.body),
    });
    setMessage(response.ok ? "Submission reviewed." : await errorDetail(response, "Review failed."));
    if (response.ok) await load();
  };

  const createModule = async () => {
    const response = await apiFetch("/api/v1/modules", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ ...module, price_minor: module.price_minor ? Number(module.price_minor) : null, language: "en" }),
    });
    if (response.ok) {
      setModules([...modules, await response.json()]);
      setMessage("Module draft created. Publish after teacher review.");
    } else setMessage(await errorDetail(response, "Module creation failed."));
  };

  const publish = async (row: any) => {
    const response = await apiFetch(`/api/v1/modules/${row.id}/publish`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ human_reviewed: true }),
    });
    setMessage(response.ok ? "Module published after human review." : await errorDetail(response, "Publish failed."));
    if (response.ok) await load();
  };

  return <section>
    <div className="page-intro"><div><p className="eyebrow">Facilitator workspace</p><h2>Guide the next step.</h2><p className="muted">Review learner evidence, shape practical modules, and keep publishing decisions human-led.</p></div><div className="page-mark">03</div></div>
    {isFacilitator && <>
      <article className="card author-card">
        <div><p className="eyebrow">Demand evaluation</p><h3>Open a learning pathway</h3><p className="muted">Choose the safeguarding mode that matches the pathway before evaluating demand.</p></div>
        <div className="form-row">
          <label>Block<select value={evaluation.block_code} onChange={e => setEvaluation({ ...evaluation, block_code: e.target.value })}><option value="">Choose a block</option>{blocks.map(block => <option key={block.code} value={block.code}>{block.name ? `${block.name} (${block.code})` : block.code}</option>)}</select></label>
          <label>Skill family<input value={evaluation.skill_family_id} onChange={e => setEvaluation({ ...evaluation, skill_family_id: e.target.value })} /></label>
          <label>Pod mode<select value={evaluation.pod_mode} onChange={e => setEvaluation({ ...evaluation, pod_mode: e.target.value })}><option value="supervised_practice">Supervised practice</option><option value="work_trial">Work trial</option></select></label>
        </div>
        <button className="primary-button" disabled={!evaluation.block_code || !evaluation.skill_family_id} onClick={() => void evaluate()}>Evaluate demand</button>
      </article>
      <div className="metric-grid compact"><div className="metric-card"><span>Active pods</span><strong>{pods.length}</strong><small>Supervised pathways</small></div><div className="metric-card"><span>Submissions</span><strong>{submissions.length}</strong><small>Awaiting review</small></div><div className="metric-card"><span>Modules</span><strong>{modules.length}</strong><small>Drafts and published</small></div></div>
      <article className="card author-card"><div><p className="eyebrow">Module studio</p><h3>Author a practical module</h3><p className="muted">Start from a real skill need. Every module stays reviewable before it is published.</p></div><div className="form-row"><label>Title<input value={module.title} onChange={e => setModule({ ...module, title: e.target.value })} placeholder="Safe mobile repair practice" /></label><label>Pricing<select value={module.pricing_model} onChange={e => setModule({ ...module, pricing_model: e.target.value })}><option value="free">Free</option><option value="pay_per_module">Pay per module</option><option value="subscription">Subscription</option></select></label></div><button className="primary-button" onClick={() => void createModule()}>Create reviewed draft</button></article>
      <div className="section-heading"><div><p className="eyebrow">Content pipeline</p><h3>Modules</h3></div></div><div className="grid">{modules.map(row => <article className="card" key={row.id}><div className="card-topline"><span className={`status-pill ${row.status}`}>{row.status}</span></div><h3>{row.title}</h3><p className="muted">Human review required before learners see this content.</p>{row.status !== "published" && <button onClick={() => void publish(row)}>Publish after review</button>}</article>)}</div>
    </>}
    {message && <p className="card" role="status">{message}</p>}
    <div className="section-heading"><div><p className="eyebrow">Cohort pulse</p><h3>Active pathways</h3></div></div><div className="grid">{pods.map(pod => <article className="card" key={pod.id}><h3>{pod.name}</h3><p>{pod.confirmed_slots}/{pod.threshold_slots} confirmed places · {pod.status} · {pod.pod_mode}</p><div className="progress"><span style={{ width: `${Math.min(100, ((pod.confirmed_slots || 0) / (pod.threshold_slots || 5)) * 100)}%` }} /></div><p className="muted">{pod.enrolments?.length || 0} learners enrolled</p>{isFacilitator && <label>Attach published module<select aria-label={`Attach module to ${pod.name}`} defaultValue={pod.module_id || ""} onChange={e => void attachModule(pod.id, e.target.value)}><option value="">Choose published module</option>{modules.filter(row => row.status === "published").map(row => <option key={row.id} value={row.id}>{row.title}</option>)}</select></label>}</article>)}</div>
    <div className="section-heading"><div><p className="eyebrow">Human review queue</p><h3>Task submissions</h3></div></div><div className="grid">{submissions.length ? submissions.map(submission => <article className="card" key={submission.id}><div className="card-topline"><span className="status-pill">{submission.status}</span><span className="badge">{submission.age_band}</span></div><h3>{submission.student_name}</h3><p className="muted">{submission.task_id}</p>{reviewAction(user?.role || "", submission.age_band) ? <button onClick={() => void review(submission)}>{user?.role === "employer" ? "Review as employer" : "Review with rubric"}</button> : <p className="muted">Minor submissions can only be reviewed by a facilitator.</p>}</article>) : <article className="card empty-state"><h3>No submissions yet</h3><p className="muted">Learner evidence will appear here once a pod task is submitted.</p></article>}</div>
  </section>;
}
