import React from "react";

interface ErrorBannerProps {
  errors: (string | null | undefined)[];
  onDismiss: () => void;
}

export const ErrorBanner: React.FC<ErrorBannerProps> = ({ errors, onDismiss }) => {
  const activeErrors = errors.filter(Boolean);
  if (activeErrors.length === 0) return null;

  return (
    <div className="error" role="alert">
      <span>{activeErrors.join(" ")}</span>
      <button onClick={onDismiss} aria-label="Dismiss error">
        ×
      </button>
    </div>
  );
};
