import { useState } from "react";

import type { ImportPreviewResponse, ImportRecordResponse } from "../../shared/api/types";
import { FileUploadZone } from "./components/FileUploadZone";
import { ImportHistoryTable } from "./components/ImportHistoryTable";
import { ImportPreviewPanel } from "./components/ImportPreviewPanel";
import { ImportSummaryPanel } from "./components/ImportSummaryPanel";

/** Import de fichiers — upload, aperçu et historique. */
export function ImportPage() {
  const [sourceName, setSourceName] = useState("");
  const [preview, setPreview] = useState<ImportPreviewResponse | null>(null);
  const [selectedRecord, setSelectedRecord] = useState<ImportRecordResponse | null>(null);
  const [historyRefreshKey, setHistoryRefreshKey] = useState(0);

  const handleImportComplete = (result: ImportRecordResponse) => {
    setPreview(null);
    setSelectedRecord(result);
    setHistoryRefreshKey((key) => key + 1);
  };

  return (
    <section className="page">
      <header className="page__header">
        <h1>Import</h1>
        <p className="page__lead">
          Ajoutez un fichier JSONL, CSV ou Parquet. Consultez l'aperçu et l'historique des
          imports.
        </p>
      </header>

      <section className="import-source" aria-label="Source des données">
        <h2 className="section-title">Source (optionnelle)</h2>
        <label className="field">
          <span className="field__label">Nom de la source</span>
          <input
            className="field__input"
            type="text"
            placeholder="traces_lab, swe_chat…"
            value={sourceName}
            onChange={(event) => setSourceName(event.target.value)}
          />
        </label>
        <p className="import-source__hint">
          Laissez vide pour laisser le moteur détecter la source, ou renseignez-la pour une
          nouvelle structure (agent IA — lot 4).
        </p>
      </section>

      <FileUploadZone
        sourceName={sourceName}
        onPreviewReady={setPreview}
        onImportComplete={handleImportComplete}
      />

      {preview && <ImportPreviewPanel preview={preview} onClose={() => setPreview(null)} />}

      {selectedRecord && (
        <ImportSummaryPanel record={selectedRecord} onClose={() => setSelectedRecord(null)} />
      )}

      <ImportHistoryTable
        refreshKey={historyRefreshKey}
        onSelect={setSelectedRecord}
      />
    </section>
  );
}
