import { SystemStatusCard } from "./SystemStatusCard";

/** État du système et santé du stockage. */
export function SystemPage() {
  return (
    <section className="page">
      <header className="page__header">
        <h1>Système</h1>
        <p className="page__lead">Version de l'application et disponibilité du stockage.</p>
      </header>

      <SystemStatusCard />
    </section>
  );
}
