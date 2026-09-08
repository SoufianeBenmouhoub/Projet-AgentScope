import { useQuery } from "@tanstack/react-query";
import { Link, useParams } from "react-router-dom";

import { fetchSessionDetail } from "../../shared/api/sessions";
import type { SessionEventResponse } from "../../shared/api/types";
import { formatAggregateValue } from "./utils/formatMetric";

export function SessionDetailPage() {
  const { sessionId } = useParams<{ sessionId: string }>();

  const { data, isPending, isError } = useQuery({
    queryKey: ["sessions", sessionId],
    queryFn: () => fetchSessionDetail(sessionId as string),
    enabled: Boolean(sessionId),
  });

  if (!sessionId) {
    return <p className="status-message status-message--error">Identifiant de session manquant.</p>;
  }

  if (isPending) {
    return <p className="status-message">Chargement de la session…</p>;
  }

  if (isError || !data) {
    return (
      <section className="page">
        <p className="status-message status-message--error" role="alert">
          Session introuvable ou API indisponible.
        </p>
        <Link to="/" className="btn btn--link">
          ← Retour au dashboard
        </Link>
      </section>
    );
  }

  return (
    <section className="page">
      <header className="page__header">
        <p>
          <Link to="/" className="btn btn--link">
            ← Dashboard
          </Link>
        </p>
        <h1>Session {data.session_id}</h1>
        <p className="page__lead">
          {data.source} · {data.agent}
        </p>
      </header>

      <section aria-label="Résumé de la session">
        <h2 className="section-title">Résumé</h2>
        <dl className="detail-grid">
          <div>
            <dt>Début</dt>
            <dd>{data.started_at ? new Date(data.started_at).toLocaleString("fr-FR") : "—"}</dd>
          </div>
          <div>
            <dt>Fin</dt>
            <dd>{data.ended_at ? new Date(data.ended_at).toLocaleString("fr-FR") : "—"}</dd>
          </div>
          <div>
            <dt>Durée</dt>
            <dd>{formatAggregateValue(data.duration)}</dd>
          </div>
          <div>
            <dt>Tokens entrée</dt>
            <dd>{formatAggregateValue(data.input_tokens)}</dd>
          </div>
          <div>
            <dt>Appels modèle</dt>
            <dd>{data.model_calls}</dd>
          </div>
          <div>
            <dt>Appels outils</dt>
            <dd>{data.tool_calls}</dd>
          </div>
          <div>
            <dt>Échecs outils</dt>
            <dd>{data.failed_tool_calls}</dd>
          </div>
        </dl>
      </section>

      <section aria-label="Chronologie">
        <h2 className="section-title">Chronologie</h2>
        {data.events.length === 0 ? (
          <p className="status-message">Aucun événement enregistré pour cette session.</p>
        ) : (
          <ol className="timeline">
            {data.events.map((event: SessionEventResponse, index: number) => (
              <li key={`${event.kind}-${event.label}-${index}`} className="timeline__item">
                <span className={`timeline__badge timeline__badge--${event.kind}`}>
                  {event.kind === "model_call" ? "Modèle" : "Outil"}
                </span>
                <div className="timeline__content">
                  <p className="timeline__label">{event.label}</p>
                  <p className="timeline__meta">
                    {event.occurred_at
                      ? new Date(event.occurred_at).toLocaleString("fr-FR")
                      : "Date inconnue"}
                    {event.input_tokens !== null && <> · {event.input_tokens} tokens</>}
                    {event.latency_ms !== null && <> · {event.latency_ms} ms</>}
                    {event.is_error === true && <> · erreur</>}
                    {event.is_error === false && <> · succès</>}
                    {event.is_error === null && <> · issue inconnue</>}
                  </p>
                </div>
              </li>
            ))}
          </ol>
        )}
      </section>
    </section>
  );
}
