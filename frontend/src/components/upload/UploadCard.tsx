import React, { useRef, useState } from "react";
import { uploadDocument } from "../../api/documents";
import { formatFileSize } from "../../utils/formatters";

interface UploadCardProps {
  maxBytes: number;
  onUploadSuccess: (id: string) => void;
  onError: (error: string) => void;
  onUploadingChange?: (uploading: boolean) => void;
}

export const UploadCard: React.FC<UploadCardProps> = ({
  maxBytes,
  onUploadSuccess,
  onError,
  onUploadingChange,
}) => {
  const [uploading, setUploading] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleUpload = async (file?: File) => {
    if (!file) return;

    if (!/\.(docx)$/i.test(file.name)) {
      onError("Please select a DOCX file.");
      return;
    }

    if (file.size > maxBytes) {
      onError(`File exceeds maximum size limit of ${formatFileSize(maxBytes)}.`);
      return;
    }

    setUploading(true);
    onUploadingChange?.(true);

    try {
      const result = await uploadDocument(file);
      onUploadSuccess(result.id);
    } catch (err) {
      const message = err instanceof Error ? err.message : "Upload failed.";
      onError(message);
    } finally {
      setUploading(false);
      onUploadingChange?.(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  };

  const onDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    if (!uploading) setIsDragging(true);
  };

  const onDragLeave = () => {
    setIsDragging(false);
  };

  const onDrop = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (uploading) return;
    const file = e.dataTransfer.files?.[0];
    if (file) {
      handleUpload(file);
    }
  };

  return (
    <section
      className={`upload ${isDragging ? "dragging" : ""}`}
      onDragOver={onDragOver}
      onDragLeave={onDragLeave}
      onDrop={onDrop}
      aria-label="Upload document section"
    >
      <div className="upload-icon" aria-hidden="true">
        ↑
      </div>
      <h2>Upload document</h2>
      <p>
        Extract ordered headings, body text and tables with source block locations.
      </p>
      <input
        ref={fileInputRef}
        id="file-upload-input"
        type="file"
        accept=".docx"
        disabled={uploading}
        onChange={(e) => handleUpload(e.target.files?.[0])}
        aria-label="Upload DOCX document"
      />
      <label
        htmlFor="file-upload-input"
        className={`button ${uploading ? "disabled" : ""}`}
      >
        <span>{uploading ? "Uploading…" : "Choose DOCX file"}</span>
        <span aria-hidden="true">↗</span>
      </label>
      <small>DOCX · up to {formatFileSize(maxBytes)}</small>
    </section>
  );
};
