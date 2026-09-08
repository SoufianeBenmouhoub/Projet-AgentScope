import { NavLink, Outlet } from "react-router-dom";

const navItems = [
  { to: "/", label: "Dashboard", end: true },
  { to: "/import", label: "Import" },
  { to: "/system", label: "Système" },
] as const;

/**
 * Mise en page commune : barre latérale, zone de contenu, pied de page.
 *
 * Chaque écran se monte dans `<Outlet />` sans dupliquer la navigation.
 */
export function AppLayout() {
  return (
    <div className="app-shell">
      <aside className="app-sidebar">
        <div className="app-brand">
          <span className="app-brand__mark" aria-hidden="true">
            AS
          </span>
          <div>
            <p className="app-brand__title">AgentScope</p>
            <p className="app-brand__tagline">Traces d'agents IA</p>
          </div>
        </div>

        <nav className="app-nav" aria-label="Navigation principale">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              end={"end" in item ? item.end : undefined}
              className={({ isActive }) =>
                isActive ? "app-nav__link app-nav__link--active" : "app-nav__link"
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </aside>

      <div className="app-main">
        <header className="app-header">
          <p className="app-header__subtitle">
            Importer, vérifier, normaliser, explorer des traces d'agents de développement IA.
          </p>
        </header>

        <main className="app-content">
          <Outlet />
        </main>

        <footer className="app-footer">
          <span>AgentScope v0.1.0</span>
        </footer>
      </div>
    </div>
  );
}
