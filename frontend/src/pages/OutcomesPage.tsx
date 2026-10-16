import { useEffect, useState } from "react";
import { apiFetch } from "../offline/api";
import type { CurrentUser } from "../types";
import { buildOutcomePayload } from "../workflowActions";

async function errorDetail(response: Response, fallback: string) {
  try {
    const body = await response.json();
    return body.detail || fallback;
  } catch {
    return fallback;
  }
}

export function OutcomesPage({ user }: { user?: CurrentUser | null }) {
  const [outcomes, setOutcomes] = useState<any[]>([]);
  const [pods, setPods] = useState<any[]>([]);
  const [studentId, setStudentId] = useState(user?.student_id || "");
  const [podId, setPodId] = useState("");
  const [stage, setStage] = useState("task_completed");
  const [notes, setNotes] = useState("");
  const [message, setMessage] = useState("");
  const isStudent = user?.role === "student";

  const load = async () => {
    const [outcomesResponse, podsResponse] = await Promise.all([apiFetch("/api/v1/outcomes"), apiFetch("/api/v1/pods")]);
    setOutcomes(outcomesResponse.ok ? await outcomesResponse.json() : []);
    setPods(podsResponse.ok ? await podsResponse.json() : []);
  };
  useEffect(() => { void load(); }, []);
  useEffect(() => { if (user?.student_id) setStudentId(user.student_id); }, [user?.student_id]);

  const record = async () => {
    const response = await apiFetch("/api/v1/outcomes", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(buildOutcomePayload(user?.role || "student", studentId, podId, stage, notes)),
    });
    setMessage(response.ok ? "Outcome recorded." : await errorDetail(response, "Outcome could not be recorded."));
    if (response.ok) { setNotes(""); await load(); }
  };

  return <section><div className="page-intro"><div><p className="eyebrow">Your evidence</p><h2>Progress you can stand behind.</h2><p className="muted">Your learning record keeps self-reported milestones separate from evidence reviewed by a facilitator or employer.</p></div><div className="page-mark">04</div></div>
    <article className="card outcome-intro"><div className="empty-icon">✓</div><div><h3>{user?.name || "Learner"}’s outcome record</h3><p className="muted">Verified evidence is stronger than a claim. Keep adding practical work, reviews, and outcomes.</p></div></article>
    <article className="card author-card"><div><p className="eyebrow">Record progress</p><h3>{isStudent ? "Add a self-reported milestone" : "Confirm a student stage"}</h3><p className="muted">{isStudent ? "Students can record only self-reported progress." : "The server applies age and safeguarding rules. Any 403 reason is shown here."}</p></div><div className="form-row"><label>Student ID<input value={studentId} disabled={isStudent} onChange={e => setStudentId(e.target.value)} placeholder="Student ID" /></label><label>Pod<select value={podId} onChange={e => setPodId(e.target.value)}><option value="">Choose a pod</option>{pods.map(pod => <option key={pod.id} value={pod.id}>{pod.name} ({pod.pod_mode})</option>)}</select></label><label>Stage<select value={stage} onChange={e => setStage(e.target.value)}><option value="interest_recorded">Interest recorded</option><option value="task_completed">Task completed</option>{!isStudent && <><option value="trial_interview_offered">Trial offered</option><option value="started_work">Started work</option><option value="first_payment_verified">First payment</option></>}</select></label></div><label>Notes<textarea value={notes} onChange={e => setNotes(e.target.value)} placeholder="What evidence was reviewed?" /></label><button className="primary-button" disabled={!studentId || !podId} onClick={() => void record()}>Record stage</button></article>
    {message && <p className="card" role="alert">{message}</p>}
    <div className="section-heading"><div><p className="eyebrow">Timeline</p><h3>Recorded outcomes</h3></div></div><div className="grid">{outcomes.length ? outcomes.map(outcome => <article className="card" key={outcome.id}><div className="card-topline"><span className="status-pill confirmed">{(outcome.payload || {}).verification_level || "self reported"}</span></div><h3>{outcome.event_type}</h3><p className="muted">Evidence level recorded in the learning workspace.</p></article>) : <article className="card empty-state"><h3>Your record starts here</h3><p className="muted">Complete a pod task or add an outcome to build a portable, trustworthy record.</p></article>}</div></section>;
}
