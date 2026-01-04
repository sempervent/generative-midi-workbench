import type { Arrangement, GenerationRequest, Project } from "../types";
import api from "./client";

export const projectsApi = {
  async list(): Promise<Project[]> {
    const response = await api.get<Project[]>("/projects");
    return response.data;
  },

  async get(id: string): Promise<Project> {
    const response = await api.get<Project>(`/projects/${id}`);
    return response.data;
  },

  async create(data: Partial<Project>): Promise<Project> {
    const response = await api.post<Project>("/projects", data);
    return response.data;
  },

  async update(id: string, data: Partial<Project>): Promise<Project> {
    const response = await api.patch<Project>(`/projects/${id}`, data);
    return response.data;
  },

  async getArrangement(id: string): Promise<Arrangement> {
    const response = await api.get<Arrangement>(`/projects/${id}/arrangement`);
    return response.data;
  },

  async generate(id: string, kind: string, seed?: number, params?: Record<string, any>) {
    const response = await api.post(`/projects/${id}/generate/${kind}`, {
      kind,
      seed,
      params: params || {},
    });
    return response.data;
  },

  async exportMidi(id: string): Promise<Blob> {
    const response = await api.get(`/projects/${id}/export/midi`, {
      responseType: "blob",
    });
    return response.data;
  },

  async exportZip(id: string, splitBy: "track" | "clip" = "track"): Promise<Blob> {
    const response = await api.get(`/projects/${id}/export/zip`, {
      params: { split_by: splitBy },
      responseType: "blob",
    });
    return response.data;
  },
};
