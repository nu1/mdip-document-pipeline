import { useEffect, useState } from "react";
import { getHealth } from "../api/documents";

const DEFAULT_MAX_BYTES = 10 * 1024 * 1024; // 10 MiB

export function useHealth() {
  const [maxUploadBytes, setMaxUploadBytes] = useState<number>(DEFAULT_MAX_BYTES);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    let active = true;
    getHealth()
      .then((res) => {
        if (active && res.max_upload_bytes) {
          setMaxUploadBytes(res.max_upload_bytes);
        }
      })
      .catch(() => {
        // Fallback to default limit silently
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, []);

  return { maxUploadBytes, isLoading };
}
