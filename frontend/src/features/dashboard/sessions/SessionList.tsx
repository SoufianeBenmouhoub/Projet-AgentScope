import type { SessionList as SessionListPayload } from "../../../shared/api/types";
import { formatAggregate } from "../formatting";

const MOMENT = new Intl.DateTimeFormat("fr-FR", {
  dateStyle: "short",
  timeStyle: "short",
});

export function formatMoment(iso: string | null): string {
  return iso === null ? "non horodatée" : MOMENT.format(new Date(iso));
}

interface Props {
  listing: SessionListPayload;
  /** Ce qui a produit cette sélection, pour que l'utilisateur sache d'où il vient. */
  origin: string;
  selectedId: string | null;
  onSelect: (sessionId: string) => void;
  onClear: () => void;
}

/**
 * Les sessions correspondant à une sélection faite dans un graphique.
 *
 * L'énoncé demande qu'on puisse partir d'un graphique et retrouver les enregistrements.
 * C'est ici que ça se termine : la liste dit d'où vient la sélection, et combien de
 * sessions elle ne montre pas quand elle est plafonnée.
 */
export function SessionList({ listing, origin, selectedId, onSelect, onClear }: Props) {
  return (
    <section className="sessions" aria-label="Sessions sélectionnées">
      <header className="sessions__header">
        <h2>
          {listing.total} session{listing.total > 1 ? "s" : ""} — {origin}
        </h2>
        <button type="button" onClick={onClear}>
          Effacer la sélection
        </button>
      </header>

      {listing.truncated && (
        <p className="sessions__note">
          Les {listing.sessions.length} premières sont affichées. Affinez les filtres pour
          réduire le périmètre.
        </p>
      )}

      {listing.sessions.length === 0 ? (
        <p className="sessions__note">Aucune session dans cette sélection.</p>
      ) : (
        <table className="sessions__table">
          <thead>
            <tr>
              <th scope="col">Session</th>
              <th scope="col">Source</th>
              <th scope="col">Début</th>
              <th scope="col">Durée</th>
              <th scope="col">Appels modèle</th>
              <th scope="col">Appels outils</th>
              <th scope="col">Tokens en entrée</th>
            </tr>
          </thead>
          <tbody>
            {listing.sessions.map((session) => (
              <tr
                key={session.session_id}
                className={session.session_id === selectedId ? "sessions__row--selected" : ""}
              >
                <th scope="row">
                  <button type="button" onClick={() => onSelect(session.session_id)}>
                    {session.session_id}
                  </button>
                </th>
                <td>{session.source}</td>
                <td>{formatMoment(session.started_at)}</td>
                <td>{formatAggregate(session.duration)}</td>
                <td>{session.model_calls}</td>
                <td>{session.tool_calls}</td>
                <td>{formatAggregate(session.input_tokens)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </section>
  );
}
