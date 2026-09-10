import type { MappingPreview } from "../../../shared/api/types";

interface Props {
  outcome: MappingPreview;
}

/**
 * Ce que l'import produirait avec le mapping en cours, sans l'avoir lancé.
 *
 * Deux lectures y répondent à deux questions différentes : le bandeau dit **ce qui sortira**
 * (sessions, appels, refus), le tableau dit **d'où ça vient** (les valeurs réellement lues,
 * champ par champ). Un chemin qui pointe à côté rend une colonne vide ; un chemin qui pointe
 * sur la mauvaise colonne rend des valeurs qui ne ressemblent pas à ce qu'on attend. Aucun
 * compteur ne montre la seconde erreur — seules les valeurs le font.
 */
export function MappingOutcomeTable({ outcome }: Props) {
  return (
    <section className="mapping-outcome" aria-label="Résultat de l'essai à blanc">
      <h3 className="mapping__subtitle">Sur l'échantillon de {outcome.records} enregistrement(s)</h3>

      <dl className="detail-grid">
        <div>
          <dt>Sessions</dt>
          <dd>{outcome.sessions}</dd>
        </div>
        <div>
          <dt>Appels au modèle</dt>
          <dd>{outcome.model_calls}</dd>
        </div>
        <div>
          <dt>Appels d'outils</dt>
          <dd>{outcome.tool_calls}</dd>
        </div>
        <div>
          <dt>Refusés</dt>
          <dd className={outcome.rejected > 0 ? "quality__missing" : undefined}>
            {outcome.rejected}
          </dd>
        </div>
      </dl>

      {outcome.rejected > 0 && (
        <p className="status-message status-message--error" role="alert">
          {outcome.rejected} enregistrement(s) de l'échantillon n'entreraient pas en base.
        </p>
      )}

      {outcome.issues.length > 0 && (
        <>
          <h3 className="mapping__subtitle">Anomalies rencontrées</h3>
          <ul className="mapping__issues">
            {outcome.issues.map((issue) => (
              <li key={issue}>{issue}</li>
            ))}
          </ul>
        </>
      )}

      <div className="mapping__table-wrap">
        <table className="mapping__table">
          <thead>
            <tr>
              <th scope="col">Champ du modèle</th>
              <th scope="col">Lu depuis</th>
              <th scope="col">Renseigné</th>
              <th scope="col">Valeurs lues</th>
            </tr>
          </thead>
          <tbody>
            {outcome.fields.map((field) => (
              <tr key={field.target_field}>
                <th scope="row">{field.target_field}</th>
                <td>{field.path ?? <span className="quality__missing">non mappé</span>}</td>
                <td>
                  {field.path === null ? (
                    "—"
                  ) : (
                    <span className={field.resolved === 0 ? "quality__missing" : undefined}>
                      {field.resolved}/{field.total}
                    </span>
                  )}
                </td>
                <td className="mapping__values">
                  {field.examples.length > 0 ? field.examples.join(" · ") : "—"}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <p className="mapping__lead">
        « 0/N » sur un champ mappé veut dire que le chemin ne mène nulle part dans
        l'échantillon. Un champ non mappé restera vide en base — ce qui est une réponse
        valable quand la source ne publie pas la mesure.
      </p>
    </section>
  );
}
