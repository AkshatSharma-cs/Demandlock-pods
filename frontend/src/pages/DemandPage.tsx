import { useEffect, useState } from "react";
import { cachedGet } from "../lib/api";
import { useT } from "../i18n/useT";
export function DemandPage() {
  const t = useT(); const [tickets, setTickets] = useState<Array<Record<string, unknown>>>([]);
  useEffect(() => { void cachedGet<Array<Record<string, unknown>>>("/api/v1/demand-tickets", "cached_pods").then(setTickets); }, []);
  return <section><h2>{t("demand")}</h2><div className="grid">{tickets.map(ticket => <article className="card" key={String(ticket.id)}><h3>{String(ticket.employer_name)}</h3><p>{String(ticket.status)} · {String(ticket.slots_confirmed ?? 0)} slots</p><p className="unknown">{ticket.pay_min_minor == null ? t("unknown") : `${String(ticket.pay_min_minor)}–${String(ticket.pay_max_minor ?? ticket.pay_min_minor)}`}</p></article>)}</div></section>;
}
