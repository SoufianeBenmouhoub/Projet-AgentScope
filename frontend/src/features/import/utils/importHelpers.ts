const ACCEPTED_EXTENSIONS = [".jsonl", ".csv", ".parquet"];

export function isAcceptedImportFile(file: File): boolean {
  const lowerName = file.name.toLowerCase();
  return ACCEPTED_EXTENSIONS.some((ext) => lowerName.endsWith(ext));
}

export function formatImportStatus(status: string): string {
  switch (status) {
    case "completed":
      return "Terminé";
    case "duplicate":
      return "Doublon";
    case "failed":
      return "Échec";
    case "running":
      return "En cours";
    case "pending":
      return "En attente";
    default:
      return status;
  }
}
