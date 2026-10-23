import { apiClient } from "@/src/api/client";
import type {
  AsyncUploadResponse,
  DocumentDetail,
  DocumentListItem,
  DocumentUploadResponse,
} from "@/src/types/api";

/**
 * Tải lên tệp PDF để backend phân tích, chia đoạn và vector hóa (hỗ trợ bất đồng bộ qua asyncMode)
 */
export async function uploadDocument(
  file: File,
  asyncMode: boolean = true
): Promise<AsyncUploadResponse | DocumentUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  const endpoint = asyncMode
    ? "/api/v1/documents/upload"
    : "/api/v1/documents/upload?async_mode=false";

  return apiClient.post<AsyncUploadResponse | DocumentUploadResponse>(endpoint, formData);
}

/**
 * Lấy danh sách toàn bộ tài liệu đã được lưu trữ trong hệ thống
 */
export async function listDocuments(): Promise<DocumentListItem[]> {
  return apiClient.get<DocumentListItem[]>("/api/v1/documents");
}

/**
 * Xem chi tiết tài liệu kèm danh sách các chunks đã trích xuất
 */
export async function getDocumentDetail(documentId: string): Promise<DocumentDetail> {
  return apiClient.get<DocumentDetail>(`/api/v1/documents/${documentId}`);
}

/**
 * Xóa một tài liệu theo ID
 */
export async function deleteDocument(documentId: string): Promise<void> {
  return apiClient.delete<void>(`/api/v1/documents/${documentId}`);
}
