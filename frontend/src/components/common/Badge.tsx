import React from "react";
import { prettyText } from "../../utils/formatters";

interface BadgeProps {
  status: string;
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ status, className = "" }) => {
  const normalizedClass = status.toLowerCase().replace(/\s+/g, "_");
  return (
    <span className={`badge ${normalizedClass} ${className}`.trim()}>
      {prettyText(status)}
    </span>
  );
};
