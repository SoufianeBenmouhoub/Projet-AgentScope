import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it } from "vitest";

import { anImportRecord } from "../../test/builders";
import { renderWithProviders } from "../../test/renderWithProviders";
import { stubFetch } from "../../test/stubFetch";
import { ImportPage } from "./ImportPage";

const CONTRACT = {
  fields: [
    { key: "session_id", scope: "session", description: "Identifiant.", required: true },
    { key: "agent", scope: "session", description: "Agent.", required: false },
  ],
};

const A_PREVIEW = {
  filename: "extrait.jsonl",
  format: "jsonl",
  row_count_sample: 1,
  columns: ["sid", "provider"],
  sample_rows: [{ sid: "s1", provider: "claude" }],
};

function stubImportScreen() {
  return stubFetch([
    { match: "/api/v1/imports/preview", body: A_PREVIEW },
    { match: "/api/v1/imports", body: { imports: [] } },
    { match: "/api/v1/mapping/fields", body: CONTRACT },
    { match: "/api/v1/mappings", body: { mappings: [] } },
  ]);
}

async function chooseFile() {
  const file = new File(['{"sid": "s1"}'], "extrait.jsonl", { type: "application/x-ndjson" });
  await userEvent.upload(document.querySelector("#import-file") as HTMLInputElement, file);
  await userEvent.click(screen.getByRole("button", { name: /prévisualiser/i }));
}

describe("ImportPage", () => {
  it("n'offre pas d'importer avant d'avoir choisi un fichier", () => {
    stubImportScreen();
    renderWithProviders(<ImportPage />);

    expect(screen.getByRole("button", { name: /^importer$/i }).hasAttribute("disabled")).toBe(true);
  });

  it("ouvre la mise au point du mapping après l'aperçu", async () => {
    stubImportScreen();
    renderWithProviders(<ImportPage />);

    await chooseFile();

    expect(await screen.findByLabelText("Mise au point du mapping")).toBeTruthy();
  });

  it("refuse d'importer tant que le mapping est incomplet", async () => {
    stubImportScreen();
    renderWithProviders(<ImportPage />);

    await chooseFile();
    await screen.findByLabelText("Mise au point du mapping");

    await waitFor(() => {
      expect(screen.getByRole("button", { name: /^importer$/i }).hasAttribute("disabled")).toBe(
        true,
      );
    });
    expect(screen.getByText(/complétez les champs obligatoires/i)).toBeTruthy();
  });

  it("envoie le mapping validé avec le fichier", async () => {
    // C'est le point de jonction de tout le parcours : ce que l'utilisateur a corrigé et
    // vérifié doit être ce que le serveur reçoit.
    const fetchMock = stubFetch([
      { match: "/api/v1/imports/preview", body: A_PREVIEW },
      { match: "/api/v1/mapping/fields", body: CONTRACT },
      { match: "/api/v1/mappings", body: { mappings: [] } },
      { match: "/api/v1/imports", body: anImportRecord(), method: "POST" },
      { match: "/api/v1/imports", body: { imports: [] } },
    ]);
    renderWithProviders(<ImportPage />);

    await userEvent.type(screen.getByLabelText(/nom de la source/i), "tracelab");
    await chooseFile();
    await userEvent.type(await screen.findByLabelText("Champ du fichier pour session_id"), "sid");
    await userEvent.type(screen.getByLabelText("Champ du fichier pour agent"), "provider");

    const button = screen.getByRole("button", { name: /^importer$/i });
    await waitFor(() => expect(button.hasAttribute("disabled")).toBe(false));
    await userEvent.click(button);

    await waitFor(() => {
      const call = fetchMock.mock.calls.find(
        ([url, init]) => String(url).endsWith("/api/v1/imports") && init?.method === "POST",
      );
      expect(call).toBeTruthy();

      const form = call?.[1]?.body as FormData;
      expect(form.get("source_name")).toBe("tracelab");
      expect(JSON.parse(String(form.get("mapping")))).toEqual({
        session_id: "sid",
        agent: "provider",
      });
    });
  });
});
