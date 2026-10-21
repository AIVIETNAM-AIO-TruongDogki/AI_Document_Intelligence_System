import { apiClient } from "@/src/api/client";
import type { HealthResponse } from "@/src/types/api";

/**
 * Kiểm tra trạng thái hoạt động của Backend API
 * @returns {Promise<HealthResponse>} Trạng thái backend ("ok") và tên ứng dụng ("DocMind")
 */
export async function checkHealth(): Promise<HealthResponse> {
  return apiClient.get<HealthResponse>("/health");
}
