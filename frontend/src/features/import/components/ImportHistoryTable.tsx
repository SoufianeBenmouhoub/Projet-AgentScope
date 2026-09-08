import { useQuery } from "@tanstack/react-query";
import { Link } from "react-router-dom";

import { fetchImportHistory } from "../../../shared/api/imports";
import type { ImportRecordResponse } from "../../../shared/api/types";
import { formatImportStatus } from "../utils/importHelpers";

interface ImportHistoryTableProps {
  refreshKey: number;
  onSelect: (record: ImportRecordResponse) => void;
}

export function ImportHistoryTable({ refreshKey, onSelect }: ImportHistoryTableProps) {
  const { data, isPending, isError, error } = useQuery({
    queryKey: ["imports", "history", refreshKey],
    queryFn: fetchImportHistory,
    retry: false,
  });

  if (isPending) {
    return <p className="status-message">Chargement de l'historique…</p>;
  }

  if (isError) {
    const message =
      error && typeof error === "object" && "status" in error && error.status === 404
        ? "L'historique des imports sera disponible quand l'API sera branchée."
        : "Impossible de charger l'historique des imports.";

    return (
      <p className="status-message" role="status">
        {message}
      </p>
    );
  }

  if (data.imports.length === 0) {
    return (
      <p className="status-message">
        Aucun import enregistré. Téléversez un fichier pour commencer.
      </p>
    );
  }

  return (
    <section className="import-history" aria-label="Historique des imports">
      <h2 className="section-title">Historique</h2>
      <div className="import-history__table-wrap">
        <table className="import-history__table">
          <thead>
            <tr>
              <th>Fichier</th>
              <th>Source</th>
              <th>Date</th>
              <th>Statut</th>
              <th>Importés</th>
              <th>Rejets</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {data.imports.map((record) => (
              <tr key={record.id}>
                <td>{record.filename}</td>
                <td>{record.source_name}</td>
                <td>{new Date(record.imported_at).toLocaleString("fr-FR")}</td>
                <td>
                  <span className={`import-status import-status--${record.status}`}>
                    {formatImportStatus(record.status)}
                  </span>
                </td>
                <td>{record.records_imported}</td>
                <td>{record.rejected_count}</td>
                <td>
                  <button
                    type="button"
                    className="btn btn--link"
                    onClick={() => onSelect(record)}
                  >
                    Bilan
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <p className="import-history__footer">
        Les données importées alimentent le{" "}
        <Link to="/" className="btn btn--link">
          dashboard
        </Link>
        .
      </p>
    </section>
  );
}
