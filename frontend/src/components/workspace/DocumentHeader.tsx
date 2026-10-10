import React from "react";
import type { DocumentItem } from "../../types/document";
import { prettyText } from "../../utils/formatters";
import { Badge } from "../common/Badge";

interface DocumentHeaderProps {
  document: DocumentItem;
}

export const DocumentHeader: React.FC<DocumentHeaderProps> = ({ document }) => {
  const pageProgress =
    document.total_pages !== null && document.total_pages !== undefined
      ? ` · ${document.processed_pages ?? 0} / ${document.total_pages} pages`
      : "";

  return (
    <div className="result-header">
      <p className="eyebrow">EXTRACTION RESULTS</p>
      <h2>{document.filename}</h2>
      <div className="status-line" role="status">
        <Badge status={document.status} />
        <span>
          {prettyText(document.processing_stage)}
          {pageProgress}
        </span>
      </div>
      <small className="document-id">ID · {document.id}</small>
    </div>
  );
};
