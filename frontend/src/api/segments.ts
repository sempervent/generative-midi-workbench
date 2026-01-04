import type { SegmentCreateRequest, SegmentGenerateResponse } from "../types";
import api from "./client";

export const segmentsApi = {
  async generateSegments(request: SegmentCreateRequest): Promise<SegmentGenerateResponse> {
    const response = await api.post<SegmentGenerateResponse>("/segments/generate", request);
    return response.data;
  },
};
