/**
 * Le mapping en cours de mise au point, et rien d'autre.
 *
 * Ces fonctions sont pures : elles ne touchent ni au réseau, ni au DOM. C'est ce qui
 * permet de vérifier les règles qui comptent — un champ non renseigné reste `null`, une
 * proposition d'IA ne peut pas introduire un champ hors contrat — sans monter d'écran.
 */

import type { FieldMappingValues, MappingProposal, TargetField } from "../../../shared/api/types";

/** Un brouillon associe chaque champ du contrat à un chemin, éventuellement vide. */
export type MappingDraft = Record<string, string>;

/** Un brouillon vide : tous les champs du contrat présents, aucun renseigné. */
export function emptyDraft(fields: TargetField[]): MappingDraft {
  return Object.fromEntries(fields.map((field) => [field.key, ""]));
}

/**
 * Reprend une proposition de l'IA dans le brouillon.
 *
 * Les champs que la proposition ne mentionne pas gardent ce qu'ils avaient : l'IA complète
 * le travail de l'utilisateur, elle ne l'efface pas. Un champ visé hors du contrat est
 * ignoré — le serveur l'a déjà écarté, mais l'interface ne doit pas non plus se laisser
 * dicter des champs par un modèle.
 */
export function applyProposal(
  draft: MappingDraft,
  proposal: MappingProposal,
  fields: TargetField[],
): MappingDraft {
  const known = new Set(fields.map((field) => field.key));
  const next = { ...draft };

  for (const item of proposal.mappings) {
    if (known.has(item.target_field) && item.source_field) {
      next[item.target_field] = item.source_field;
    }
  }

  return next;
}

/** Reprend un mapping enregistré, en remplaçant intégralement le brouillon. */
export function fromSaved(saved: FieldMappingValues, fields: TargetField[]): MappingDraft {
  return Object.fromEntries(fields.map((field) => [field.key, saved[field.key] ?? ""]));
}

/**
 * Le mapping tel que le serveur l'attend.
 *
 * **Un champ laissé vide devient `null`, jamais la chaîne vide.** C'est la même règle que
 * partout ailleurs dans le projet : une absence reste une absence. Une chaîne vide serait
 * interprétée comme un chemin, et le moteur irait chercher une colonne sans nom.
 */
export function toMapping(draft: MappingDraft): FieldMappingValues {
  return Object.fromEntries(
    Object.entries(draft).map(([key, path]) => [key, path.trim() || null]),
  );
}

/** Les champs obligatoires encore vides — ce qui empêche d'importer. */
export function missingRequired(draft: MappingDraft, fields: TargetField[]): string[] {
  return fields
    .filter((field) => field.required && !draft[field.key]?.trim())
    .map((field) => field.key);
}

/**
 * Les champs d'appel d'outil renseignés alors que le tableau qui les contient ne l'est pas.
 *
 * Le serveur refuse ce cas, mais l'attendre pour le dire ferait perdre un aller-retour sur
 * une erreur que l'interface a sous les yeux.
 */
export function toolFieldsWithoutCollection(
  draft: MappingDraft,
  fields: TargetField[],
): string[] {
  if (draft["tools"]?.trim()) {
    return [];
  }

  return fields
    .filter((field) => field.scope === "tool_call" && draft[field.key]?.trim())
    .map((field) => field.key);
}

/** Les notes de l'IA, par champ, pour les afficher à côté de ce qu'elle a proposé. */
export function notesByField(
  proposal: MappingProposal | undefined,
): Record<string, { confidence: number | null; note: string | null }> {
  if (!proposal) {
    return {};
  }

  return Object.fromEntries(
    proposal.mappings.map((item) => [
      item.target_field,
      { confidence: item.confidence, note: item.note },
    ]),
  );
}
