import { FormEvent, useEffect, useRef, useState } from "react";
import { apiFetch } from "../offline/api";
import { useT } from "../i18n/useT";
import { VoiceButton, SpeakButton } from "../voice/VoiceButton";
import { useDictation } from "../voice/useDictation";
import type { CurrentUser } from "../types";

type Block = { code: string; name: string; district?: string; state?: string };
type Ticket = Record<string, any>;
type Reference = { skills: Array<{ slug: string; name: string }>; records: Array<{ id: string; title: string; source_url: string; verification_status: string }> };

export function DemandPage({ user }: { user?: CurrentUser | null }) {
  const t = useT();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [reference, setReference] = useState<Reference>({ skills: [], records: [] });
  const [form, setForm] = useState({ employer_name: user?.name || "", source_type: "text", transcript_original: "", block_code: "" });
  const [message, setMessage] = useState(""); const [voice, setVoice] = useState<{ blob: Blob; mimeType: string }>();
  const dictation = useDictation((user?.language as "en" | "hi" | "ta") || "en");
  const userLanguage = (user?.language as "en" | "hi" | "ta") || "en";
  const appendedDictationRef = useRef("");
  const load = async () => {
    const response = await apiFetch("/api/v1/demand-tickets");
    if (response.ok) setTickets(await response.json());
  };
  useEffect(() => { void load(); void apiFetch("/api/v1/blocks").then(r => r.ok ? r.json() : []).then(setBlocks); void apiFetch("/api/v1/reference").then(r => r.ok ? r.json() : { skills: [], records: [] }).then(setReference); }, []);
  useEffect(() => {
    if (!dictation.finalText || dictation.finalText === appendedDictationRef.current) return;
    appendedDictationRef.current = dictation.finalText;
    setForm(current => ({ ...current, transcript_original: `${current.transcript_original}${current.transcript_original ? " " : ""}${dictation.finalText}` }));
  }, [dictation.finalText]);
  const submit = async (event: FormEvent) => {
    event.preventDefault(); setMessage("");
    const created = await apiFetch("/api/v1/demand-tickets", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...form, transcript_language: userLanguage, source_type: voice ? "voice" : "text" }) });
    if (!created.ok) { setMessage("Could not create the demand ticket."); return; }
    const ticket = await created.json();
    const extracted = await apiFetch(`/api/v1/demand-tickets/${ticket.id}/extract`, { method: "POST" });
    if (extracted.ok) { if (voice) { const audio = new FormData(); audio.append("file", voice.blob, `demand.${voice.mimeType.split("/")[1] || "audio"}`); await apiFetch(`/api/v1/demand-tickets/${ticket.id}/audio`, { method: "POST", body: audio }); } setMessage("Draft extracted. A human must review and confirm it."); await load(); }
  };
  const confirm = async (ticket: Ticket) => {
    const proposed = ticket.proposed_fields || {};
    const response = await apiFetch(`/api/v1/demand-tickets/${ticket.id}/confirm`, {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ confirmed_skill_id: proposed.skill_family || "mobile_repair", slots_confirmed: proposed.slots || 1, block_code: form.block_code || ticket.block_code || "unmapped-block", demand_type: proposed.demand_type || "employment", pay_min_minor: proposed.pay_min_minor, pay_max_minor: proposed.pay_max_minor, pay_period: proposed.pay_period }),
    });
    setMessage(response.ok ? "Ticket confirmed." : "Confirmation needs a valid skill and block.");
    if (response.ok) await load();
  };
  return <section><div className="page-intro"><div><p className="eyebrow">Demand intelligence</p><h2>Turn local needs into learning pathways.</h2><p className="muted">Capture a real request, review the AI draft, and keep every decision grounded in local evidence.</p></div><div className="page-mark">01</div></div>
    <div className="metric-grid"><div className="metric-card"><span>Open requests</span><strong>{tickets.filter(ticket => ticket.status !== "confirmed").length}</strong><small>Awaiting review</small></div><div className="metric-card"><span>Reference skills</span><strong>{reference.skills.length}</strong><small>Preloaded locally</small></div><div className="metric-card"><span>Source records</span><strong>{reference.records.length}</strong><small>Ready to cite</small></div></div>
    {user?.role !== "student" && <article className="card"><h3>Capture local demand</h3><form onSubmit={submit}>
      <label>Employer name<input value={form.employer_name} onChange={e => setForm({ ...form, employer_name: e.target.value })} required /></label>
      <label>Need or voice-note transcript<textarea value={form.transcript_original} onChange={e => setForm({ ...form, transcript_original: e.target.value })} required={!voice} placeholder="I need two mobile repair helpers..." /></label><div className="voice-actions"><VoiceButton lang={userLanguage} onRecorded={(blob, mimeType) => setVoice({ blob, mimeType })} /><div className="dictation-control">{dictation.supported && <button type="button" className={`dictation-button ${dictation.listening ? "listening" : ""}`} onClick={() => dictation.listening ? dictation.stop() : dictation.start()}>{dictation.listening ? "■ Stop dictation" : "✦ Dictate"}</button>}<small>{dictation.supported ? "Browser speech service · needs internet · always edit before confirming" : "Voice dictation unavailable · type instead"}</small>{dictation.error && <span className="unknown">{dictation.error}</span>}</div></div>{(dictation.finalText || dictation.interimText) && <p className="dictation-preview"><b>Dictation:</b> {dictation.finalText} <em>{dictation.interimText}</em></p>}<SpeakButton lang={userLanguage} text="Describe the local work needed, then review the extracted ticket." />
      <label>Block{blocks.length ? <select value={form.block_code} onChange={e => setForm({ ...form, block_code: e.target.value })}><option value="">Choose a block</option>{blocks.map(block => <option key={block.code} value={block.code}>{block.name} ({block.code})</option>)}</select> : <input value={form.block_code} onChange={e => setForm({ ...form, block_code: e.target.value })} placeholder="Enter block code" required />}</label>
      <button className="primary-button">Extract draft</button>
    </form></article>}
    {message && <p className="card" role="status">{message}</p>}
    <div className="section-heading"><div><p className="eyebrow">Your workspace</p><h3>Recent demand requests</h3></div><span className="muted">{tickets.length} total</span></div><div className="grid">{tickets.length ? tickets.map(ticket => <article className="card" key={ticket.id}><div className="card-topline"><span className={`status-pill ${ticket.status}`}>{ticket.status.replace("_", " ")}</span><span className="muted">{ticket.slots_confirmed ?? 0} slots</span></div><h3>{ticket.employer_name}</h3><p>{ticket.transcript_original || "No transcript"}</p>{ticket.status === "needs_confirmation" && user?.role !== "student" && <button className="primary-button" onClick={() => void confirm(ticket)}>Confirm reviewed ticket</button>}</article>) : <article className="card empty-state"><div className="empty-icon">✦</div><h3>Your demand desk is ready</h3><p className="muted">Create your first request above. Your preloaded skill and source library will help the extractor make a stronger draft.</p></article>}</div>
    <div className="section-heading"><div><p className="eyebrow">Preloaded library</p><h3>Reference skills</h3></div><span className="muted">Source-backed starting points</span></div><div className="reference-grid">{reference.skills.map(skill => <article className="reference-card" key={skill.slug}><span className="reference-icon">↗</span><div><strong>{skill.name}</strong><small>{reference.records.filter(record => record.id.includes(skill.slug) || record.title.toLowerCase().includes(skill.name.toLowerCase().split(" ")[0])).length || "Source"} records available</small></div></article>)}</div>
  </section>;
}
