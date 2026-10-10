import React from "react";

export type ContentViewMode = "blocks" | "text";

interface ContentTabsProps {
  viewMode: ContentViewMode;
  onViewChange: (mode: ContentViewMode) => void;
  blocksCount: number;
}

export const ContentTabs: React.FC<ContentTabsProps> = ({
  viewMode,
  onViewChange,
  blocksCount,
}) => {
  return (
    <div className="tabs" role="tablist" aria-label="Document view modes">
      <button
        type="button"
        role="tab"
        aria-selected={viewMode === "blocks"}
        aria-pressed={viewMode === "blocks"}
        onClick={() => onViewChange("blocks")}
      >
        Structured blocks <span>{blocksCount}</span>
      </button>
      <button
        type="button"
        role="tab"
        aria-selected={viewMode === "text"}
        aria-pressed={viewMode === "text"}
        onClick={() => onViewChange("text")}
      >
        Readable text
      </button>
    </div>
  );
};
