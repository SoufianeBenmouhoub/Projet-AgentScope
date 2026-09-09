import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError, apiGet, apiPostForm, apiPostJson } from "./client";

afterEach(() => {
  vi.unstubAllGlobals();
});

function stubResponse(response: Partial<Response> & { json?: () => Promise<unknown> }) {
  const mock = vi.fn().mockResolvedValue(response);
  vi.stubGlobal("fetch", mock);
  return mock;
}

describe("apiGet", () => {
  it("renvoie le corps décodé", async () => {
    stubResponse({ ok: true, json: async () => ({ version: "0.1.0" }) });

    await expect(apiGet<{ version: string }>("/api/v1/system/status")).resolves.toEqual({
      version: "0.1.0",
    });
  });

  it("échoue avec le statut plutôt que de renvoyer un corps vide", async () => {
    stubResponse({ ok: false, status: 500, json: async () => ({}) });

    await expect(apiGet("/api/v1/system/status")).rejects.toBeInstanceOf(ApiError);
  });
});

describe("apiPostJson", () => {
  it("remonte le message d'erreur de l'API quand il y en a un", async () => {
    stubResponse({ ok: false, status: 422, json: async () => ({ detail: "Mapping invalide." }) });

    await expect(apiPostJson("/api/v1/mapping/propose", {})).rejects.toThrow("Mapping invalide.");
  });

  it("remonte le premier message d'une erreur de validation détaillée", async () => {
    stubResponse({
      ok: false,
      status: 422,
      json: async () => ({ detail: [{ msg: "Champ requis manquant." }] }),
    });

    await expect(apiPostJson("/api/v1/mapping/propose", {})).rejects.toThrow(
      "Champ requis manquant.",
    );
  });

  it("se rabat sur le statut quand le corps n'est pas exploitable", async () => {
    stubResponse({
      ok: false,
      status: 500,
      json: async () => {
        throw new Error("corps non JSON");
      },
    });

    await expect(apiPostJson("/api/v1/mapping/propose", {})).rejects.toThrow("500");
  });
});

describe("apiPostForm", () => {
  it("envoie le formulaire sans forcer d'en-tête de type de contenu", async () => {
    const fetchMock = stubResponse({ ok: true, json: async () => ({ id: "1" }) });
    const form = new FormData();

    await apiPostForm("/api/v1/imports", form);

    const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(init.body).toBe(form);
    expect(init.headers).toBeUndefined();
  });
});
