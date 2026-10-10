import { apiClient } from "./client";
import type { HealthResponse, PaginationParams, UploadResponse } from "../types/api";
import type { DocumentItem } from "../types/document";

/**
 * Fetches server health and configuration limits (e.g. max_upload_bytes).
 */
export async function getHealth(): Promise<HealthResponse> {
  return apiClient<HealthResponse>("/health");
}

/**
 * Fetches paginated document list.
 */
export async function getDocuments(
  params: PaginationParams = {},
  signal?: AbortSignal,
): Promise<DocumentItem[]> {
  const { limit = 20, offset = 0 } = params;
  return apiClient<DocumentItem[]>(`/documents?limit=${limit}&offset=${offset}`, {
    signal,
  });
}

/**
 * Fetches single document details, extracted data, and status.
 */
export async function getDocument(
  id: string,
  signal?: AbortSignal,
): Promise<DocumentItem> {
  return apiClient<DocumentItem>(`/documents/${encodeURIComponent(id)}`, {
    signal,
  });
}

/**
 * Uploads a document file using multipart/form-data.
 */
export async function uploadDocument(file: File): Promise<UploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  return apiClient<UploadResponse>("/documents", {
    method: "POST",
    body: formData,
  });
}
