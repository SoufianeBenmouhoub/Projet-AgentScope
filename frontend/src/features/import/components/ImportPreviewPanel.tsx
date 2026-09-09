import type { ImportPreviewResponse } from "../../../shared/api/types";

interface ImportPreviewPanelProps {
  preview: ImportPreviewResponse;
  onClose: () => void;
}

export function ImportPreviewPanel({ preview, onClose }: ImportPreviewPanelProps) {
  const columns = preview.columns.length > 0 ? preview.columns : Object.keys(preview.sample_rows[0] ?? {});

  return (
    <section className="import-preview" aria-label="Aperçu du fichier">
      <div className="import-preview__header">
        <h2 className="section-title">Aperçu — {preview.filename}</h2>
        <button type="button" className="btn btn--ghost" onClick={onClose}>
          Fermer
        </button>
      </div>

      <p className="import-preview__meta">
        Format {preview.format.toUpperCase()} · {preview.row_count_sample} ligne(s) échantillon
      </p>

      {columns.length === 0 ? (
        <p className="status-message">Aucune colonne détectée dans l'échantillon.</p>
      ) : (
        <div className="import-preview__table-wrap">
          <table className="import-preview__table">
            <thead>
              <tr>
                {columns.map((column) => (
                  <th key={column}>{column}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {preview.sample_rows.map((row, index) => (
                <tr key={index}>
                  {columns.map((column) => (
                    <td key={column}>{formatCell(row[column])}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}

function formatCell(value: unknown): string {
  if (value === null || value === undefined) {
    return "—";
  }
  if (typeof value === "object") {
    return JSON.stringify(value);
  }
  return String(value);
}
