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
          </summary>
          {(route.warnings ?? []).map((warning, index) => (
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
