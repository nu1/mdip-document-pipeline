import React from "react";

export const ProcessingStatus: React.FC = () => {
  return (
    <div className="processing" role="status" aria-live="polite">
      <span className="pulse" aria-hidden="true" />
      <span>Processing document. Status updates automatically.</span>
    </div>
  );
};
