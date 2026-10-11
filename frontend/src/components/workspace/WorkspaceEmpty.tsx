import React from "react";

export const WorkspaceEmpty: React.FC = () => {
  return (
    <div className="empty">
      <div className="empty-sheet" aria-hidden="true">
        <span />
        <span />
        <span />
        <div>¶</div>
      </div>

      <p className="eyebrow">DOCUMENT REVIEW</p>
      <h2>Select a document to review</h2>
      <p className="empty-intro">
        Upload a source DOCX or PDF file or choose a saved document to inspect its
        extracted content, structure, and processing details.
      </p>

      <div className="empty-features" aria-label="Supported document details">
        <div className="feature-card">
          <strong>Processing status</strong>
          <p>
            Track ingestion stages from queued and processing through to
            completion or failure.
          </p>
        </div>
        <div className="feature-card">
          <strong>Extracted content</strong>
          <p>
            Review ordered headings, body paragraphs, and DOCX tables in
            tabbed block or readable text views.
          </p>
        </div>
        <div className="feature-card">
          <strong>Source locations</strong>
          <p>
            Inspect sequential body block indices and page numbers that map each
            element back to its position in the source file.
          </p>
        </div>
        <div className="feature-card">
          <strong>Extraction warnings</strong>
          <p>
            Flag unextracted content such as images, text boxes, shapes, or
            nested tables.
          </p>
        </div>
      </div>

      <div className="steps" aria-label="Processing stages">
        <span>01 Upload DOCX or PDF</span>
        <span>02 Ingest & extract</span>
        <span>03 Review content & citations</span>
      </div>
    </div>
  );
};
