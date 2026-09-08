import { Link } from "react-router-dom";

interface DrillDownPanelProps {
  label: string;
  sessionIds: string[];
  onClose: () => void;
  onApplyFilter: (sessionIds: string[]) => void;
}

/** Liste de sessions issues d'un clic sur un graphique. */
export function DrillDownPanel({ label, sessionIds, onClose, onApplyFilter }: DrillDownPanelProps) {
  if (sessionIds.length === 0) {
    return null;
  }

  return (
    <section className="drilldown" aria-label="Sessions correspondantes">
      <div className="drilldown__header">
        <h2 className="section-title">{label}</h2>
        <button type="button" className="btn btn--ghost" onClick={onClose}>
          Fermer
        </button>
      </div>

      <p className="drilldown__meta">{sessionIds.length} session(s) correspondante(s)</p>

      <div className="drilldown__actions">
        <button type="button" className="btn btn--primary" onClick={() => onApplyFilter(sessionIds)}>
          Filtrer le dashboard sur ces sessions
        </button>
      </div>

      <ul className="session-links">
        {sessionIds.map((sessionId) => (
          <li key={sessionId}>
            <Link to={`/sessions/${encodeURIComponent(sessionId)}`}>{sessionId}</Link>
          </li>
        ))}
      </ul>
    </section>
  );
}
