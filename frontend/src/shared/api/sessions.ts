import { apiGet } from "./client";
import type { SessionDetailResponse } from "./types";

export function fetchSessionDetail(sessionId: string): Promise<SessionDetailResponse> {
  return apiGet<SessionDetailResponse>(`/api/v1/sessions/${encodeURIComponent(sessionId)}`);
}
