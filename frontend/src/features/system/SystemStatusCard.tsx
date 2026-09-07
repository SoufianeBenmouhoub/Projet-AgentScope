import { useQuery } from "@tanstack/react-query";

import { apiGet } from "../../shared/api/client";
import type { SystemStatus } from "../../shared/api/types";

/**
 * Exemple de référence : un composant qui consomme l'API.
 *
 * À retenir pour les autres lots : les trois états — en cours, en erreur, chargé — sont
 * traités explicitement. Une information indisponible s'affiche comme indisponible, jamais
 * comme une valeur par défaut.
 */
export function SystemStatusCard() {
  const { data, isPending, isError } = useQuery({
    queryKey: ["system", "status"],
    queryFn: () => apiGet<SystemStatus>("/api/v1/system/status"),
  });

  if (isPending) {
    return <p>Vérification de l'état du système…</p>;
  }

  if (isError) {
    return <p role="alert">État du système indisponible : l'API ne répond pas.</p>;
  }

  return (
    <section>
      <h2>État du système</h2>
      <p>
        {data.operational
          ? "L'application est opérationnelle."
          : "L'application est démarrée mais son stockage est injoignable."}
      </p>
      <dl>
        <dt>Version</dt>
        <dd>{data.version}</dd>
        <dt>Stockage</dt>
        <dd>{data.database === "ok" ? "joignable" : "injoignable"}</dd>
      </dl>
    </section>
  );
}
