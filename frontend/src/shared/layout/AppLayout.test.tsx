import { cleanup, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";
import { createMemoryRouter, RouterProvider } from "react-router-dom";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

import { DashboardPage } from "../../features/dashboard/DashboardPage";
import { ImportPage } from "../../features/import/ImportPage";
import { SystemPage } from "../../features/system/SystemPage";
import { AppLayout } from "./AppLayout";

const testRoutes = [
  {
    path: "/",
    element: <AppLayout />,
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "import", element: <ImportPage /> },
      { path: "system", element: <SystemPage /> },
    ],
  },
];

function renderApp(initialEntry = "/") {
  const queryClient = new QueryClient({
    defaultOptions: { queries: { retry: false } },
  });

  const router = createMemoryRouter(testRoutes, { initialEntries: [initialEntry] });

  return render(
    <QueryClientProvider client={queryClient}>
      <RouterProvider router={router} />
    </QueryClientProvider>,
  );
}

describe("AppLayout", () => {
  afterEach(() => {
    cleanup();
  });

  it("affiche la navigation et le contenu de la route active", () => {
    renderApp();

    expect(screen.getByRole("navigation", { name: /navigation principale/i })).toBeTruthy();
    expect(screen.getByRole("heading", { level: 1, name: /tableau de bord/i })).toBeTruthy();
  });

  it("montre la page import sur la route /import", () => {
    renderApp("/import");
    expect(screen.getByRole("heading", { level: 1, name: /^import$/i })).toBeTruthy();
    expect(screen.getByRole("heading", { name: /nouvel import/i })).toBeTruthy();
    expect(screen.getByLabelText(/téléversement de fichier/i)).toBeTruthy();
  });

  it("montre la page système sur la route /system", () => {
    renderApp("/system");
    expect(screen.getByRole("heading", { level: 1, name: /^système$/i })).toBeTruthy();
  });
});
