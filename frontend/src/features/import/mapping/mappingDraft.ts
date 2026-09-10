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

/**
 * Les portées, dans l'ordre où on remplit le formulaire : ce qui décrit la session, puis
 * l'appel au modèle, puis le tableau des outils, puis ce qu'on lit dedans.
 */
const SCOPE_ORDER = ["session", "model_call", "collection", "tool_call"];

/**
 * Répartit les champs par portée, en conservant l'ordre du contrat à l'intérieur de chaque
 * groupe.
 *
 * Dix-sept champs à la suite forment une liste sans relief, où les six derniers — ceux des
 * appels d'outils — se retrouvent en bas sans que rien ne dise qu'ils forment un bloc.
 *
 * Une portée inconnue du serveur n'est pas jetée : elle est rendue après les autres, dans
 * son propre groupe. Perdre un champ parce que sa portée est nouvelle serait pire que de
 * l'afficher au mauvais endroit.
 */
export function groupByScope(fields: TargetField[]): [string, TargetField[]][] {
  const groups = new Map<string, TargetField[]>();

  for (const field of fields) {
    const group = groups.get(field.scope);
    if (group) {
      group.push(field);
    } else {
      groups.set(field.scope, [field]);
    }
  }

  const rank = (scope: string) => {
    const index = SCOPE_ORDER.indexOf(scope);
    return index === -1 ? SCOPE_ORDER.length : index;
  };

  return [...groups.entries()].sort(([a], [b]) => rank(a) - rank(b));
}

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
