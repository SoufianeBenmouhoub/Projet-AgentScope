import { useState } from "react";

import type {
  FieldMappingValues,
  ImportPreviewResponse,
  ImportRecordResponse,
} from "../../shared/api/types";
import { FileUploadZone } from "./components/FileUploadZone";
import { ImportHistoryTable } from "./components/ImportHistoryTable";
import { ImportLauncher } from "./components/ImportLauncher";
import { ImportPreviewPanel } from "./components/ImportPreviewPanel";
import { ImportSummaryPanel } from "./components/ImportSummaryPanel";
import { MappingEditor } from "./mapping/MappingEditor";

/**
 * L'écran d'import, dans l'ordre des étapes : **choisir, regarder, mapper, vérifier,
 * importer**.
 *
 * La page tient l'état commun — le fichier, l'aperçu, le mapping — parce que trois écrans
 * s'en servent et qu'aucun n'en est propriétaire. Le mapping ne descend au lanceur que
 * lorsqu'il est applicable : `null` veut dire « rien de valable à envoyer », ce qui n'est
 * pas la même chose qu'un mapping vide.
 */
export function ImportPage() {
  const [sourceName, setSourceName] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<ImportPreviewResponse | null>(null);
  const [mapping, setMapping] = useState<FieldMappingValues | null>(null);
  const [mappingBlocked, setMappingBlocked] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState<ImportRecordResponse | null>(null);
  const [historyRefreshKey, setHistoryRefreshKey] = useState(0);

  const handleImportComplete = (result: ImportRecordResponse) => {
    setPreview(null);
    setFile(null);
    setMapping(null);
    setMappingBlocked(false);
    setSelectedRecord(result);
    setHistoryRefreshKey((key) => key + 1);
  };

  const handleFileChange = (chosen: File | null) => {
    setFile(chosen);
    setPreview(null);
    setMapping(null);
    setMappingBlocked(false);
  };

  return (
    <section className="page">
      <header className="page__header">
        <h1>Import</h1>
        <p className="page__lead">
          Ajoutez un fichier JSONL, CSV ou Parquet, décidez comment le lire, vérifiez le
          résultat, puis importez.
        </p>
      </header>

      <section className="import-source" aria-label="Source des données">
        <h2 className="section-title">Source</h2>
        <label className="field">
          <span className="field__label">Nom de la source</span>
          <input
            className="field__input"
            type="text"
            placeholder="tracelab, swe-chat…"
            value={sourceName}
            onChange={(event) => setSourceName(event.target.value)}
          />
        </label>
        <p className="import-source__hint">
          Le nom sous lequel les traces apparaîtront dans le tableau de bord. Une source déjà
          connue est réutilisée telle quelle.
        </p>
      </section>

      <FileUploadZone
        sourceName={sourceName}
        file={file}
        onFileChange={handleFileChange}
        onPreviewReady={setPreview}
      />

      {preview && <ImportPreviewPanel preview={preview} onClose={() => setPreview(null)} />}

      {preview && (
        <MappingEditor
          preview={preview}
          onReady={(applicable) => {
            setMapping(applicable);
            setMappingBlocked(applicable === null);
          }}
        />
      )}

      <ImportLauncher
        file={file}
        sourceName={sourceName}
        mapping={mapping}
        mappingBlocked={mappingBlocked}
        onImportComplete={handleImportComplete}
      />

      {selectedRecord && (
        <ImportSummaryPanel record={selectedRecord} onClose={() => setSelectedRecord(null)} />
      )}

      <ImportHistoryTable refreshKey={historyRefreshKey} onSelect={setSelectedRecord} />
    </section>
  );
}
