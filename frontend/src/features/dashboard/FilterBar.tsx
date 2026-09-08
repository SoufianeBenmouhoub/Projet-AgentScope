import type { FilterOptions } from "../../shared/api/types";
import { isUnfiltered, NO_FILTERS, toggle, type TraceFilters } from "./filters";

interface Props {
  options: FilterOptions;
  filters: TraceFilters;
  onChange: (filters: TraceFilters) => void;
}

/**
 * Les filtres du dashboard.
 *
 * Les choix proposés viennent des traces réellement importées, jamais d'une liste écrite
 * en dur : une source qui n'a jamais été importée n'apparaît pas.
 */
export function FilterBar({ options, filters, onChange }: Props) {
  if (options.is_empty) {
    return null;
  }

  return (
    <form className="filters" aria-label="Filtres du tableau de bord">
      <CheckboxGroup
        legend="Source"
        values={options.sources}
        selected={filters.sources}
        onToggle={(value) => onChange({ ...filters, sources: toggle(filters.sources, value) })}
      />

      <CheckboxGroup
        legend="Agent"
        values={options.agents}
        selected={filters.agents}
        onToggle={(value) => onChange({ ...filters, agents: toggle(filters.agents, value) })}
      />

      <CheckboxGroup
        legend="Modèle"
        values={options.models}
        selected={filters.models}
        onToggle={(value) => onChange({ ...filters, models: toggle(filters.models, value) })}
      />

      <fieldset className="filters__group">
        <legend>Période</legend>
        {options.first_day === null ? (
          <p className="filters__unavailable">
            Aucun enregistrement n'est horodaté : le filtre par période ne s'applique pas.
          </p>
        ) : (
          <div className="filters__period">
            <label>
              Du
              <input
                type="date"
                value={filters.since ?? ""}
                min={options.first_day ?? undefined}
                max={options.last_day ?? undefined}
                onChange={(event) =>
                  onChange({ ...filters, since: event.target.value || null })
                }
              />
            </label>
            <label>
              Au
              <input
                type="date"
                value={filters.until ?? ""}
                min={options.first_day ?? undefined}
                max={options.last_day ?? undefined}
                onChange={(event) =>
                  onChange({ ...filters, until: event.target.value || null })
                }
              />
            </label>
          </div>
        )}
      </fieldset>

      <button
        type="button"
        className="filters__reset"
        disabled={isUnfiltered(filters)}
        onClick={() => onChange(NO_FILTERS)}
      >
        Réinitialiser
      </button>
    </form>
  );
}

function CheckboxGroup({
  legend,
  values,
  selected,
  onToggle,
}: {
  legend: string;
  values: string[];
  selected: string[];
  onToggle: (value: string) => void;
}) {
  if (values.length === 0) {
    return null;
  }

  return (
    <fieldset className="filters__group">
      <legend>{legend}</legend>
      {values.map((value) => (
        <label key={value} className="filters__choice">
          <input
            type="checkbox"
            checked={selected.includes(value)}
            onChange={() => onToggle(value)}
          />
          {value}
        </label>
      ))}
    </fieldset>
  );
}
