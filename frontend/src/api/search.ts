import { apiClient } from "@/src/api/client";
import type { SearchRequest, SearchResponse } from "@/src/types/api";

/**
 * Tìm kiếm ngữ nghĩa (Semantic Search) trên các tài liệu đã index
 */
export async function searchDocuments(request: SearchRequest): Promise<SearchResponse> {
  return apiClient.post<SearchResponse>("/api/v1/search", request);
}
