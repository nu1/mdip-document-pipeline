import { useCallback, useEffect, useState } from "react";
import { getDocuments } from "../api/documents";
import type { DocumentItem } from "../types/document";
import { isTerminalStatus } from "../utils/formatters";

export function useDocuments(page: number, pageSize: number = 20, refreshKey?: unknown) {
  const [documents, setDocuments] = useState<DocumentItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string>("");

  const fetchList = useCallback(async () => {
    try {
      const rows = await getDocuments({
        limit: pageSize,
        offset: page * pageSize,
      });
      setDocuments(rows);
      setError("");
      return rows;
    } catch (err) {
      const message = err instanceof Error ? err.message : "Failed to load documents.";
      setError(message);
      throw err;
    }
  }, [page, pageSize]);

  useEffect(() => {
    let active = true;
    let timer: ReturnType<typeof setTimeout> | undefined;

    async function poll() {
      if (!active) return;
      try {
        const rows = await fetchList();
        if (!active) return;

        // If any document is still processing, poll more frequently (1s)
        const hasProcessing = rows.some((d) => !isTerminalStatus(d.status));
        if (hasProcessing) {
          timer = setTimeout(poll, 1000);
        }
      } catch {
        if (active) {
          // On network/server error, retry with slower backoff (3s)
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
  }, [fetchList, refreshKey]);

  return {
    documents,
    isLoading,
    error,
    setError,
    refetch: fetchList,
  };
}
