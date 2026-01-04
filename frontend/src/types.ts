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
  duration_beats: number;
  roman_numeral: string;
  chord_name: string;
  intensity: number;
  voicing: string;
  inversion: number;
  strum_ms?: number | null; // Deprecated, use strum_beats
  humanize_ms?: number | null; // Deprecated, use humanize_beats
  strum_beats: number;
  humanize_beats: number;
  duration_gate: number;
  velocity_jitter: number;
  timing_jitter_ms: number;
  is_enabled: boolean;
  is_locked: boolean;
  grid_quantum?: number | null;
  created_at: string;
  // Pattern fields
  pattern_type: "block" | "strum" | "comp" | "arp" | "stabs";
  velocity_curve: "flat" | "down" | "up" | "swell" | "dip";
  comp_pattern?: {
    grid: string;
    steps: number[];
    accent: number[];
    swing: number;
  } | null;
  strum_direction: "down" | "up" | "alternate" | "random";
  strum_spread: number;
  retrigger: boolean;
  // New fields
  offset_beats: number;
  strum_curve: "linear" | "ease_in" | "ease_out";
  hit_params?: {
    // Stabs mode
    hits?: number;
    spacing?: string; // "1/8", "1/16", "1/32"
    skip_prob?: number;
    vel_curve?: string;
    // Comp mode
    source?: "diatonic" | "euclidean" | "polyrhythm";
    euclid_steps?: number;
    euclid_pulses?: number;
    euclid_rotation?: number;
    polyrhythm_profile_id?: string;
    swing?: number;
    humanize?: number;
    // Arp mode
    dir?: "up" | "down" | "up-down" | "random";
    rate?: string; // "1/8", "1/16", "1/32"
    octaves?: number;
    latch?: boolean;
    // Strum mode (additional to existing strum fields)
    tightness?: number;
  } | null;
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

export interface ChordGenRun {
  id: string;
  project_id: string;
  clip_id: string | null;
  bar_start: number;
  bar_end: number;
  seed: number;
  params: Record<string, any>;
  suggestions: ChordGenSuggestion[];
}

export interface ChordGenSuggestion {
  id: string;
  rank: number;
  score: number;
  title: string | null;
  explanation: string | null;
  progression: ChordProgressionItem[];
  locks: Record<string, any> | null;
}

export interface ChordProgressionItem {
  roman_numeral: string;
  chord_name: string;
  start_bar: number;
  length_bars: number;
  duration_beats?: number;
  intensity?: number;
  voicing?: string;
  inversion?: number;
  pattern_type?: string;
  duration_gate?: number;
  velocity_curve?: string;
  comp_pattern?: {
    grid: string;
    steps: number[];
    accent: number[];
    swing: number;
  };
  strum_direction?: string;
  strum_spread?: number;
  retrigger?: boolean;
  strum_beats?: number;
  humanize_beats?: number;
}

export interface ChordGenParams {
  style?: "guitar" | "piano" | "pads";
  complexity?: number;
  tension?: number;
  harmonic_rhythm?: "1chord/bar" | "2chords/bar" | "slow" | "custom";
  progression_style?: "pop" | "rap_minor" | "jazzy" | "modal" | "circle_fifths";
  cadence_ending?: boolean;
}

export interface ChordLockSpec {
  [key: string]: string;
}
