import React from "react";
import type { DocumentItem } from "../../types/document";
import { DocumentRow } from "./DocumentRow";
import { Pagination } from "./Pagination";

interface DocumentLibraryProps {
  documents: DocumentItem[];
  selectedId: string | null;
  onSelect: (id: string) => void;
  page: number;
  onPageChange: (page: number) => void;
  pageSize?: number;
}

export const DocumentLibrary: React.FC<DocumentLibraryProps> = ({
  documents,
  selectedId,
  onSelect,
  page,
  onPageChange,
  pageSize = 20,
}) => {
  return (
    <>
      <div className="section-label">
        <span>DOCUMENT LIBRARY </span>
        <span>{documents.length}</span>
      </div>

      <nav aria-label="Saved documents" className="library">
        {documents.length === 0 ? (
          <p className="muted">No saved documents yet. Upload a file above to begin.</p>
        ) : (
          documents.map((doc) => (
            <DocumentRow
              key={doc.id}
              document={doc}
              isSelected={selectedId === doc.id}
              onSelect={onSelect}
            />
          ))
        )}
      </nav>

      <Pagination
        page={page}
        hasMore={documents.length >= pageSize}
        onPageChange={onPageChange}
      />

      <p className="privacy">
        Original files and extracted results are stored locally.
      </p>
    </>
  );
};
