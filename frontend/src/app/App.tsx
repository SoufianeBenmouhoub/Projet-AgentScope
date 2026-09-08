import { DashboardPage } from "../features/dashboard/DashboardPage";
import { SystemStatusCard } from "../features/system/SystemStatusCard";

/**
 * Coquille de l'application.
 *
 * Point d'entrée du **lot 6** : navigation, mise en page, et raccordement des écrans
 * d'import et de mapping. En attendant le routage, le dashboard est monté directement ici.
 */
export function App() {
  return (
    <main>
      <h1>AgentScope</h1>
      <p>Importer, vérifier, normaliser, explorer des traces d'agents de développement IA.</p>
      <DashboardPage />
      <SystemStatusCard />
    </main>
  );
}
