import { useMutation } from "@tanstack/react-query";

import { ApiError } from "../../../shared/api/client";
import { uploadImportFile } from "../../../shared/api/imports";
import type { FieldMappingValues, ImportRecordResponse } from "../../../shared/api/types";

interface Props {
  file: File | null;
  sourceName: string;
  mapping: FieldMappingValues | null;
  mappingBlocked: boolean;
  onImportComplete: (result: ImportRecordResponse) => void;
}

/**
 * Le dernier geste : lancer l'import avec le mapping qu'on vient de vérifier.
 *
 * Il est séparé du choix du fichier pour une raison de parcours : l'ordre des écrans est
 * l'ordre des étapes, et il n'y a rien à importer tant qu'on n'a pas décidé comment lire le
 * fichier. Le bouton reste refusé tant que le mapping est inapplicable, avec la raison — un
 * import lancé pour recevoir un 422 fait perdre un aller-retour et rien d'autre.
 */
export function ImportLauncher({
  file,
  sourceName,
  mapping,
  mappingBlocked,
  onImportComplete,
}: Props) {
  const uploadMutation = useMutation({
    mutationFn: () => uploadImportFile(file!, sourceName, mapping),
    onSuccess: onImportComplete,
  });

  const message =
    uploadMutation.error instanceof ApiError
      ? uploadMutation.error.message
      : "Une erreur inattendue s'est produite.";

  return (
    <section className="import-launch" aria-label="Lancement de l'import">
      <h2 className="section-title">Importer</h2>

      <p className="import-upload__hint">
        {mapping
          ? "Le fichier sera importé avec le mapping ci-dessus."
          : "Aucun mapping fourni : le serveur tentera un préréglage connu pour cette source, ou une correspondance à l'identique."}
      </p>

      {uploadMutation.isError && (
        <p className="status-message status-message--error" role="alert">
          {message}
        </p>
      )}

      <div className="import-upload__actions">
        <button
          type="button"
          className="btn btn--primary"
          disabled={!file || mappingBlocked || uploadMutation.isPending}
          onClick={() => uploadMutation.mutate()}
        >
          {uploadMutation.isPending ? "Import en cours…" : "Importer"}
        </button>
      </div>

      {mappingBlocked && (
        <p className="status-message">
          Complétez les champs obligatoires du mapping avant d'importer.
        </p>
      )}
    </section>
  );
}
