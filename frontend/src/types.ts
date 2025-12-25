export interface Project {
  id: string;
  name: string;
  bpm: number;
  time_signature_num: number;
  time_signature_den: number;
  bars: number;
  key_tonic: string;
  mode: string;
  seed: number;
  created_at: string;
  updated_at: string;
}

export interface Track {
  id: string;
  project_id: string;
  name: string;
  role: "drums" | "chords" | "bass" | "melody";
  midi_channel: number;
  midi_program: number;
  is_muted: boolean;
  created_at: string;
}

export interface Note {
  id: string;
  clip_id: string;
  pitch: number;
  velocity: number;
  start_tick: number;
  duration_tick: number;
  probability: number;
  created_at: string;
}

export interface ChordEvent {
  id: string;
  clip_id: string;
  start_tick: number;
  duration_tick: number;
  roman_numeral: string;
  chord_name: string;
  created_at: string;
}

export interface PolyrhythmProfile {
  id: string;
  name: string;
  steps: number;
  pulses: number;
  rotation: number;
  cycle_beats: number;
  swing: number | null;
  humanize_ms: number | null;
  created_at: string;
  updated_at: string;
}

export interface PolyrhythmLane {
  id: string;
  clip_id: string;
  polyrhythm_profile_id: string;
  lane_name: string;
  instrument_role: string | null;
  pitch: number;
  velocity: number;
  mute: boolean;
  solo: boolean;
  order_index: number;
  seed_offset: number;
  created_at: string;
}

export interface Clip {
  id: string;
  start_bar: number;
  length_bars: number;
  grid_mode: "standard" | "euclidean" | "polyrhythm" | "polyrhythm_multi";
  polyrhythm_profile_id: string | null;
  is_muted: boolean;
  is_soloed: boolean;
  notes: Note[];
  chord_events: ChordEvent[];
  polyrhythm_lanes?: PolyrhythmLane[];
}

export interface GridSpec {
  ticks_per_bar: number;
  ticks_per_step: number;
  grid_steps_per_bar: number;
  lcm_steps: number;
}

export interface LanePreviewInfo {
  lane_id: string;
  lane_name: string;
  ratio: string;
  pitch: number;
  velocity: number;
  mute: boolean;
  solo: boolean;
}

export interface PolyrhythmLanesPreview {
  lanes: LanePreviewInfo[];
  events: Array<{
    pitch: number;
    velocity: number;
    start_tick: number;
    duration_tick: number;
  }>;
  grid_spec: GridSpec;
}

export interface TrackInArrangement {
  id: string;
  name: string;
  role: string;
  midi_channel: number;
  midi_program: number;
  is_muted: boolean;
  clips: Clip[];
}

export interface Arrangement {
  project_id: string;
  project_name: string;
  bpm: number;
  time_signature_num: number;
  time_signature_den: number;
  bars: number;
  key_tonic: string;
  mode: string;
  seed: number;
  tracks: TrackInArrangement[];
}

export interface GenerationRequest {
  kind: "drums" | "chords" | "bass" | "melody" | "full";
  seed?: number;
  params?: Record<string, any>;
}

export type PlaybackRange =
  | { kind: "project" } // uses computed project length
  | { kind: "bars"; startBar: number; endBar: number }; // endBar exclusive

export interface PlaybackState {
  isPlaying: boolean;
  loopEnabled: boolean; // default true
  range: PlaybackRange; // default {kind:"project"}
}
