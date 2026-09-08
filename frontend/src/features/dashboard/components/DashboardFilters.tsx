import type { TraceFilters } from "../../../shared/api/types";
import { EMPTY_TRACE_FILTERS } from "../utils/filters";

interface DashboardFiltersProps {
  filters: TraceFilters;
  onChange: (filters: TraceFilters) => void;
  onReset: () => void;
}

function joinList(values: string[]): string {
  return values.join(", ");
}

function parseListInput(raw: string): string[] {
  return raw
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

/** Barre de filtres synchronisée avec l'URL. */
export function DashboardFilters({ filters, onChange, onReset }: DashboardFiltersProps) {
  const updateField = (field: keyof TraceFilters, value: string | string[] | null) => {
    onChange({ ...filters, [field]: value });
  };

  return (
    <section className="filters" aria-label="Filtres du dashboard">
      <div className="filters__header">
        <h2 className="section-title">Filtres</h2>
        <button type="button" className="btn btn--ghost" onClick={onReset}>
          Réinitialiser
        </button>
      </div>

      <div className="filters__grid">
        <label className="field">
          <span className="field__label">Sources</span>
          <input
            className="field__input"
            type="text"
            placeholder="traces_lab, swe_chat…"
            value={joinList(filters.sources)}
            onChange={(event) => updateField("sources", parseListInput(event.target.value))}
          />
        </label>

        <label className="field">
          <span className="field__label">Agents</span>
          <input
            className="field__input"
            type="text"
            placeholder="claude_code, codex…"
            value={joinList(filters.agents)}
            onChange={(event) => updateField("agents", parseListInput(event.target.value))}
          />
        </label>

        <label className="field">
          <span className="field__label">Modèles</span>
          <input
            className="field__input"
            type="text"
            placeholder="claude-3-5-sonnet…"
            value={joinList(filters.models)}
            onChange={(event) => updateField("models", parseListInput(event.target.value))}
          />
        </label>

        <label className="field">
          <span className="field__label">Depuis</span>
          <input
            className="field__input"
            type="date"
            value={filters.since ?? ""}
            onChange={(event) => updateField("since", event.target.value || null)}
          />
        </label>

        <label className="field">
          <span className="field__label">Jusqu'au</span>
          <input
            className="field__input"
            type="date"
            value={filters.until ?? ""}
            onChange={(event) => updateField("until", event.target.value || null)}
          />
        </label>
      </div>

      {filters.sessionIds.length > 0 && (
        <p className="filters__active">
          Filtre actif : {filters.sessionIds.length} session(s) sélectionnée(s) depuis un
          graphique.{" "}
          <button
            type="button"
            className="btn btn--link"
            onClick={() => onChange({ ...filters, sessionIds: EMPTY_TRACE_FILTERS.sessionIds })}
          >
            Effacer la sélection
          </button>
        </p>
      )}
    </section>
  );
}
