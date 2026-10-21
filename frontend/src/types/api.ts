/**
 * API Type Definitions for DocMind Frontend
 * Synchronized with backend Pydantic schemas in app/api/schemas/
 */

export interface HealthResponse {
  status: string;
  app_name: string;
}

export interface Chunk {
  chunk_id: string;
  document_id: string;
  text: string;
  page_numbers: number[];
  token_count: number;
}

export interface DocumentUploadResponse {
  document_id: string;
  filename: string;
  page_count: number;
  chunk_count: number;
  message: string;
}

export interface DocumentDetail {
  document_id: string;
  filename: string;
  page_count: number;
  chunks: Chunk[];
}

export interface DocumentListItem {
  document_id: string;
  filename: string;
  file_size: number;
  page_count: number;
}

export interface SearchRequest {
  query: string;
  top_k?: number;
  document_id?: string | null;
}

export interface SearchResult {
  chunk_id: string;
  document_id: string;
  text: string;
  page_numbers: number[];
  score: number;
}

export interface SearchResponse {
  query: string;
  total_results: number;
  results: SearchResult[];
}

export interface ChatRequest {
  query: string;
  document_id?: string | null;
  top_k?: number;
  session_id?: string | null;
}

export interface Source {
  source_index: number;
  chunk_id: string;
  document_id: string;
  page_numbers: number[];
  snippet: string;
}

export interface TokenUsage {
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
}

export interface ChatResponse {
  session_id: string;
  answer: string;
  sources: Source[];
  model: string;
  usage: TokenUsage;
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  sources?: Source[] | null;
  tokens_used?: Record<string, number> | null;
  created_at: string;
}

export interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
}

export interface ChatSessionDetail extends ChatSession {
  messages: ChatMessage[];
}
