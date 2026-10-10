import React from "react";

interface ReadableTextViewProps {
  text?: string;
}

export const ReadableTextView: React.FC<ReadableTextViewProps> = ({ text }) => {
  if (!text || text.trim() === "") {
    return <p className="muted">No readable text available for this document.</p>;
  }

  return <pre>{text}</pre>;
};
