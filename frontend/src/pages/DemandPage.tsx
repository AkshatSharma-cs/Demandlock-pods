import { FormEvent, useEffect, useState } from "react";
import { apiFetch } from "../offline/api";
import { useT } from "../i18n/useT";
import { VoiceButton, SpeakButton } from "../voice/VoiceButton";
import type { CurrentUser } from "../types";

type Block = { code: string; name: string; district?: string; state?: string };
type Ticket = Record<string, any>;

export function DemandPage({ user }: { user?: CurrentUser | null }) {
  const t = useT();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [blocks, setBlocks] = useState<Block[]>([]);
  const [form, setForm] = useState({ employer_name: user?.name || "", source_type: "text", transcript_original: "", block_code: "" });
  const [message, setMessage] = useState(""); const [voice, setVoice] = useState<{ blob: Blob; mimeType: string }>();
  const load = async () => {
    const response = await apiFetch("/api/v1/demand-tickets");
    if (response.ok) setTickets(await response.json());
  };
  useEffect(() => { void load(); void apiFetch("/api/v1/blocks").then(r => r.ok ? r.json() : []).then(setBlocks); }, []);
  const submit = async (event: FormEvent) => {
    event.preventDefault(); setMessage("");
    const created = await apiFetch("/api/v1/demand-tickets", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ ...form, source_type: voice ? "voice" : "text" }) });
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
  return <section><h2>{t("demand")}</h2>
    {user?.role !== "student" && <article className="card"><h3>Capture local demand</h3><form onSubmit={submit}>
      <label>Employer name<input value={form.employer_name} onChange={e => setForm({ ...form, employer_name: e.target.value })} required /></label>
      <label>Need or voice-note transcript<textarea value={form.transcript_original} onChange={e => setForm({ ...form, transcript_original: e.target.value })} required={!voice} placeholder="I need two mobile repair helpers..." /></label><VoiceButton lang={(user?.language as "en" | "hi" | "ta") || "en"} onRecorded={(blob, mimeType) => setVoice({ blob, mimeType })} /><SpeakButton lang={(user?.language as "en" | "hi" | "ta") || "en"} text="Describe the local work needed, then review the extracted ticket." />
      <label>Block{blocks.length ? <select value={form.block_code} onChange={e => setForm({ ...form, block_code: e.target.value })}><option value="">Choose a block</option>{blocks.map(block => <option key={block.code} value={block.code}>{block.name} ({block.code})</option>)}</select> : <input value={form.block_code} onChange={e => setForm({ ...form, block_code: e.target.value })} placeholder="Enter block code" required />}</label>
      <button className="primary-button">Extract draft</button>
    </form></article>}
    {message && <p className="card" role="status">{message}</p>}
    <div className="grid">{tickets.map(ticket => <article className="card" key={ticket.id}><h3>{ticket.employer_name}</h3><p>{ticket.status} · {ticket.slots_confirmed ?? 0} slots</p><p>{ticket.transcript_original || "No transcript"}</p>{ticket.status === "needs_confirmation" && user?.role !== "student" && <button className="primary-button" onClick={() => void confirm(ticket)}>Confirm reviewed ticket</button>}</article>)}</div>
  </section>;
}
