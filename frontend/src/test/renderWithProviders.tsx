import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import type { ReactElement } from "react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";

/**
 * Monte un composant avec les fournisseurs de l'application.
 *
 * Un client de requêtes neuf par test : pas de cache partagé entre deux cas, et les
 * réessais sont désactivés pour qu'un test d'erreur ne mette pas trois secondes.
 */
export function renderWithProviders(ui: ReactElement) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  return render(<QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>);
}

/** Monte un arbre routé en mémoire — pour tester navigation et pages. */
export function renderWithRouter(routes: Parameters<typeof createMemoryRouter>[0]) {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  const router = createMemoryRouter(routes, { initialEntries: ["/"] });

  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
}
