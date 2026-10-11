import React from "react";

export const Intro: React.FC = () => {
  return (
    <div className="intro">
      <div>
        <h1>Document processing</h1>
        <p className="subtitle">
          Upload source files, monitor extraction and review saved results.
        </p>
      </div>
      <span className="edition">
        DOCX & PDF PIPELINE
        <br />
        LOCAL STORAGE
      </span>
    </div>
  );
};
