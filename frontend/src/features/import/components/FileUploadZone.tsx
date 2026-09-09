import { useMutation } from "@tanstack/react-query";
import { useRef, useState } from "react";

import { previewImportFile, uploadImportFile } from "../../../shared/api/imports";
import { ApiError } from "../../../shared/api/client";
import type { ImportPreviewResponse, ImportRecordResponse } from "../../../shared/api/types";
import { isAcceptedImportFile } from "../utils/importHelpers";

interface FileUploadZoneProps {
  sourceName: string;
  onImportComplete: (result: ImportRecordResponse) => void;
  onPreviewReady: (preview: ImportPreviewResponse) => void;
}

export function FileUploadZone({ sourceName, onImportComplete, onPreviewReady }: FileUploadZoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [validationError, setValidationError] = useState<string | null>(null);

  const previewMutation = useMutation({
    mutationFn: (file: File) => previewImportFile(file, sourceName),
    onSuccess: onPreviewReady,
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadImportFile(file, sourceName),
    onSuccess: (result) => {
      setSelectedFile(null);
      if (inputRef.current) {
        inputRef.current.value = "";
      }
      onImportComplete(result);
    },
  });

  const handleFile = (file: File | undefined) => {
    setValidationError(null);
    previewMutation.reset();
    uploadMutation.reset();

    if (!file) {
      setSelectedFile(null);
      return;
    }

    if (!isAcceptedImportFile(file)) {
      setSelectedFile(null);
      setValidationError("Formats acceptés : JSONL, CSV ou Parquet.");
      return;
    }

    setSelectedFile(file);
  };

  const apiMessage = (error: unknown): string => {
    if (error instanceof ApiError) {
      if (error.status === 404) {
        return "L'API d'import n'est pas encore disponible côté serveur.";
      }
      return error.message;
    }
    return "Une erreur inattendue s'est produite.";
  };

  const isBusy = previewMutation.isPending || uploadMutation.isPending;

  return (
    <section className="import-upload" aria-label="Téléversement de fichier">
      <h2 className="section-title">Nouvel import</h2>
      <p className="import-upload__hint">
        Sélectionnez un fichier JSONL, CSV ou Parquet. Vous pouvez prévisualiser sa structure
        avant de lancer l'import définitif.
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
          {selectedFile ? (
            <>
              <strong>{selectedFile.name}</strong>
              <span>{Math.round(selectedFile.size / 1024)} Ko</span>
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

      {uploadMutation.isError && (
        <p className="status-message status-message--error" role="alert">
          {apiMessage(uploadMutation.error)}
        </p>
      )}

      <div className="import-upload__actions">
        <button
          type="button"
          className="btn btn--ghost"
          disabled={!selectedFile || isBusy}
          onClick={() => selectedFile && previewMutation.mutate(selectedFile)}
        >
          {previewMutation.isPending ? "Analyse…" : "Prévisualiser"}
        </button>
        <button
          type="button"
          className="btn btn--primary"
          disabled={!selectedFile || isBusy}
          onClick={() => selectedFile && uploadMutation.mutate(selectedFile)}
        >
          {uploadMutation.isPending ? "Import en cours…" : "Importer"}
        </button>
      </div>
    </section>
  );
}
