import api from "./client";

export interface ChordSuggestRequest {
  project_id: string;
  context_bar?: number;
  num_suggestions?: number;
  seed?: number;
  style?: string;
  tension?: number;
  cadence_bias?: number;
  include_borrowed?: boolean;
  include_secondary_dominants?: boolean;
  include_chromatic?: boolean;
}

export interface ChordSuggestion {
  roman_numeral: string;
  chord_name: string;
  reason: string;
  score: number;
  explanation?: string;
}

export interface ChordSuggestResponse {
  suggestions: ChordSuggestion[];
  context_key: string;
  context_mode: string;
}

export const chordSuggestApi = {
  async suggest(request: ChordSuggestRequest): Promise<ChordSuggestResponse> {
    const response = await api.post<ChordSuggestResponse>("/api/v1/chords/suggest", request);
    return response.data;
  },
};

