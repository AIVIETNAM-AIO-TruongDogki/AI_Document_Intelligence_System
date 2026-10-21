import { apiClient } from "@/src/api/client";
import type {
  DocumentDetail,
  DocumentListItem,
  DocumentUploadResponse,
} from "@/src/types/api";

/**
 * Tải lên tệp PDF để backend phân tích, chia đoạn và vector hóa
 */
export async function uploadDocument(file: File): Promise<DocumentUploadResponse> {
  const formData = new FormData();
  formData.append("file", file);

  return apiClient.post<DocumentUploadResponse>("/api/v1/documents/upload", formData);
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
