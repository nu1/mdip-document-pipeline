import { useEffect, useState } from "react";
import { getDocument } from "../api/documents";
import type { DocumentItem } from "../types/document";
import { isTerminalStatus } from "../utils/formatters";

export function useDocumentDetail(selectedId: string | null) {
  const [document, setDocument] = useState<DocumentItem | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>("");

  useEffect(() => {
    if (!selectedId) {
      return;
    }

    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;

    async function poll() {
      if (!active || !selectedId) return;
      try {
        const result = await getDocument(selectedId);
        if (!active) return;
        setDocument(result);
        setError("");

        // Continue polling while in non-terminal state
        if (!isTerminalStatus(result.status)) {
          timer = setTimeout(poll, 700);
        }
      } catch (err) {
        if (active) {
          const message =
            err instanceof Error ? err.message : "Failed to load document details.";
          setError(message);
          // Retry poll after 3s on error
          timer = setTimeout(poll, 3000);
        }
      } finally {
        if (active) {
          setIsLoading(false);
        }
      }
    }

    poll();

    return () => {
      active = false;
      if (timer) clearTimeout(timer);
    };
  }, [selectedId]);

  // Derive active document matching selectedId to avoid synchronous reset in effect
  const activeDocument = document?.id === selectedId ? document : null;
  const isWaiting = Boolean(selectedId && !activeDocument && !error);

  return {
    document: activeDocument,
    isLoading: isWaiting || isLoading,
    error,
    setError,
  };
}
