import { screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { renderWithProviders } from "../../test/renderWithProviders";
import { SystemStatusCard } from "./SystemStatusCard";

function stubFetch(body: unknown, { ok = true }: { ok?: boolean } = {}) {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({ ok, json: async () => body }),
  );
}

describe("SystemStatusCard", () => {
  it("affiche l'état renvoyé par l'API", async () => {
    stubFetch({ version: "0.1.0", database: "ok", operational: true });

    renderWithProviders(<SystemStatusCard />);

    await waitFor(() => {
      expect(screen.getByText(/opérationnelle/i)).toBeTruthy();
    });
  });

  it("signale l'indisponibilité au lieu d'afficher un état par défaut", async () => {
    stubFetch({}, { ok: false });

    renderWithProviders(<SystemStatusCard />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeTruthy();
    });
  });
});
