import { useQuery } from "@tanstack/react-query";

import { fetchImportDetail } from "../../../shared/api/imports";
import type { ImportRecordResponse } from "../../../shared/api/types";
import { formatImportStatus } from "../utils/importHelpers";

interface ImportSummaryPanelProps {
  record: ImportRecordResponse;
  onClose: () => void;
}

export function ImportSummaryPanel({ record, onClose }: ImportSummaryPanelProps) {
  const detailQuery = useQuery({
    queryKey: ["imports", record.id],
    queryFn: () => fetchImportDetail(record.id),
    retry: false,
  });

  const rejections = detailQuery.data?.rejections ?? [];

  return (
    <section className="import-summary" aria-label="Bilan d'import">
      <div className="import-summary__header">
        <h2 className="section-title">Bilan — {record.filename}</h2>
        <button type="button" className="btn btn--ghost" onClick={onClose}>
          Fermer
        </button>
      </div>

      <dl className="detail-grid">
        <div>
          <dt>Statut</dt>
          <dd>{formatImportStatus(record.status)}</dd>
        </div>
        <div>
          <dt>Source</dt>
          <dd>{record.source_name}</dd>
        </div>
        <div>
          <dt>Format</dt>
          <dd>{record.format.toUpperCase()}</dd>
        </div>
        <div>
          <dt>Importés</dt>
          <dd>{record.records_imported}</dd>
        </div>
        <div>
          <dt>Doublons</dt>
          <dd>{record.duplicates_count}</dd>
        </div>
        <div>
          <dt>Rejets</dt>
          <dd>{record.rejected_count}</dd>
        </div>
        <div>
          <dt>Infos manquantes</dt>
          <dd>{record.missing_data_count}</dd>
        </div>
      </dl>

      {detailQuery.isPending && (
        <p className="status-message">Chargement des rejets détaillés…</p>
      )}

      {detailQuery.isError && (
        <p className="status-message">
          Détail des rejets indisponible — le résumé ci-dessus reste valide.
        </p>
      )}

      {rejections.length > 0 && (
        <>
          <h3 className="section-title">Rejets</h3>
          <ul className="import-rejections">
            {rejections.map((rejection) => (
              <li key={`${rejection.line_number}-${rejection.reason}`}>
                <strong>Ligne {rejection.line_number}</strong> — {rejection.reason}
                {rejection.raw_preview && (
                  <pre className="import-rejections__preview">{rejection.raw_preview}</pre>
                )}
              </li>
            ))}
          </ul>
        </>
      )}
    </section>
  );
}
