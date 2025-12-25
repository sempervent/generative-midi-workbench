import api from "./client";

export interface SuggestionRun {
  id: string;
  project_id: string;
  seed: number;
  context_json: Record<string, any>;
  params_json: Record<string, any>;
  created_at: string;
  suggestions: Suggestion[];
}

export interface Suggestion {
  id: string;
  run_id: string;
  kind: "harmony" | "rhythm" | "melody";
  title: string;
  explanation: string;
  score: number;
  payload_json: {
    preview_events: PreviewEvent[];
    commit_plan: Record<string, any>;
  };
  is_committed: boolean;
  committed_at: string | null;
  created_at: string;
}

export interface PreviewEvent {
  pitch: number;
  velocity: number;
  start_tick: number;
  duration_tick: number;
  channel: number;
}

export interface PreviewResponse {
  explanation: string;
  preview_events: PreviewEvent[];
}

export const suggestionsApi = {
  async createRun(
    projectId: string,
    seed?: number,
    params?: Record<string, any>
  ): Promise<SuggestionRun> {
    const response = await api.post<SuggestionRun>("/suggestions/run", {
      project_id: projectId,
      seed,
      params: params || {},
    });
    return response.data;
  },

  async getRun(runId: string): Promise<SuggestionRun> {
    const response = await api.get<SuggestionRun>(`/suggestions/runs/${runId}`);
    return response.data;
  },

  async commitSuggestion(suggestionId: string) {
    const response = await api.post(`/suggestions/${suggestionId}/commit`);
    return response.data;
  },

  async preview(
    projectId: string,
    kind: string,
    seed?: number,
    params?: Record<string, any>
  ): Promise<PreviewResponse> {
    const response = await api.post<PreviewResponse>("/suggestions/preview", {
      project_id: projectId,
      kind,
      seed,
      params: params || {},
    });
    return response.data;
  },
};
