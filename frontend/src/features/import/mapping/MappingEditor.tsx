import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";

import { ApiError } from "../../../shared/api/client";
import {
  deleteMapping,
  fetchMappingFields,
  fetchSavedMappings,
  previewMapping,
  proposeMapping,
  saveMapping,
} from "../../../shared/api/mappings";
import type {
  FieldMappingValues,
  ImportPreviewResponse,
  MappingProposal,
} from "../../../shared/api/types";
import {
  applyProposal,
  emptyDraft,
  fromSaved,
  missingRequired,
  notesByField,
  toMapping,
  toolFieldsWithoutCollection,
  type MappingDraft,
} from "./mappingDraft";
import { MappingOutcomeTable } from "./MappingOutcomeTable";

interface Props {
  preview: ImportPreviewResponse;
  onReady: (mapping: FieldMappingValues | null) => void;
}

const SCOPE_LABELS: Record<string, string> = {
  session: "Session",
  model_call: "Appel au modèle",
  tool_call: "Appel d'outil",
  collection: "Tableau à parcourir",
};

function message(error: unknown): string {
  return error instanceof ApiError ? error.message : "Une erreur inattendue s'est produite.";
}

/**
 * La mise au point d'un mapping, de la proposition à l'import.
 *
 * Le parcours tient en quatre gestes, dans cet ordre : **l'IA propose, l'utilisateur
 * corrige, l'essai à blanc montre ce que ça donnerait, et le mapping vérifié s'enregistre**
 * pour être rejoué sur le fichier suivant.
 *
 * Trois décisions se voient dans le code :
 *
 * - **La liste des champs vient du serveur** (`/api/v1/mapping/fields`), jamais d'une copie
 *   locale. Une liste dupliquée finirait par proposer des champs que le moteur refuse.
 * - **Rien n'est validé à la place de l'utilisateur.** L'IA remplit des cases qu'il peut
 *   toutes corriger, et l'essai à blanc lui montre les valeurs réellement lues avant qu'il
 *   ne décide.
 * - **Un champ vide reste vide.** Il n'est pas deviné à partir d'un nom qui se ressemble.
 */
export function MappingEditor({ preview, onReady }: Props) {
  const queryClient = useQueryClient();
  const [draft, setDraft] = useState<MappingDraft>({});
  const [proposal, setProposal] = useState<MappingProposal | undefined>();
  const [name, setName] = useState("");
  const [saveNotice, setSaveNotice] = useState<string | null>(null);

  const contractQuery = useQuery({ queryKey: ["mapping", "fields"], queryFn: fetchMappingFields });
  const savedQuery = useQuery({ queryKey: ["mappings"], queryFn: fetchSavedMappings, retry: false });

  const fields = useMemo(() => contractQuery.data?.fields ?? [], [contractQuery.data]);

  // Le brouillon ne peut exister avant de savoir quels champs le composent. On l'initialise
  // dès que le contrat arrive, et une seule fois : réinitialiser à chaque rendu effacerait
  // ce que l'utilisateur vient de saisir.
  useEffect(() => {
    if (fields.length > 0 && Object.keys(draft).length === 0) {
      setDraft(emptyDraft(fields));
    }
  }, [fields, draft]);

  const proposeMutation = useMutation({
    mutationFn: () =>
      proposeMapping(preview.sample_rows as Record<string, unknown>[], preview.format),
    onSuccess: (result) => {
      setProposal(result);
      setDraft((current) => applyProposal(current, result, fields));
    },
  });

  const previewMutation = useMutation({
    mutationFn: (mapping: FieldMappingValues) =>
      previewMapping(preview.sample_rows as Record<string, unknown>[], mapping),
  });

  const saveMutation = useMutation({
    mutationFn: (mapping: FieldMappingValues) => saveMapping(name, mapping),
    onSuccess: (saved) => {
      setSaveNotice(`Mapping « ${saved.name} » enregistré.`);
      void queryClient.invalidateQueries({ queryKey: ["mappings"] });
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteMapping,
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: ["mappings"] }),
  });

  const mapping = toMapping(draft);
  const missing = missingRequired(draft, fields);
  const orphanTools = toolFieldsWithoutCollection(draft, fields);
  const notes = notesByField(proposal);

  // Tant que le contrat n'est pas arrivé, il n'y a pas de mapping — pas même un mapping
  // vide. Sans cette garde, un brouillon vide face à une liste de champs vide passerait
  // pour applicable, et la page proposerait d'importer avec rien du tout.
  const ready = fields.length > 0 && Object.keys(draft).length > 0;
  const blocking = !ready || missing.length > 0 || orphanTools.length > 0;

  // Le mapping ne remonte à la page que lorsqu'il est applicable : proposer d'importer avec
  // un mapping que le serveur refusera n'aide personne.
  useEffect(() => {
    onReady(blocking ? null : mapping);
    // `mapping` est recalculé à chaque rendu ; c'est le brouillon qui décide vraiment.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [draft, blocking, fields.length]);

  const setField = (key: string, value: string) => {
    setDraft((current) => ({ ...current, [key]: value }));
    setSaveNotice(null);
  };

  if (contractQuery.isPending) {
    return <p className="status-message">Chargement des champs du modèle commun…</p>;
  }

  if (contractQuery.isError) {
    return (
      <p className="status-message status-message--error" role="alert">
        Impossible de lire les champs du modèle commun : {message(contractQuery.error)}
      </p>
    );
  }

  const savedMappings = savedQuery.data?.mappings ?? [];

  return (
    <section className="mapping" aria-label="Mise au point du mapping">
      <div className="mapping__header">
        <h2 className="section-title">Mapping — {preview.filename}</h2>
        <p className="mapping__lead">
          Associez chaque champ du modèle commun à un champ du fichier. Un champ laissé vide
          reste vide : il ne devient pas zéro, et rien n'est deviné à votre place.
        </p>
      </div>

      <div className="mapping__actions">
        <button
          type="button"
          className="btn btn--ghost"
          disabled={proposeMutation.isPending}
          onClick={() => proposeMutation.mutate()}
        >
          {proposeMutation.isPending ? "L'agent analyse…" : "Proposer avec l'IA"}
        </button>

        {savedMappings.length > 0 && (
          <label className="field field--inline">
            <span className="field__label">Mapping enregistré</span>
            <select
              className="field__input"
              defaultValue=""
              onChange={(event) => {
                const chosen = savedMappings.find((entry) => entry.id === event.target.value);
                if (chosen) {
                  setDraft(fromSaved(chosen.mapping, fields));
                  setName(chosen.name);
                  setProposal(undefined);
                  setSaveNotice(null);
                }
              }}
            >
              <option value="">Choisir…</option>
              {savedMappings.map((entry) => (
                <option key={entry.id} value={entry.id}>
                  {entry.name}
                  {entry.source_name ? ` (${entry.source_name})` : ""}
                </option>
              ))}
            </select>
          </label>
        )}

        <button
          type="button"
          className="btn btn--ghost"
          onClick={() => {
            setDraft(emptyDraft(fields));
            setProposal(undefined);
            setSaveNotice(null);
          }}
        >
          Tout effacer
        </button>
      </div>

      {proposeMutation.isError && (
        <p className="status-message status-message--error" role="alert">
          {message(proposeMutation.error)}
        </p>
      )}

      {proposal && proposal.unresolved_notes.length > 0 && (
        <div className="mapping__unresolved">
          <h3 className="mapping__subtitle">Ce que l'agent n'a pas su rapprocher</h3>
          <ul>
            {proposal.unresolved_notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </div>
      )}

      <datalist id="mapping-columns">
        {preview.columns.map((column) => (
          <option key={column} value={column} />
        ))}
      </datalist>

      <div className="mapping__table-wrap">
        <table className="mapping__table">
          <thead>
            <tr>
              <th scope="col">Champ du modèle</th>
              <th scope="col">Champ du fichier</th>
              <th scope="col">Portée</th>
              <th scope="col">L'agent dit</th>
            </tr>
          </thead>
          <tbody>
            {fields.map((field) => (
              <tr key={field.key}>
                <th scope="row">
                  <span className="mapping__key">{field.key}</span>
                  {field.required && <span className="mapping__required"> (obligatoire)</span>}
                  <span className="mapping__description">{field.description}</span>
                </th>
                <td>
                  <input
                    className="field__input"
                    type="text"
                    list="mapping-columns"
                    placeholder="laisser vide si absent"
                    aria-label={`Champ du fichier pour ${field.key}`}
                    value={draft[field.key] ?? ""}
                    onChange={(event) => setField(field.key, event.target.value)}
                  />
                </td>
                <td>{SCOPE_LABELS[field.scope] ?? field.scope}</td>
                <td className="mapping__note">
                  {notes[field.key]?.confidence !== undefined &&
                    notes[field.key]?.confidence !== null && (
                      <strong>{Math.round((notes[field.key].confidence ?? 0) * 100)} % </strong>
                    )}
                  {notes[field.key]?.note ?? ""}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {missing.length > 0 && (
        <p className="status-message status-message--error" role="alert">
          Champs obligatoires non renseignés : {missing.join(", ")}. Sans eux, les
          enregistrements ne peuvent être rattachés à aucune session.
        </p>
      )}

      {orphanTools.length > 0 && (
        <p className="status-message status-message--error" role="alert">
          {orphanTools.join(", ")} décrivent des appels d'outils, mais « tools » ne dit pas où
          les trouver. Renseignez le chemin du tableau qui les contient.
        </p>
      )}

      <div className="mapping__actions">
        <button
          type="button"
          className="btn btn--ghost"
          disabled={blocking || previewMutation.isPending}
          onClick={() => previewMutation.mutate(mapping)}
        >
          {previewMutation.isPending ? "Essai en cours…" : "Vérifier sur l'échantillon"}
        </button>

        <label className="field field--inline">
          <span className="field__label">Nom du mapping</span>
          <input
            className="field__input"
            type="text"
            placeholder="TraceLab JSONL"
            value={name}
            onChange={(event) => setName(event.target.value)}
          />
        </label>

        <button
          type="button"
          className="btn btn--ghost"
          disabled={blocking || !name.trim() || saveMutation.isPending}
          onClick={() => saveMutation.mutate(mapping)}
        >
          {saveMutation.isPending ? "Enregistrement…" : "Enregistrer ce mapping"}
        </button>
      </div>

      {saveNotice && <p className="status-message">{saveNotice}</p>}

      {saveMutation.isError && (
        <p className="status-message status-message--error" role="alert">
          {message(saveMutation.error)}
        </p>
      )}

      {previewMutation.isError && (
        <p className="status-message status-message--error" role="alert">
          {message(previewMutation.error)}
        </p>
      )}

      {previewMutation.data && <MappingOutcomeTable outcome={previewMutation.data} />}

      {savedMappings.length > 0 && (
        <details className="mapping__library">
          <summary>Mappings enregistrés ({savedMappings.length})</summary>
          <ul className="mapping__library-list">
            {savedMappings.map((entry) => (
              <li key={entry.id}>
                <span>{entry.name}</span>
                <button
                  type="button"
                  className="btn btn--ghost btn--small"
                  onClick={() => deleteMutation.mutate(entry.id)}
                >
                  Supprimer
                </button>
              </li>
            ))}
          </ul>
        </details>
      )}
    </section>
  );
}
