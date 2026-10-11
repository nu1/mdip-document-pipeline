import React from "react";

interface HeaderProps {
  section: "documents" | "agents";
  onSectionChange: (section: "documents" | "agents") => void;
}

export const Header: React.FC<HeaderProps> = ({ section, onSectionChange }) => {
  return (
    <header>
      <a className="brand" href="/" aria-label="Fletchers AI Home">
        fletchers<span> / ai</span>
      </a>
      <nav className="header-nav" aria-label="Workspace sections">
        <button aria-pressed={section === "documents"} onClick={() => onSectionChange("documents")}>
          Documents
        </button>
        <button aria-pressed={section === "agents"} onClick={() => onSectionChange("agents")}>
          For Agents
        </button>
      </nav>
    </header>
  );
};
