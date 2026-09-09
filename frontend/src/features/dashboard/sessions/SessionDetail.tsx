import type { SessionDetail as SessionDetailPayload } from "../../../shared/api/types";
import { formatAggregate, UNAVAILABLE } from "../formatting";
import { formatMoment } from "./SessionList";

/**
 * La vue détaillée d'une session : ses compteurs et sa chronologie.
 *
 * Deux détails qui ne sont pas cosmétiques :
 *
 * - un événement non horodaté apparaît en fin de chronologie plutôt que d'être retiré ;
 * - l'issue d'un appel d'outil a trois états, et « inconnue » n'est pas « réussi ».
 */
export function SessionDetail({ detail }: { detail: SessionDetailPayload }) {
  return (
    <section className="session" aria-label={`Détail de la session ${detail.session_id}`}>
      <h3 className="session__title">Session {detail.session_id}</h3>

      <dl className="session__facts">
        <div>
          <dt>Source</dt>
          <dd>{detail.source}</dd>
        </div>
        <div>
          <dt>Agent</dt>
          {/* Toutes les sources ne nomment pas l'agent : une case vide se lirait comme un
              oubli d'affichage, « n/a » dit que l'information n'existe pas. */}
          <dd>{detail.agent ?? UNAVAILABLE}</dd>
        </div>
        <div>
          <dt>Début</dt>
          <dd>{formatMoment(detail.started_at)}</dd>
        </div>
        <div>
          <dt>Durée</dt>
          <dd>{formatAggregate(detail.duration)}</dd>
        </div>
        <div>
          <dt>Appels au modèle</dt>
          <dd>{detail.model_calls}</dd>
        </div>
        <div>
          <dt>Appels d'outils</dt>
          <dd>
            {detail.tool_calls}
            {detail.failed_tool_calls > 0 && ` — dont ${detail.failed_tool_calls} en erreur`}
          </dd>
        </div>
        <div>
          <dt>Tokens en entrée</dt>
          <dd>{formatAggregate(detail.input_tokens)}</dd>
        </div>
      </dl>

      <h4 className="session__subtitle">Chronologie</h4>
      <table className="session__events">
        <thead>
          <tr>
            <th scope="col">Instant</th>
            <th scope="col">Type</th>
            <th scope="col">Détail</th>
            <th scope="col">Tokens</th>
            <th scope="col">Issue</th>
            <th scope="col">Latence</th>
          </tr>
        </thead>
        <tbody>
          {detail.events.map((event, index) => (
            <tr key={`${event.kind}-${index}`}>
              <td>{formatMoment(event.occurred_at)}</td>
              <td>{event.kind === "model_call" ? "Appel modèle" : "Appel outil"}</td>
              <td>{event.label}</td>
              <td>{event.input_tokens ?? UNAVAILABLE}</td>
              <td>{outcomeOf(event.is_error)}</td>
              <td>{event.latency_ms === null ? UNAVAILABLE : `${event.latency_ms} ms`}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}

/** Trois états, pas deux : ne pas savoir n'est pas la même chose que réussir. */
function outcomeOf(isError: boolean | null): string {
  if (isError === null) return UNAVAILABLE;
  return isError ? "erreur" : "succès";
}
