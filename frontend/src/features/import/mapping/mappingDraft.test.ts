import { describe, expect, it } from "vitest";

import type { MappingProposal, TargetField } from "../../../shared/api/types";
import {
  applyProposal,
  emptyDraft,
  fromSaved,
  missingRequired,
  notesByField,
  toMapping,
  toolFieldsWithoutCollection,
} from "./mappingDraft";

const FIELDS: TargetField[] = [
  { key: "session_id", scope: "session", description: "Identifiant.", required: true },
  { key: "agent", scope: "session", description: "Agent.", required: false },
  { key: "tools", scope: "collection", description: "Tableau des outils.", required: false },
  { key: "tool_name", scope: "tool_call", description: "Nom de l'outil.", required: false },
];

function aProposal(mappings: MappingProposal["mappings"]): MappingProposal {
  return { mappings, unresolved_notes: [] };
}

describe("brouillon de mapping", () => {
  it("part de tous les champs du contrat, aucun renseigné", () => {
    expect(emptyDraft(FIELDS)).toEqual({
      session_id: "",
      agent: "",
      tools: "",
      tool_name: "",
    });
  });
});

describe("proposition de l'agent", () => {
  it("remplit les champs qu'elle vise", () => {
    const draft = applyProposal(
      emptyDraft(FIELDS),
      aProposal([{ target_field: "agent", source_field: "provider", confidence: 0.9, note: null }]),
      FIELDS,
    );

    expect(draft.agent).toBe("provider");
  });

  it("ne touche pas aux champs qu'elle ne mentionne pas", () => {
    // L'agent complète le travail de l'utilisateur, il ne l'efface pas.
    const draft = applyProposal(
      { ...emptyDraft(FIELDS), session_id: "sid_choisi_a_la_main" },
      aProposal([{ target_field: "agent", source_field: "provider", confidence: 0.9, note: null }]),
      FIELDS,
    );

    expect(draft.session_id).toBe("sid_choisi_a_la_main");
  });

  it("ignore un champ hors du contrat", () => {
    // Le serveur l'écarte déjà, mais l'interface ne doit pas non plus se laisser dicter
    // des champs par un modèle.
    const draft = applyProposal(
      emptyDraft(FIELDS),
      aProposal([{ target_field: "latency_ms", source_field: "duree", confidence: 1, note: null }]),
      FIELDS,
    );

    expect(draft).not.toHaveProperty("latency_ms");
  });

  it("ignore une correspondance que l'agent n'a pas trouvée", () => {
    const draft = applyProposal(
      { ...emptyDraft(FIELDS), agent: "déjà_saisi" },
      aProposal([{ target_field: "agent", source_field: null, confidence: null, note: "rien" }]),
      FIELDS,
    );

    expect(draft.agent).toBe("déjà_saisi");
  });

  it("récupère la confiance et la note par champ", () => {
    const notes = notesByField(
      aProposal([{ target_field: "agent", source_field: "provider", confidence: 0.8, note: "ok" }]),
    );

    expect(notes.agent).toEqual({ confidence: 0.8, note: "ok" });
  });

  it("sans proposition, aucune note", () => {
    expect(notesByField(undefined)).toEqual({});
  });
});

describe("mapping enregistré", () => {
  it("remplace intégralement le brouillon", () => {
    const draft = fromSaved({ session_id: "sid", agent: null }, FIELDS);

    expect(draft).toEqual({ session_id: "sid", agent: "", tools: "", tool_name: "" });
  });

  it("ignore un champ enregistré qui n'existe plus dans le contrat", () => {
    const draft = fromSaved({ session_id: "sid", latency_ms: "x" }, FIELDS);

    expect(draft).not.toHaveProperty("latency_ms");
  });
});

describe("mapping envoyé au serveur", () => {
  it("traduit un champ vide en absence, pas en chaîne vide", () => {
    // Une chaîne vide serait interprétée comme un chemin, et le moteur irait chercher une
    // colonne sans nom.
    const mapping = toMapping({ session_id: "sid", agent: "" });

    expect(mapping).toEqual({ session_id: "sid", agent: null });
  });

  it("retire les espaces autour d'un chemin", () => {
    expect(toMapping({ session_id: "  sid  " }).session_id).toBe("sid");
  });

  it("traduit un champ ne contenant que des espaces en absence", () => {
    expect(toMapping({ session_id: "sid", agent: "   " }).agent).toBeNull();
  });
});

describe("ce qui empêche d'importer", () => {
  it("signale un champ obligatoire vide", () => {
    expect(missingRequired(emptyDraft(FIELDS), FIELDS)).toEqual(["session_id"]);
  });

  it("ne signale rien quand l'obligatoire est renseigné", () => {
    expect(missingRequired({ ...emptyDraft(FIELDS), session_id: "sid" }, FIELDS)).toEqual([]);
  });

  it("signale un champ d'outil sans le tableau qui le contient", () => {
    const draft = { ...emptyDraft(FIELDS), session_id: "sid", tool_name: "nom" };

    expect(toolFieldsWithoutCollection(draft, FIELDS)).toEqual(["tool_name"]);
  });

  it("ne signale rien quand le tableau est renseigné", () => {
    const draft = { ...emptyDraft(FIELDS), session_id: "sid", tool_name: "nom", tools: "outils" };

    expect(toolFieldsWithoutCollection(draft, FIELDS)).toEqual([]);
  });
});
