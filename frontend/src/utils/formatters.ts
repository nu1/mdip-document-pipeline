import type { Location } from "../types/document";

const TERMINAL_STATUSES = new Set([
  "completed",
  "completed_with_warnings",
  "failed",
]);

/**
 * Checks if a document's processing status has reached a terminal state.
 */
export function isTerminalStatus(status: string): boolean {
  return TERMINAL_STATUSES.has(status);
}

/**
 * Converts snake_case strings into friendly human-readable titles.
 */
export function prettyText(value?: string | null): string {
  if (!value) return "";
  return value.replaceAll("_", " ");
}

/**
 * Formats a block's source location into a readable citation string.
 */
export function formatSourceLocation(location: Location): string {
  if (location.page !== undefined && location.page !== null) {
    return `Page ${location.page}`;
  }
  const blockNum = (location.block_index ?? 0) + 1;
  return `Body block ${blockNum}`;
}

/**
 * Formats bytes to human-readable megabytes / gigabytes.
 */
export function formatFileSize(bytes: number): string {
  if (bytes <= 0) return "0 B";
  const mib = bytes / (1024 * 1024);
  if (mib < 1) {
    const kib = bytes / 1024;
    return `${kib.toFixed(1)} KiB`;
  }
  return `${Number(mib.toFixed(1))} MiB`;
}

/**
 * Formats an ISO date string to a localized date representation.
 */
export function formatDate(dateString: string): string {
  try {
    const d = new Date(dateString);
    if (isNaN(d.getTime())) return dateString;
    return d.toLocaleDateString(undefined, {
      year: "numeric",
      month: "short",
      day: "numeric",
    });
  } catch {
    return dateString;
  }
}
