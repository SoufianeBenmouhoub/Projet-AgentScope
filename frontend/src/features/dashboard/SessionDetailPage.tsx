import { Link, useParams } from "react-router-dom";

import { useSessionDetail } from "./api";
import "./dashboard.css";
import { SessionDetail } from "./sessions/SessionDetail";

/**
 * La page d'une session, atteignable par son URL.
 *
 * Elle ne réimplémente rien : elle résout l'identifiant de la route et confie l'affichage
 * au composant déjà utilisé dans le tableau de bord. Une session est ainsi lisible de deux
 * façons — en restant sur le dashboard après un clic dans un graphique, ou par un lien
 * direct qu'on peut partager.
 */
export function SessionDetailPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const { data, isPending, isError } = useSessionDetail(sessionId ?? null);

  if (!sessionId) {
    return <p role="alert">Identifiant de session manquant dans l'adresse.</p>;
  }

  if (isPending) {
    return <p>Chargement de la session…</p>;
  }

  if (isError || !data) {
    return (
      <section>
        <p role="alert">Session introuvable, ou API indisponible.</p>
        <Link to="/">← Retour au tableau de bord</Link>
      </section>
    );
  }

  return (
    <section>
      <p>
        <Link to="/">← Retour au tableau de bord</Link>
      </p>
      <SessionDetail detail={data} />
    </section>
  );
}
