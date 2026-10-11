import React from "react";
import type { PageRoute } from "../../types/document";
import { prettyText } from "../../utils/formatters";
import { Badge } from "../common/Badge";

interface PageRoutesViewProps {
  routes: PageRoute[];
}

export const PageRoutesView: React.FC<PageRoutesViewProps> = ({ routes }) => {
  if (!routes || routes.length === 0) return null;

  return (
    <section className="routes" aria-label="Page extraction decisions">
      <h3>Page decisions</h3>
      <p className="muted">
        Native text and image geometry determine each page’s route.
      </p>
      {routes.map((route) => (
        <details key={route.page}>
          <summary>
            <span>Page {route.page}</span>
            <Badge status={route.route} />
            <span>{prettyText(route.reason)}</span>
            {route.fallback && (
              <span>AI fallback{route.fallback.provider.mocked ? " (mock)" : ""}: {prettyText(route.fallback.status)}</span>
            )}
          </summary>
          {route.fallback && (
            <p>
              Fallback reason: {prettyText(route.fallback.reason)}. Provider: {route.fallback.provider.name}
              {" "}({route.fallback.provider.version}).
              {route.fallback.provider.mocked && " Mock demonstration; no external service was called."}
            </p>
          )}
          {route.fallback?.note && <p>{route.fallback.note}</p>}
          {(route.warnings ?? [])
            .filter((warning) => !route.fallback?.note || !warning.startsWith("ai_fallback_note:"))
            .map((warning, index) => (
            <p className="warning-text" key={index}>
              {prettyText(warning)}
            </p>
          ))}
          <pre>{JSON.stringify(route.signals, null, 2)}</pre>
        </details>
      ))}
    </section>
  );
};
