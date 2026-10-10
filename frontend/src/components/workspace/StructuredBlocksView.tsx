import React from "react";
import type { Block } from "../../types/document";
import { formatSourceLocation, prettyText } from "../../utils/formatters";

interface StructuredBlocksViewProps {
  blocks: Block[];
}

export const StructuredBlocksView: React.FC<StructuredBlocksViewProps> = ({ blocks }) => {
  if (blocks.length === 0) {
    return (
      <p className="muted">
        No extractable content was recovered. Review any extraction notes below.
      </p>
    );
  }

  return (
    <>
      {blocks.map((block) => (
        <article className="block" key={block.order}>
          <div className="block-label">
            <span>
              {formatSourceLocation(block.source_location)} ·{" "}
              {prettyText(block.extraction_method)}
            </span>
            <span>{block.type}</span>
          </div>

          {block.type === "table" ? (
            <div className="table-wrap">
              <table>
                <tbody>
                  {(block.rows ?? []).map((row, rowIndex) => (
                    <tr key={rowIndex}>
                      {row.map((cell, colIndex) => (
                        <td key={colIndex}>{cell}</td>
                      ))}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : block.type === "heading" ? (
            <h3>{block.text}</h3>
          ) : (
            <p>{block.text}</p>
          )}
        </article>
      ))}
    </>
  );
};
