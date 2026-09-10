import { useMutation } from "@tanstack/react-query";
import { useRef, useState } from "react";

import { ApiError } from "../../../shared/api/client";
import { previewImportFile } from "../../../shared/api/imports";
import type { ImportPreviewResponse } from "../../../shared/api/types";
import { isAcceptedImportFile } from "../utils/importHelpers";

interface FileUploadZoneProps {
  sourceName: string;
  file: File | null;
  onFileChange: (file: File | null) => void;
  onPreviewReady: (preview: ImportPreviewResponse) => void;
}

/**
 * Le choix du fichier et son aperçu. **Rien n'est importé ici.**
 *
 * L'import est déclenché plus bas, après la mise au point du mapping : mettre le bouton
 * « Importer » à côté du bouton « Prévisualiser » inviterait à sauter l'étape qui donne
 * tout son sens à l'aperçu.
 */
export function FileUploadZone({
  sourceName,
  file,
  onFileChange,
  onPreviewReady,
}: FileUploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  const previewMutation = useMutation({
    mutationFn: (chosen: File) => previewImportFile(chosen, sourceName),
    onSuccess: onPreviewReady,
  });

  const handleFile = (chosen: File | undefined) => {
    setValidationError(null);
    previewMutation.reset();

    if (!chosen) {
      onFileChange(null);
      return;
    }

    if (!isAcceptedImportFile(chosen)) {
      onFileChange(null);
      setValidationError("Formats acceptés : JSONL, CSV ou Parquet.");
      return;
    }

    onFileChange(chosen);
  };

  const apiMessage = (error: unknown): string => {
    if (error instanceof ApiError) {
      return error.status === 404
        ? "L'API d'import n'est pas encore disponible côté serveur."
        : error.message;
    }
    return "Une erreur inattendue s'est produite.";
  };

  return (
    <section className="import-upload" aria-label="Téléversement de fichier">
      <h2 className="section-title">Nouvel import</h2>
      <p className="import-upload__hint">
        Sélectionnez un fichier JSONL, CSV ou Parquet. L'aperçu montre ses champs et
        quelques lignes, sans rien écrire en base.
      </p>

      <div
        className="import-dropzone"
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          handleFile(event.dataTransfer.files[0]);
        }}
      >
        <input
          ref={inputRef}
          id="import-file"
          className="import-dropzone__input"
          type="file"
          accept=".jsonl,.csv,.parquet"
          onChange={(event) => handleFile(event.target.files?.[0])}
        />
        <label htmlFor="import-file" className="import-dropzone__label">
          {file ? (
            <>
              <strong>{file.name}</strong>
              <span>{Math.round(file.size / 1024)} Ko</span>
            </>
          ) : (
            <>Glissez un fichier ici ou cliquez pour parcourir</>
          )}
        </label>
      </div>

      {validationError && (
        <p className="status-message status-message--error" role="alert">
          {validationError}
        </p>
      )}

      {previewMutation.isError && (
        <p className="status-message status-message--error" role="alert">
          {apiMessage(previewMutation.error)}
        </p>
      )}

      <div className="import-upload__actions">
        <button
          type="button"
          className="btn btn--primary"
          disabled={!file || previewMutation.isPending}
          onClick={() => file && previewMutation.mutate(file)}
        >
          {previewMutation.isPending ? "Analyse…" : "Prévisualiser"}
        </button>
      </div>
    </section>
  );
}
