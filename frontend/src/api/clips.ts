import type { Clip } from "../types";
import api from "./client";

export interface ClipUpdate {
  start_bar?: number;
  length_bars?: number;
  is_muted?: boolean;
  is_soloed?: boolean;
  intensity?: number;
  params?: Record<string, any>;
}

export interface ClipDuplicate {
  new_start_bar?: number;
}

export interface ClipTimeScale {
  mode: "half" | "double";
}

export interface ClipOffset {
  bars: number;
}

export interface ClipRegenerate {
  scope: "beats" | "chords" | "bass" | "melody" | "all";
  seed?: number;
}

export const clipsApi = {
  async update(clipId: string, data: ClipUpdate): Promise<Clip> {
    const response = await api.patch<Clip>(`/api/v1/clips/${clipId}`, data);
    return response.data;
  },

  async duplicate(clipId: string, data: ClipDuplicate): Promise<Clip> {
    const response = await api.post<Clip>(`/api/v1/clips/${clipId}/duplicate`, data);
    return response.data;
  },

  async timeScale(clipId: string, data: ClipTimeScale): Promise<Clip> {
    const response = await api.post<Clip>(`/api/v1/clips/${clipId}/time-scale`, data);
    return response.data;
  },

  async offset(clipId: string, data: ClipOffset): Promise<Clip> {
    const response = await api.post<Clip>(`/api/v1/clips/${clipId}/offset`, data);
    return response.data;
  },

  async regenerate(clipId: string, data: ClipRegenerate): Promise<any> {
    const response = await api.post<any>(`/api/v1/clips/${clipId}/regenerate`, data);
    return response.data;
  },

  async previewRegenerate(clipId: string, data: ClipRegenerate): Promise<any> {
    const response = await api.post<any>(`/api/v1/clips/${clipId}/preview-regenerate`, data);
    return response.data;
  },
};
