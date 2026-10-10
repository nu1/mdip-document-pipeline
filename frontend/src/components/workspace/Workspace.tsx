import React, { useState } from "react";
import type { DocumentItem } from "../../types/document";
import { isTerminalStatus } from "../../utils/formatters";
import { ContentTabs, type ContentViewMode } from "./ContentTabs";
import { DocumentHeader } from "./DocumentHeader";
import { ExtractionWarnings } from "./ExtractionWarnings";
import { PageRoutesView } from "./PageRoutesView";
import { ProcessingStatus } from "./ProcessingStatus";
import { ReadableTextView } from "./ReadableTextView";
import { StructuredBlocksView } from "./StructuredBlocksView";
import { WorkspaceEmpty } from "./WorkspaceEmpty";

interface WorkspaceProps {
  selectedId: string | null;
  document: DocumentItem | null;
  isLoading: boolean;
  documentError?: string;
  onDismissError?: () => void;
}

export const Workspace: React.FC<WorkspaceProps> = ({
  selectedId,
  document,
  isLoading,
  documentError,
  onDismissError,
}) => {
  const [viewMode, setViewMode] = useState<ContentViewMode>("blocks");

  if (!selectedId) {
    return (
      <section className="workspace" aria-label="Document results">
        <WorkspaceEmpty />
      </section>
    );
  }

  if (isLoading && !document) {
    return (
      <section className="workspace" aria-label="Document results">
        <div className="empty" role="status" aria-live="polite">
          Loading document…
        </div>
      </section>
    );
  }

  if (!document) {
    return (
      <section className="workspace" aria-label="Document results">
        <div className="empty" role="status">
          Document could not be found.
        </div>
      </section>
    );
  }

  const isTerminal = isTerminalStatus(document.status);
  const blocks = document.extracted_data?.blocks ?? [];
  const pageRoutes = document.extracted_data?.page_routes ?? [];
  const warnings = document.extracted_data?.warnings ?? [];

  return (
    <section className="workspace" aria-label="Document results">
      <DocumentHeader document={document} />

      {documentError && (
        <div className="error" role="alert">
          <span>{documentError}</span>
          {onDismissError && (
            <button onClick={onDismissError} aria-label="Dismiss error">
              ×
            </button>
          )}
        </div>
      )}

      {document.error_message && (
        <div className="error" role="alert">
          <span>{document.error_message}</span>
        </div>
      )}

      <ExtractionWarnings warnings={warnings} />

      {!isTerminal && <ProcessingStatus />}

      {document.extracted_data && (
        <>
          <ContentTabs
            viewMode={viewMode}
            onViewChange={setViewMode}
            blocksCount={blocks.length}
          />

          <div className="content">
            {viewMode === "text" ? (
              <ReadableTextView text={document.rendered_text} />
            ) : (
              <StructuredBlocksView blocks={blocks} />
            )}
          </div>

          <PageRoutesView routes={pageRoutes} />
        </>
      )}
    </section>
  );
};
