export type Location = {
  page?: number;
  block_index?: number;
  paragraph_index?: number;
  bbox?: [number, number, number, number];
};

export type BlockType = "heading" | "paragraph" | "table";

export type Block = {
  type: BlockType;
  order: number;
  text: string;
  level?: number;
  rows?: string[][];
  source_location: Location;
  extraction_method: string;
};

export type PageRoute = {
  page: number;
  route: string;
  reason: string;
  signals: Record<string, unknown>;
  warnings: string[];
};

export type ExtractionData = {
  blocks: Block[];
  page_routes: PageRoute[];
  warnings: string[];
};

export type DocumentStatus =
  | "pending"
  | "processing"
  | "completed"
  | "completed_with_warnings"
  | "failed"
  | string;

export type DocumentItem = {
  id: string;
  filename: string;
  status: DocumentStatus;
  processing_stage: string;
  processed_pages: number | null;
  total_pages: number | null;
  created_at: string;
  error_message: string | null;
  rendered_text?: string;
  extracted_data?: ExtractionData | null;
};

export type DocumentChunksResponse = {
  document_id: string;
  filename: string;
  status: DocumentStatus;
  processing_stage: string;
  warnings: string[];
  error_message: string | null;
  chunks: {
    id: string;
    document_id: string;
    chunk_index: number;
    text: string;
    source_location: Location;
    metadata: { extraction_method: string; block_order: number; type: BlockType };
  }[];
  next_offset: number | null;
};
