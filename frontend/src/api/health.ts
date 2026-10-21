import { apiClient } from "@/src/api/client";
import type { HealthResponse } from "@/src/types/api";

/**
 * Kiểm tra trạng thái hoạt động của Backend API
 * @returns {Promise<HealthResponse>} Trạng thái backend ("ok") và tên ứng dụng ("DocMind")
 */
export async function checkHealth(): Promise<HealthResponse> {
  return apiClient.get<HealthResponse>("/health");
}

/**
 * Kiểm tra kết nối Backend kèm tính toán độ trễ (latency ms)
 */
export async function checkHealthStatus(): Promise<{ ok: boolean; latency: number }> {
  const start = performance.now();
  try {
    const res = await checkHealth();
    const latency = Math.round(performance.now() - start);
    return { ok: res.status === "ok", latency };
  } catch {
    return { ok: false, latency: 0 };
  }
}
