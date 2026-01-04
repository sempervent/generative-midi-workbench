import api from "./client";

export interface ClipChordSettings {
  id: string;
  clip_id: string;
  projection_profile_id: string | null;
  gate_pct: number;
  strum_ms: number;
  humanize_ms: number;
  offset_ticks: number;
  subdivision: string;
  pattern: Record<string, any> | null;
  voicing_low_midi: number;
  voicing_high_midi: number;
  inversion_policy: string;
  created_at: string;
  updated_at: string;
}

export interface ClipChordSettingsUpdate {
  projection_profile_id?: string | null;
  gate_pct?: number;
  strum_ms?: number;
  humanize_ms?: number;
  offset_ticks?: number;
  subdivision?: string;
  pattern?: Record<string, any> | null;
  voicing_low_midi?: number;
  voicing_high_midi?: number;
  inversion_policy?: string;
}

export interface NoteEvent {
  pitch: number;
  start_tick: number;
  duration_tick: number;
  velocity: number;
}

export interface ChordPreviewRequest {
  project_id: string;
  bars_range?: [number, number] | null;
  progression_source: string;
  chord_events?: Array<{
    start_tick: number;
    duration_tick: number;
    roman_numeral: string;
    chord_name: string;
  }> | null;
  suggestion_id?: string | null;
  settings: Record<string, any>;
  seed?: number | null;
}

export interface ChordPreviewResponse {
  note_events: NoteEvent[];
  summary: Record<string, any>;
}

export interface ChordCommitRequest {
  project_id: string;
  clip_id: string;
  settings: Record<string, any>;
  seed?: number | null;
  commit_key?: string | null;
}

export interface ChordCommitResponse {
  clip_id: string;
  notes_created: number;
  notes_updated: number;
}

export interface ChordEventCreate {
  clip_id: string;
  start_tick: number;
  duration_tick: number;
  duration_beats: number;
  roman_numeral: string;
  chord_name: string;
  intensity?: number;
  voicing?: string;
  inversion?: number;
  strum_ms?: number;
  humanize_ms?: number;
  velocity_jitter?: number;
  timing_jitter_ms?: number;
  is_enabled?: boolean;
  is_locked?: boolean;
  grid_quantum?: number | null;
}

export interface ChordEventUpdate {
  start_tick?: number;
  duration_tick?: number;
  duration_beats?: number;
  roman_numeral?: string;
  chord_name?: string;
  intensity?: number;
  voicing?: string;
  inversion?: number;
  strum_ms?: number;
  humanize_ms?: number;
  velocity_jitter?: number;
  timing_jitter_ms?: number;
  is_enabled?: boolean;
  is_locked?: boolean;
  grid_quantum?: number | null;
}

export interface ChordInsertRequest {
  project_id: string;
  start_bar: number;
  duration_bars: number;
  roman_numeral: string;
  chord_name: string;
  intensity?: number;
  voicing?: string;
  inversion?: number;
  strum_beats?: number;
  humanize_beats?: number;
  duration_gate?: number;
  pattern_type?: string;
  velocity_curve?: string;
  comp_pattern?: any;
  strum_direction?: string;
  strum_spread?: number;
  retrigger?: boolean;
}

export const chordsApi = {
  async getClipSettings(clipId: string): Promise<ClipChordSettings> {
    const response = await api.get<ClipChordSettings>(`/chords/clips/${clipId}/settings`);
    return response.data;
  },

  async updateClipSettings(
    clipId: string,
    data: ClipChordSettingsUpdate
  ): Promise<ClipChordSettings> {
    const response = await api.put<ClipChordSettings>(`/chords/clips/${clipId}/settings`, data);
    return response.data;
  },

  async preview(request: ChordPreviewRequest): Promise<ChordPreviewResponse> {
    const response = await api.post<ChordPreviewResponse>("/chords/preview", request);
    return response.data;
  },

  async commit(request: ChordCommitRequest): Promise<ChordCommitResponse> {
    const response = await api.post<ChordCommitResponse>("/chords/commit", request);
    return response.data;
  },

  async list(projectId: string, startBar?: number, endBar?: number): Promise<ChordEvent[]> {
    const params: Record<string, any> = {};
    if (startBar !== undefined) params.start_bar = startBar;
    if (endBar !== undefined) params.end_bar = endBar;
    const response = await api.get<ChordEvent[]>(`/projects/${projectId}/chords`, { params });
    return response.data;
  },

  async create(data: ChordEventCreate): Promise<ChordEvent> {
    const response = await api.post<ChordEvent>("/chords", data);
    return response.data;
  },

  async update(chordId: string, data: ChordEventUpdate): Promise<ChordEvent> {
    const response = await api.put<ChordEvent>(`/chords/${chordId}`, data);
    return response.data;
  },

  async delete(chordId: string): Promise<void> {
    await api.delete(`/chords/${chordId}`);
  },

  async insert(data: ChordInsertRequest): Promise<ChordEvent> {
    const response = await api.post<ChordEvent>("/chords/insert", data);
    return response.data;
  },
};
