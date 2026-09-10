import { useQuery } from "@tanstack/react-query";

import { fetchImportDetail, fetchImportHistory } from "../../../shared/api/imports";

/**
 * Ce que le dernier import a refusé, et pourquoi.
 *
 * Le tableau de bord montre ce qui est entré en base. Sans cette section, ce qui n'y est
 * pas entré resterait invisible : des chiffres justes, calculés sur un fichier amputé sans
 * que rien ne le dise. C'est exactement le genre de silence que ce projet s'interdit.
 *
 * Le composant lit lui-même l'historique plutôt que de recevoir le bilan en propriété : la
 * qualité des données ne dépend d'aucun filtre du tableau de bord, et faire redescendre
 * cette requête depuis la page coûterait plus qu'elle ne rapporte.
 */
export function LatestImportRejections() {
  const historyQuery = useQuery({
    queryKey: ["imports"],
    queryFn: fetchImportHistory,
    retry: false,
  });

  const latest = historyQuery.data?.imports[0];

  const detailQuery = useQuery({
    queryKey: ["imports", latest?.id],
    queryFn: () => fetchImportDetail(latest!.id),
    enabled: latest !== undefined,
    retry: false,
  });

  if (historyQuery.isPending) {
    return <p className="quality__note">Chargement du dernier import…</p>;
  }

  // Une erreur de chargement n'est pas une absence de rejet : les confondre afficherait
  // « aucun rejet » alors qu'on ne sait rien.
  if (historyQuery.isError) {
    return <p className="quality__note">Historique des imports indisponible.</p>;
  }

  if (latest === undefined) {
    return <p className="quality__note">Aucun import à ce jour.</p>;
  }

  if (detailQuery.isError) {
    return (
      <p className="quality__note">
        Détail des rejets de « {latest.filename} » indisponible — le nombre annoncé reste{" "}
        {latest.rejected_count}.
      </p>
    );
  }

  const rejections = detailQuery.data?.rejections ?? [];

  if (detailQuery.isPending) {
    return <p className="quality__note">Chargement des rejets de « {latest.filename} »…</p>;
  }

  if (rejections.length === 0) {
    return (
      <p className="quality__note">
        « {latest.filename} » — aucun enregistrement refusé sur {latest.records_imported}{" "}
        importés.
      </p>
    );
  }

  return (
    <>
      <p className="quality__note">
        « {latest.filename} » — {rejections.length}{" "}
        {rejections.length > 1 ? "enregistrements refusés" : "enregistrement refusé"}, pour{" "}
        {latest.records_imported} importés. Ils ne sont pas en base : les indicateurs ne les
        comptent pas.
      </p>
      <ul className="quality__list">
        {rejections.map((rejection) => (
          <li key={rejection.line_number}>
            <strong>Ligne {rejection.line_number}</strong> — {rejection.reason}
            {rejection.raw_preview !== null && (
              <pre className="quality__preview">{rejection.raw_preview}</pre>
            )}
          </li>
        ))}
      </ul>
    </>
  );
}
