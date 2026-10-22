import { apiClient } from "@/src/api/client";
import type { JobResponse } from "@/src/types/api";

/**
 * Kiểm tra trạng thái và tiến độ xử lý nền của một Job
 */
export async function getJobStatus(jobId: string): Promise<JobResponse> {
  return apiClient.get<JobResponse>(`/api/v1/jobs/${jobId}`);
}

/**
 * Lấy danh sách các jobs gần đây
 */
export async function listJobs(): Promise<JobResponse[]> {
  return apiClient.get<JobResponse[]>("/api/v1/jobs");
}
