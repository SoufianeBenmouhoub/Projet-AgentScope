import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import type {
  ImportPreviewResponse,
  MappingContract,
  MappingPreview,
  MappingProposal,
  SavedMappingList,
} from "../../../shared/api/types";
import { renderWithProviders } from "../../../test/renderWithProviders";
import { stubFetch } from "../../../test/stubFetch";
import { MappingEditor } from "./MappingEditor";

const FIELDS = "/api/v1/mapping/fields";
const PROPOSE = "/api/v1/mapping/propose";
const PREVIEW = "/api/v1/mapping/preview";
const LIBRARY = "/api/v1/mappings";

const CONTRACT: MappingContract = {
  fields: [
    { key: "session_id", scope: "session", description: "Identifiant de session.", required: true },
    { key: "agent", scope: "session", description: "Nom de l'agent.", required: false },
    { key: "tools", scope: "collection", description: "Tableau des outils.", required: false },
    { key: "tool_name", scope: "tool_call", description: "Nom de l'outil.", required: false },
  ],
};

const A_PREVIEW: ImportPreviewResponse = {
  filename: "extrait.jsonl",
  format: "jsonl",
  row_count_sample: 2,
  columns: ["sid", "provider", "outils"],
  sample_rows: [
    { sid: "s1", provider: "claude" },
    { sid: "s2", provider: "codex" },
  ],
};

const A_PROPOSAL: MappingProposal = {
  mappings: [
    { target_field: "session_id", source_field: "sid", confidence: 0.95, note: "Nom proche" },
    { target_field: "agent", source_field: "provider", confidence: 0.8, note: "Valeurs d'agents" },
  ],
  unresolved_notes: ["tools : cette source ne publie pas d'appels d'outils"],
};

const AN_OUTCOME: MappingPreview = {
  fields: [
    {
      target_field: "session_id",
      path: "sid",
      scope: "session",
      required: true,
      examples: ["s1", "s2"],
      resolved: 2,
      total: 2,
    },
    {
      target_field: "agent",
      path: "absent",
      scope: "session",
      required: false,
      examples: [],
      resolved: 0,
      total: 2,
    },
  ],
  records: 2,
  sessions: 2,
  model_calls: 2,
  tool_calls: 0,
  issues: ["input_tokens : « douze » n'est pas un nombre entier."],
  rejected: 1,
};

const EMPTY_LIBRARY: SavedMappingList = { mappings: [] };

function stubMapping(overrides: Partial<Record<string, unknown>> = {}) {
  return stubFetch([
    { match: FIELDS, body: overrides.contract ?? CONTRACT },
    { match: PROPOSE, body: overrides.proposal ?? A_PROPOSAL },
    { match: PREVIEW, body: overrides.outcome ?? AN_OUTCOME },
    // La bibliothèque en dernier : « /api/v1/mapping… » est plus spécifique.
    { match: LIBRARY, body: overrides.library ?? EMPTY_LIBRARY },
  ]);
}

function renderEditor(onReady = vi.fn()) {
  renderWithProviders(<MappingEditor preview={A_PREVIEW} onReady={onReady} />);
  return onReady;
}

async function inputFor(key: string) {
  return await screen.findByLabelText(`Champ du fichier pour ${key}`);
}

describe("MappingEditor — le contrat vient du serveur", () => {
  it("affiche un champ de saisie par champ du modèle commun", async () => {
    stubMapping();
    renderEditor();

    for (const field of CONTRACT.fields) {
      expect(await inputFor(field.key)).toBeTruthy();
    }
  });

  it("signale les champs obligatoires et leur définition", async () => {
    stubMapping();
    renderEditor();

    expect(await screen.findByText("(obligatoire)")).toBeTruthy();
    expect(screen.getByText("Identifiant de session.")).toBeTruthy();
  });

  it("annonce l'échec plutôt que d'afficher un formulaire vide", async () => {
    // Un formulaire sans champs ressemblerait à un modèle sans champs.
    stubFetch([{ match: FIELDS, body: { detail: "panne" }, ok: false }, { match: LIBRARY, body: EMPTY_LIBRARY }]);
    renderEditor();

    expect(await screen.findByRole("alert")).toBeTruthy();
  });
});

describe("MappingEditor — l'agent propose, l'utilisateur corrige", () => {
  it("remplit les champs à partir de la proposition", async () => {
    stubMapping();
    renderEditor();

    await userEvent.click(await screen.findByRole("button", { name: /proposer avec l'ia/i }));

    await waitFor(async () => {
      expect(((await inputFor("session_id")) as HTMLInputElement).value).toBe("sid");
    });
    expect(((await inputFor("agent")) as HTMLInputElement).value).toBe("provider");
  });

  it("montre ce que l'agent n'a pas su rapprocher", async () => {
    stubMapping();
    renderEditor();

    await userEvent.click(await screen.findByRole("button", { name: /proposer avec l'ia/i }));

    expect(
      await screen.findByText(/cette source ne publie pas d'appels d'outils/i),
    ).toBeTruthy();
  });

  it("laisse corriger une correspondance proposée", async () => {
    // C'est tout l'intérêt : l'agent propose, il ne décide pas.
    stubMapping();
    const onReady = renderEditor();

    await userEvent.click(await screen.findByRole("button", { name: /proposer avec l'ia/i }));
    const input = await inputFor("agent");
    await waitFor(() => expect((input as HTMLInputElement).value).toBe("provider"));

    await userEvent.clear(input);
    await userEvent.type(input, "autre_colonne");

    await waitFor(() => {
      const last = onReady.mock.calls.at(-1)?.[0];
      expect(last?.agent).toBe("autre_colonne");
    });
  });

  it("un fournisseur injoignable est signalé sans effacer la saisie", async () => {
    stubFetch([
      { match: FIELDS, body: CONTRACT },
      { match: PROPOSE, body: { detail: "Le fournisseur Anthropic n'a pas répondu." }, ok: false },
      { match: LIBRARY, body: EMPTY_LIBRARY },
    ]);
    renderEditor();

    const input = await inputFor("session_id");
    await userEvent.type(input, "sid");
    await userEvent.click(screen.getByRole("button", { name: /proposer avec l'ia/i }));

    expect(await screen.findByText(/n'a pas répondu/i)).toBeTruthy();
    expect((input as HTMLInputElement).value).toBe("sid");
  });
});

describe("MappingEditor — ce qui empêche d'importer", () => {
  it("refuse de remonter un mapping sans son champ obligatoire", async () => {
    stubMapping();
    const onReady = renderEditor();

    expect(await screen.findByText(/champs obligatoires non renseignés/i)).toBeTruthy();
    expect(onReady.mock.calls.at(-1)?.[0]).toBeNull();
  });

  it("remonte le mapping dès que l'obligatoire est renseigné", async () => {
    stubMapping();
    const onReady = renderEditor();

    await userEvent.type(await inputFor("session_id"), "sid");

    await waitFor(() => {
      expect(onReady.mock.calls.at(-1)?.[0]).toMatchObject({ session_id: "sid" });
    });
  });

  it("signale un champ d'outil sans le tableau qui le contient", async () => {
    stubMapping();
    renderEditor();

    await userEvent.type(await inputFor("session_id"), "sid");
    await userEvent.type(await inputFor("tool_name"), "nom");

    expect(await screen.findByText(/« tools » ne dit pas où les trouver/i)).toBeTruthy();
  });

  it("un champ laissé vide part en absence, pas en chaîne vide", async () => {
    stubMapping();
    const onReady = renderEditor();

    await userEvent.type(await inputFor("session_id"), "sid");

    await waitFor(() => {
      expect(onReady.mock.calls.at(-1)?.[0]?.agent).toBeNull();
    });
  });
});

describe("MappingEditor — l'essai à blanc", () => {
  async function runPreview() {
    stubMapping();
    renderEditor();
    await userEvent.type(await inputFor("session_id"), "sid");
    await userEvent.click(screen.getByRole("button", { name: /vérifier sur l'échantillon/i }));
  }

  it("montre ce que l'import produirait", async () => {
    await runPreview();

    const outcome = await screen.findByLabelText("Résultat de l'essai à blanc");
    expect(within(outcome).getByText("Sessions")).toBeTruthy();
    expect(within(outcome).getByText(/2 enregistrement/i)).toBeTruthy();
  });

  it("montre les valeurs réellement lues, champ par champ", async () => {
    // Un chemin qui pointe sur la mauvaise colonne rend des valeurs qui ne ressemblent pas
    // à ce qu'on attend — ce qu'aucun compteur ne montre.
    await runPreview();

    expect(await screen.findByText("s1 · s2")).toBeTruthy();
  });

  it("signale un chemin qui ne mène nulle part", async () => {
    await runPreview();

    expect(await screen.findByText("0/2")).toBeTruthy();
  });

  it("annonce les enregistrements qui seraient refusés", async () => {
    await runPreview();

    expect(await screen.findByText(/n'entreraient pas en base/i)).toBeTruthy();
  });
});

describe("MappingEditor — la bibliothèque", () => {
  it("enregistre le mapping sous le nom saisi", async () => {
    const fetchMock = stubMapping();
    renderEditor();

    await userEvent.type(await inputFor("session_id"), "sid");
    await userEvent.type(screen.getByLabelText(/nom du mapping/i), "TraceLab");
    await userEvent.click(screen.getByRole("button", { name: /enregistrer ce mapping/i }));

    await waitFor(() => expect(screen.getByText(/enregistré/i)).toBeTruthy());

    // La bibliothèque est aussi lue en GET sur la même URL : on cherche l'écriture.
    const call = fetchMock.mock.calls.find(
      ([url, init]) => String(url).endsWith("/api/v1/mappings") && init?.method === "POST",
    );
    const body = JSON.parse(String(call?.[1]?.body));
    expect(body).toMatchObject({ name: "TraceLab", mapping: { session_id: "sid", agent: null } });
  });

  it("refuse d'enregistrer sans nom", async () => {
    stubMapping();
    renderEditor();

    await userEvent.type(await inputFor("session_id"), "sid");

    expect(
      screen.getByRole("button", { name: /enregistrer ce mapping/i }).hasAttribute("disabled"),
    ).toBe(true);
  });

  it("recharge un mapping enregistré dans le formulaire", async () => {
    stubMapping({
      library: {
        mappings: [
          {
            id: "m1",
            name: "TraceLab",
            source_name: "tracelab",
            mapping: { session_id: "session_id", agent: "provider", tools: null, tool_name: null },
            created_at: "2026-09-11T09:00:00Z",
            updated_at: "2026-09-11T09:00:00Z",
          },
        ],
      },
    });
    renderEditor();

    await userEvent.selectOptions(
      await screen.findByLabelText(/mapping enregistré/i),
      "m1",
    );

    await waitFor(async () => {
      expect(((await inputFor("session_id")) as HTMLInputElement).value).toBe("session_id");
    });
    expect(((await inputFor("agent")) as HTMLInputElement).value).toBe("provider");
  });

  it("sans mapping enregistré, aucun sélecteur n'est proposé", async () => {
    stubMapping();
    renderEditor();

    await screen.findByLabelText("Champ du fichier pour session_id");
    expect(screen.queryByLabelText(/mapping enregistré/i)).toBeNull();
  });
});
