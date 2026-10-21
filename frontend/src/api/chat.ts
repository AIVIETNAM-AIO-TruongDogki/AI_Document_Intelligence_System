import { apiClient } from "@/src/api/client";
import type {
  ChatRequest,
  ChatResponse,
  ChatSession,
  ChatSessionDetail,
} from "@/src/types/api";

/**
 * Gửi câu hỏi đến hệ thống RAG Backend để lấy câu trả lời kèm trích dẫn
 */
export async function sendChatMessage(request: ChatRequest): Promise<ChatResponse> {
  return apiClient.post<ChatResponse>("/api/v1/chat", request);
}

/**
 * Lấy danh sách toàn bộ các phiên trò chuyện
 */
export async function listChatSessions(): Promise<ChatSession[]> {
  return apiClient.get<ChatSession[]>("/api/v1/chat/sessions");
}

/**
 * Lấy chi tiết phiên trò chuyện kèm toàn bộ lịch sử tin nhắn
 */
export async function getChatSessionDetail(
  sessionId: string
): Promise<ChatSessionDetail> {
  return apiClient.get<ChatSessionDetail>(`/api/v1/chat/sessions/${sessionId}`);
}

/**
 * Xóa một phiên trò chuyện theo ID
 */
export async function deleteChatSession(sessionId: string): Promise<void> {
  return apiClient.delete<void>(`/api/v1/chat/sessions/${sessionId}`);
}
