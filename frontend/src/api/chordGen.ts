import type { ChordGenParams, ChordGenRun, ChordGenSuggestion, ChordLockSpec } from "../types";
import api from "./client";

export interface ChordGenRequest {
  project_id: string;
  clip_id?: string | null;
  bar_start: number;
  bar_end: number;
  seed: number;
  params: ChordGenParams;
  locks?: ChordLockSpec | null;
}

export interface ChordSuggestionPreviewRequest {
  bpm: number;
  time_signature_num?: number;
  time_signature_den?: number;
}

export interface ChordSuggestionApplyRequest {
  clip_id: string;
  replace_existing?: boolean;
}

export const chordGenApi = {
  async createRun(request: ChordGenRequest): Promise<ChordGenRun> {
    const response = await api.post<ChordGenRun>("/api/v1/chords/generate/run", request);
    return response.data;
  },

  async getRun(runId: string): Promise<ChordGenRun> {
    const response = await api.get<ChordGenRun>(`/api/v1/chords/generate/runs/${runId}`);
    return response.data;
  },

  async previewSuggestion(
    suggestionId: string,
    request: ChordSuggestionPreviewRequest
  ): Promise<{ suggestion_id: string; notes: any[]; chord_count: number }> {
    const response = await api.post<{ suggestion_id: string; notes: any[]; chord_count: number }>(
      `/api/v1/chords/generate/suggestions/${suggestionId}/preview`,
      request
    );
    return response.data;
  },

  async applySuggestion(
    suggestionId: string,
    request: ChordSuggestionApplyRequest
  ): Promise<{ suggestion_id: string; chords_created: number; chord_ids: string[] }> {
    const response = await api.post<{
      suggestion_id: string;
      chords_created: number;
      chord_ids: string[];
    }>(`/api/v1/chords/generate/suggestions/${suggestionId}/apply`, request);
    return response.data;
  },
};
