import type { PolyrhythmProfile } from "../types";
import api from "./client";

export const polyrhythmsApi = {
  async list(): Promise<PolyrhythmProfile[]> {
    const response = await api.get<PolyrhythmProfile[]>("/polyrhythms");
    return response.data;
  },

  async get(id: string): Promise<PolyrhythmProfile> {
    const response = await api.get<PolyrhythmProfile>(`/polyrhythms/${id}`);
    return response.data;
  },

  async create(data: Partial<PolyrhythmProfile>): Promise<PolyrhythmProfile> {
    const response = await api.post<PolyrhythmProfile>("/polyrhythms", data);
    return response.data;
  },

  async update(id: string, data: Partial<PolyrhythmProfile>): Promise<PolyrhythmProfile> {
    const response = await api.put<PolyrhythmProfile>(`/polyrhythms/${id}`, data);
    return response.data;
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/polyrhythms/${id}`);
  },

  async preview(
    projectId: string,
    params: {
      steps: number;
      pulses: number;
      rotation?: number;
      cycle_beats: number;
      swing?: number | null;
      clip_start_bar?: number;
      clip_length_bars?: number;
      pitch?: number;
      velocity?: number;
    }
  ) {
    const response = await api.post(`/polyrhythms/preview?project_id=${projectId}`, params);
    return response.data;
  },
};
