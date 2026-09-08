import type { ReactNode } from "react";

interface Props {
  title: string;
  note?: ReactNode;
  /** Le tableau équivalent au graphique. Toute valeur lisible dans le graphique s'y retrouve. */
  table: ReactNode;
  /** Estompe le contenu pendant un rechargement, sans le remplacer par un squelette. */
  refreshing?: boolean;
  children: ReactNode;
}

/**
 * Le cadre commun à tous les graphiques.
 *
 * Deux règles qu'il fait respecter partout :
 *
 * - **chaque graphique a son équivalent en tableau.** Une infobulle enrichit la lecture,
 *   elle ne doit jamais être le seul moyen d'atteindre une valeur — ni pour quelqu'un au
 *   clavier, ni pour quelqu'un qui distingue mal deux couleurs ;
 * - **pas de squelette au rechargement.** Le rendu précédent reste affiché, estompé : le
 *   contenu ne saute pas quand on change un filtre.
 */
export function ChartCard({ title, note, table, refreshing = false, children }: Props) {
  return (
    <figure className="chart">
      <figcaption className="chart__title">{title}</figcaption>

      <div className="chart__plot" style={{ opacity: refreshing ? 0.6 : 1 }}>
        {children}
      </div>

      {note && <p className="chart__note">{note}</p>}

      <details className="chart__table">
        <summary>Voir les données</summary>
        {table}
      </details>
    </figure>
  );
}
