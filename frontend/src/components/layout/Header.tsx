import React from "react";

export const Header: React.FC = () => {
  return (
    <header>
      <a className="brand" href="/" aria-label="Fletchers AI Home">
        fletchers<span> / ai</span>
      </a>
      <span className="local">
        <i aria-hidden="true" /> Document processing workspace
      </span>
    </header>
  );
};
