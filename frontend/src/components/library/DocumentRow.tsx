import React from "react";
import type { DocumentItem } from "../../types/document";
import { formatDate, prettyText } from "../../utils/formatters";

interface DocumentRowProps {
  document: DocumentItem;
  isSelected: boolean;
  onSelect: (id: string) => void;
}

export const DocumentRow: React.FC<DocumentRowProps> = ({
  document,
  isSelected,
  onSelect,
}) => {
  const isPdf = document.filename.toLowerCase().endsWith(".pdf");
  const fileTypeLabel = isPdf ? "PDF" : "DOCX";

  return (
    <button
      className={`document-row ${isSelected ? "selected" : ""}`}
      onClick={() => onSelect(document.id)}
      type="button"
      aria-current={isSelected ? "true" : undefined}
    >
      <span className="file-icon" aria-hidden="true">
        {fileTypeLabel}
      </span>
      <span className="file-meta">
        <strong title={document.filename}>{document.filename}</strong>
        <small>
          {formatDate(document.created_at)} · {prettyText(document.status)}
        </small>
      </span>
      <span aria-hidden="true">›</span>
    </button>
  );
};
