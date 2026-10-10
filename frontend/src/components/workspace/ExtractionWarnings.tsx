import React from "react";
import { prettyText } from "../../utils/formatters";

interface ExtractionWarningsProps {
  warnings: string[];
}

export const ExtractionWarnings: React.FC<ExtractionWarningsProps> = ({ warnings }) => {
  if (!warnings || warnings.length === 0) return null;

  return (
    <div className="warnings" role="region" aria-label="Extraction notes">
      <strong>Extraction notes</strong>
      <ul>
        {warnings.map((w, index) => (
          <li key={index}>{prettyText(w)}</li>
        ))}
      </ul>
    </div>
  );
};
