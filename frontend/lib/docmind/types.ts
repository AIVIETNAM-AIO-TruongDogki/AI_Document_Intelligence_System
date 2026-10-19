export interface DocumentItem {
  document_id: string
  filename: string
  file_size: number
  page_count: number
  created_at?: string
}

export interface JobProgress {
  job_id: string
  document_id: string
  status: "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED"
  progress: number
  error_message: string | null
}

export interface CitationSource {
  source_index: number
  chunk_id: string
  document_id: string
  filename?: string
  page_numbers: number[]
  snippet: string
}

export interface ChatMessage {
  id: string
  role: "user" | "assistant"
  content: string
  sources?: CitationSource[] | null
  created_at: string
}

export interface ChatSession {
  id: string
  title: string
  created_at: string
  updated_at: string
}

/** Client-side view of an ingestion job; extends the JobProgress contract with display metadata. */
export interface IngestionJob extends JobProgress {
  filename: string
  file_size: number
}

export interface DocumentChunk {
  chunk_id: string
  document_id: string
  page_numbers: number[]
  heading: string
  content: string
  snippet: string
}

export type ContextScope = "all" | "selected"

export type ApiStatus =
  | { state: "checking" }
  | { state: "connected"; latency: number }
  | { state: "offline" }
