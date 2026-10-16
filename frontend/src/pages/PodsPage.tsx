import { useEffect, useState } from "react";
import { cachedGet } from "../lib/api";
import { useT } from "../i18n/useT";
export function PodsPage() {
  const t = useT(); const [pods, setPods] = useState<Array<Record<string, unknown>>>([]);
  useEffect(() => { void cachedGet<Array<Record<string, unknown>>>("/api/v1/pods", "cached_pods").then(setPods); }, []);
  return <section><h2>{t("pods")}</h2><div className="grid">{pods.map(pod => { const allowed = pod.can_enrol !== false; return <article className="card" key={String(pod.id)}><h3>{String(pod.name)}</h3><p>{String(pod.pod_mode)} · {String(pod.status)}</p><p>{String(pod.explanation || "Learning practice; participation does not promise a job or income.")}</p><button disabled={!allowed}>{allowed ? t("join") : t("notEligible")}</button></article>; })}</div></section>;
}
