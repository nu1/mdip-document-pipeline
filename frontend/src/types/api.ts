export type HealthResponse = {
  max_upload_bytes: number;
};

export type UploadResponse = {
  id: string;
};

export type PaginationParams = {
  limit?: number;
  offset?: number;
};

export type ApiErrorDetail = {
  detail?: string;
  message?: string;
};
