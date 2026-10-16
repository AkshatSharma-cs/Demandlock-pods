import { useEffect, useState } from "react";
import { apiFetch } from "../offline/api";
import type { CurrentUser } from "../types";
export function OutcomesPage({ user }: { user?: CurrentUser | null }) {
  const [outcomes, setOutcomes] = useState<any[]>([]);
  useEffect(() => { void apiFetch("/api/v1/outcomes").then(r => r.ok ? r.json() : []).then(setOutcomes); }, []);
  return <section><h2>Outcomes</h2><article className="card"><p>{user?.name || "Learner"}: self-reported and verified outcomes remain separate.</p>{outcomes.map(outcome => <p key={outcome.id}><b>{outcome.event_type}</b> · {(outcome.payload || {}).verification_level}</p>)}</article></section>;
}
