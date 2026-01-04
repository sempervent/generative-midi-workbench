import api from "./client";

export interface ChordProjectionProfile {
  id: string;
  name: string;
  kind: "block" | "arpeggio" | "broken" | "rhythm_pattern";
  settings: Record<string, any> | null;
  created_at: string;
  updated_at: string;
}

export interface ChordProjectionProfileCreate {
  name: string;
  kind: "block" | "arpeggio" | "broken" | "rhythm_pattern";
  settings?: Record<string, any> | null;
}

export const chordProjectionsApi = {
  async list(): Promise<ChordProjectionProfile[]> {
    const response = await api.get<ChordProjectionProfile[]>("/chord-projections");
    return response.data;
  },

  async create(data: ChordProjectionProfileCreate): Promise<ChordProjectionProfile> {
    const response = await api.post<ChordProjectionProfile>("/chord-projections", data);
    return response.data;
  },

  async get(id: string): Promise<ChordProjectionProfile> {
    const response = await api.get<ChordProjectionProfile>(`/chord-projections/${id}`);
    return response.data;
  },

  async update(
    id: string,
    data: Partial<ChordProjectionProfileCreate>
  ): Promise<ChordProjectionProfile> {
    const response = await api.put<ChordProjectionProfile>(`/chord-projections/${id}`, data);
    return response.data;
  },

  async delete(id: string): Promise<void> {
    await api.delete(`/chord-projections/${id}`);
  },
};
