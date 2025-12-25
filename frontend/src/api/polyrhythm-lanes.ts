import type { PolyrhythmLane, PolyrhythmLanesPreview } from "../types";
import api from "./client";

export const polyrhythmLanesApi = {
  async list(clipId: string): Promise<PolyrhythmLane[]> {
    const response = await api.get<PolyrhythmLane[]>(`/clips/${clipId}/polyrhythm-lanes`);
    return response.data;
  },

  async create(clipId: string, data: Partial<PolyrhythmLane>): Promise<PolyrhythmLane> {
    const response = await api.post<PolyrhythmLane>(`/clips/${clipId}/polyrhythm-lanes`, data);
    return response.data;
  },

  async update(laneId: string, data: Partial<PolyrhythmLane>): Promise<PolyrhythmLane> {
    const response = await api.put<PolyrhythmLane>(`/polyrhythm-lanes/${laneId}`, data);
    return response.data;
  },

  async delete(laneId: string): Promise<void> {
    await api.delete(`/polyrhythm-lanes/${laneId}`);
  },

  async preview(projectId: string, clipId: string): Promise<PolyrhythmLanesPreview> {
    const response = await api.post<PolyrhythmLanesPreview>(
      `/polyrhythms/preview-lanes?project_id=${projectId}&clip_id=${clipId}`
    );
    return response.data;
  },
};
