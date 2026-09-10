import { screen, waitFor } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { ImportPreviewResponse } from "../../../shared/api/types";
import { renderWithProviders } from "../../../test/renderWithProviders";
import { stubFetch } from "../../../test/stubFetch";
import { MappingEditor } from "./MappingEditor";

/** Le contrat réel du domaine, dans l'ordre exact où le serveur le publie. */
const CONTRACT_KEYS = [
  "session_id",
  "agent",
  "session_status",
  "occurred_at",
  "ended_at",
  "model",
  "input_tokens",
  "output_tokens",
  "cache_creation_tokens",
  "model_call_id",
  "tools",
  "tool_name",
  "tool_started_at",
  "tool_ended_at",
  "tool_is_error",
  "tool_error",
  "tool_call_id",
];

/** Les portées réelles, telles que `domain/mapping/contract.py` les déclare. */
const SCOPES: Record<string, string> = {
  session_id: "session",
  agent: "session",
  session_status: "session",
  occurred_at: "model_call",
  ended_at: "model_call",
  model: "model_call",
  input_tokens: "model_call",
  output_tokens: "model_call",
  cache_creation_tokens: "model_call",
  model_call_id: "model_call",
  tools: "collection",
  tool_name: "tool_call",
  tool_started_at: "tool_call",
  tool_ended_at: "tool_call",
  tool_is_error: "tool_call",
  tool_error: "tool_call",
  tool_call_id: "tool_call",
};

const CONTRACT = {
  fields: CONTRACT_KEYS.map((key) => ({
    key,
    scope: SCOPES[key],
    description: `Description de ${key}.`,
    required: key === "session_id",
  })),
};

const A_PREVIEW: ImportPreviewResponse = {
  filename: "extrait.jsonl",
  format: "jsonl",
  row_count_sample: 1,
  columns: ["sid"],
  sample_rows: [{ sid: "s1" }],
};

describe("MappingEditor — toutes les lignes du contrat sont rendues", () => {
  it("affiche une ligne par champ, y compris les six derniers", async () => {
    stubFetch([
      { match: "/api/v1/mapping/fields", body: CONTRACT },
      { match: "/api/v1/mappings", body: { mappings: [] } },
    ]);

    renderWithProviders(<MappingEditor preview={A_PREVIEW} onReady={vi.fn()} />);

    await waitFor(() =>
      expect(screen.getByLabelText("Champ du fichier pour session_id")).toBeTruthy(),
    );

    for (const key of CONTRACT_KEYS) {
      expect(screen.getByLabelText(`Champ du fichier pour ${key}`)).toBeTruthy();
    }

    const rows = document.querySelectorAll(".mapping__table tbody tr:not(.mapping__group)");
    expect(rows.length).toBe(CONTRACT_KEYS.length);
  });

  it("regroupe les champs par portée, avec un titre et un compte", async () => {
    // Dix-sept champs à la suite forment une liste sans relief, où les six derniers se
    // retrouvent en bas sans que rien ne dise qu'ils forment un bloc.
    stubFetch([
      { match: "/api/v1/mapping/fields", body: CONTRACT },
      { match: "/api/v1/mappings", body: { mappings: [] } },
    ]);

    renderWithProviders(<MappingEditor preview={A_PREVIEW} onReady={vi.fn()} />);

    await waitFor(() =>
      expect(screen.getByLabelText("Champ du fichier pour session_id")).toBeTruthy(),
    );

    const titles = [...document.querySelectorAll(".mapping__group th")].map((cell) =>
      cell.textContent?.trim(),
    );

    expect(titles).toHaveLength(4);
    expect(titles[0]).toContain("Session");
    expect(titles[3]).toContain("Appel d'outil");
    expect(titles[3]).toContain("6 champs");
  });

  it("garde le tableau des outils juste avant les champs qu'il contient", async () => {
    // L'ordre est celui du remplissage : « tools » commande les six suivants.
    stubFetch([
      { match: "/api/v1/mapping/fields", body: CONTRACT },
      { match: "/api/v1/mappings", body: { mappings: [] } },
    ]);

    renderWithProviders(<MappingEditor preview={A_PREVIEW} onReady={vi.fn()} />);

    await waitFor(() =>
      expect(screen.getByLabelText("Champ du fichier pour session_id")).toBeTruthy(),
    );

    const keys = [...document.querySelectorAll(".mapping__key")].map((cell) => cell.textContent);

    expect(keys.indexOf("tools")).toBeLessThan(keys.indexOf("tool_name"));
    expect(keys.at(-1)).toBe("tool_call_id");
  });
});
