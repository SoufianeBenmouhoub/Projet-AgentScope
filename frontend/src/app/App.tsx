import { SystemStatusCard } from "../features/system/SystemStatusCard";

/**
 * Coquille de l'application.
 *
 * Point d'entrée du **lot 6** : navigation, mise en page, et raccordement des écrans
 * d'import et de mapping. Le dashboard (lot 5) viendra se monter sous sa propre route.
 */
export function App() {
  return (
    <main>
      <h1>AgentScope</h1>
      <p>Importer, vérifier, normaliser, explorer des traces d'agents de développement IA.</p>
      <SystemStatusCard />
    </main>
  );
}
