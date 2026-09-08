import type { Indicator } from "../../shared/api/types";
import { coverageNote, formatAggregate, UNAVAILABLE } from "./formatting";

/**
 * Un indicateur, indissociable de sa définition.
 *
 * L'énoncé demande que chaque indicateur ait une définition accessible : calcul, unité,
 * périmètre et traitement des valeurs manquantes. Elle est donc dépliable ici, à côté du
 * chiffre — pas reléguée dans un document que personne n'ouvrira.
 */
export function IndicatorCard({ indicator }: { indicator: Indicator }) {
  const { definition, aggregate } = indicator;
  const value = formatAggregate(aggregate);
  const note = coverageNote(aggregate);
  const unavailable = value === UNAVAILABLE;

  return (
    <article className="indicator" aria-labelledby={`indicator-${definition.key}`}>
      <h3 className="indicator__label" id={`indicator-${definition.key}`}>
        {definition.label}
      </h3>

      <p className={unavailable ? "indicator__value indicator__value--unavailable" : "indicator__value"}>
        {value}
      </p>

      {indicator.mixes_incomparable_sources && (
        <p className="indicator__warning" role="note">
          Cet indicateur agrège {indicator.sources.length} sources qui ne le mesurent pas de la
          même façon. Filtrez par source pour obtenir un chiffre comparable.
        </p>
      )}

      {note && <p className="indicator__note">{note}</p>}

      <details className="indicator__definition">
        <summary>Définition</summary>
        <dl>
          <dt>Calcul</dt>
          <dd>{definition.computation}</dd>
          <dt>Unité</dt>
          <dd>{definition.unit}</dd>
          <dt>Périmètre</dt>
          <dd>{definition.scope}</dd>
          <dt>Valeurs manquantes</dt>
          <dd>{definition.missing_values}</dd>
        </dl>
      </details>
    </article>
  );
}
