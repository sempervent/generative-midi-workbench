<template>
  <Teleport to="body">
    <div v-if="isOpen" class="editor-overlay" @click="handleOverlayClick">
      <div class="chord-editor" @click.stop>
        <div class="editor-header">
          <h3>Edit Chord</h3>
          <button class="close-btn" @click="close" title="Close (Esc)">×</button>
        </div>
        <div v-if="chord" class="editor-content">
          <div class="chord-info">
            <div class="info-row">
              <span class="label">Chord:</span>
              <span class="value">{{ chord.chord_name }} ({{ chord.roman_numeral }})</span>
            </div>
          </div>

          <!-- Chord Picker -->
          <div v-if="projectId && diatonicChords.length > 0" class="chord-picker-section">
            <label>Select Chord</label>
            <div class="chord-picker-tabs">
              <button
                class="tab-btn"
                :class="{ active: !showBorrowed }"
                @click="showBorrowed = false"
              >
                Diatonic
              </button>
              <button
                class="tab-btn"
                :class="{ active: showBorrowed }"
                @click="loadBorrowedChords"
              >
                Borrowed
              </button>
            </div>
            <div class="chord-chips">
              <button
                v-for="diatonicChord in displayedChords"
                :key="diatonicChord.roman_numeral"
                class="chord-chip"
                :class="{
                  active: chord.chord_name === diatonicChord.chord_name,
                  tension: diatonicChord.tension > 0.5,
                }"
                :title="`${diatonicChord.function} - Tension: ${diatonicChord.tension.toFixed(1)}`"
                @click="selectChord(diatonicChord)"
              >
                <span class="chip-roman">{{ diatonicChord.roman_numeral }}</span>
                <span class="chip-name">{{ diatonicChord.chord_name }}</span>
              </button>
            </div>
          </div>

          <div class="controls">
            <!-- Intensity -->
            <div class="control-group">
              <label>Intensity</label>
              <input
                v-model.number="localIntensity"
                type="range"
                min="0"
                max="1"
                step="0.01"
                @input="updateIntensity"
              />
              <span class="value">{{ (localIntensity * 100).toFixed(0) }}%</span>
            </div>

            <!-- Duration -->
            <div class="control-group">
              <label>Duration (beats)</label>
              <div class="duration-control">
                <input
                  v-model.number="localDurationBeats"
                  type="number"
                  min="0.25"
                  max="8"
                  step="0.25"
                  @input="updateDuration"
                  class="duration-input"
                />
                <div class="quick-buttons">
                  <button
                    v-for="beats in [1, 2, 4, 8]"
                    :key="beats"
                    class="quick-btn"
                    :class="{ active: localDurationBeats === beats }"
                    @click="setDuration(beats)"
                  >
                    {{ beats }}
                  </button>
                </div>
              </div>
            </div>

            <!-- Strum -->
            <div class="control-group">
              <label>Strum (beats)</label>
              <div class="strum-control">
                <input
                  v-model.number="localStrumBeats"
                  type="range"
                  min="0"
                  max="1"
                  step="0.001"
                  @input="updateStrum"
                  class="strum-slider"
                />
                <input
                  v-model.number="localStrumBeats"
                  type="number"
                  min="0"
                  max="2"
                  step="0.001"
                  @input="updateStrum"
                  class="strum-input"
                />
                <select v-model="strumPreset" @change="applyStrumPreset" class="preset-select">
                  <option value="custom">Custom</option>
                  <option value="0">None (0)</option>
                  <option value="0.0625">1/16</option>
                  <option value="0.125">1/8</option>
                  <option value="0.25">1/4</option>
                  <option value="0.5">1/2</option>
                  <option value="1">1</option>
                </select>
              </div>
            </div>

            <!-- Humanize -->
            <div class="control-group">
              <label>Humanize (beats)</label>
              <div class="humanize-control">
                <input
                  v-model.number="localHumanizeBeats"
                  type="range"
                  min="0"
                  max="0.125"
                  step="0.001"
                  @input="updateHumanize"
                  class="humanize-slider"
                />
                <input
                  v-model.number="localHumanizeBeats"
                  type="number"
                  min="0"
                  max="0.5"
                  step="0.001"
                  @input="updateHumanize"
                  class="humanize-input"
                />
              </div>
            </div>

            <!-- Pattern Type (Hit Mode) -->
            <div class="control-group">
              <label>Hit Pattern</label>
              <div class="pattern-type-selector">
                <button
                  v-for="mode in ['block', 'stabs', 'comp', 'arp', 'strum']"
                  :key="mode"
                  class="pattern-btn"
                  :class="{ active: localPatternType === mode }"
                  @click="setPatternType(mode)"
                >
                  {{ mode === 'block' ? 'Hold' : mode.charAt(0).toUpperCase() + mode.slice(1) }}
                </button>
              </div>
            </div>

            <!-- Strum Direction (only for strum pattern) -->
            <div v-if="localPatternType === 'strum'" class="control-group">
              <label>Strum Direction</label>
              <select v-model="localStrumDirection" @change="updateStrumDirection">
                <option value="down">Down</option>
                <option value="up">Up</option>
                <option value="alternate">Alternate</option>
                <option value="random">Random</option>
              </select>
            </div>

            <!-- Velocity Curve -->
            <div v-if="localPatternType === 'strum'" class="control-group">
              <label>Velocity Curve</label>
              <select v-model="localVelocityCurve" @change="updateVelocityCurve">
                <option value="flat">Flat</option>
                <option value="down">Down</option>
                <option value="up">Up</option>
                <option value="swell">Swell</option>
                <option value="dip">Dip</option>
              </select>
            </div>

            <!-- Comp Pattern (only for comp pattern) -->
            <div v-if="localPatternType === 'comp'" class="control-group">
              <label>Comp Pattern</label>
              <div class="comp-pattern-editor">
                <select v-model="localCompGrid" @change="updateCompPattern">
                  <option value="1/4">1/4 notes</option>
                  <option value="1/8">1/8 notes</option>
                  <option value="1/16">1/16 notes</option>
                </select>
                <div class="pattern-steps">
                  <button
                    v-for="(step, idx) in localCompSteps"
                    :key="idx"
                    class="step-btn"
                    :class="{ active: step === 1 }"
                    @click="toggleCompStep(idx)"
                  >
                    {{ idx + 1 }}
                  </button>
                </div>
                <label class="toggle-label">
                  <input v-model="localRetrigger" type="checkbox" @change="updateRetrigger" />
                  Retrigger
                </label>
              </div>
            </div>

            <!-- Duration Gate -->
            <div class="control-group">
              <label>Duration Gate</label>
              <input
                v-model.number="localDurationGate"
                type="range"
                min="0.1"
                max="1.0"
                step="0.05"
                @input="updateDurationGate"
              />
              <span class="value">{{ (localDurationGate * 100).toFixed(0) }}%</span>
            </div>

            <!-- Voicing -->
            <div class="control-group">
              <label>Voicing</label>
              <select v-model="localVoicing" @change="updateVoicing">
                <option value="root">Root</option>
                <option value="open">Open</option>
                <option value="drop2">Drop-2</option>
                <option value="smooth">Smooth</option>
              </select>
            </div>

            <!-- Inversion -->
            <div class="control-group">
              <label>Inversion</label>
              <div class="inversion-control">
                <button
                  class="inversion-btn"
                  @click="decrementInversion"
                  :disabled="localInversion <= 0"
                >
                  −
                </button>
                <span class="inversion-value">{{ localInversion }}</span>
                <button
                  class="inversion-btn"
                  @click="incrementInversion"
                  :disabled="localInversion >= 3"
                >
                  +
                </button>
              </div>
            </div>

            <!-- Timing Preview -->
            <div class="timing-preview">
              <div class="preview-text">
                <span v-if="localStrumBeats > 0">
                  Strum spreads notes across {{ localStrumBeats.toFixed(3) }} beats
                </span>
                <span v-if="localHumanizeBeats > 0">
                  <span v-if="localStrumBeats > 0">; </span>
                  Humanize ±{{ localHumanizeBeats.toFixed(3) }} beats
                </span>
                <span v-if="localStrumBeats === 0 && localHumanizeBeats === 0">
                  All notes start simultaneously
                </span>
              </div>
            </div>

            <!-- Toggles -->
            <div class="control-group toggles">
              <label class="toggle-label">
                <input
                  v-model="localEnabled"
                  type="checkbox"
                  @change="updateEnabled"
                />
                Enabled
              </label>
              <label class="toggle-label">
                <input
                  v-model="localLocked"
                  type="checkbox"
                  @change="updateLocked"
                />
                Locked
              </label>
            </div>
          </div>

          <div class="editor-actions">
            <button class="btn btn-audition" @click="audition" :disabled="!chord.is_enabled">
              Audition
            </button>
            <button class="btn btn-secondary" @click="close">Cancel</button>
            <button class="btn btn-primary" @click="save">Save</button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import * as Tone from "tone";
import { computed, onMounted, ref, watch } from "vue";
import { chordsApi } from "../api/chords";
import { type DiatonicChord, theoryApi } from "../api/theory";
import type { ChordEvent } from "../types";

const props = defineProps<{
  chord: ChordEvent | null;
  isOpen: boolean;
  beatsPerBar?: number;
  bpm?: number;
  projectId?: string;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "saved", chord: ChordEvent): void;
}>();

const localIntensity = ref(0.85);
const localVoicing = ref("root");
const localInversion = ref(0);
const localStrumBeats = ref(0.0);
const localHumanizeBeats = ref(0.0);
const localDurationBeats = ref(1.0);
const localEnabled = ref(true);
const localLocked = ref(false);
const strumPreset = ref("custom");
const localPatternType = ref<"block" | "strum" | "comp" | "arp" | "stabs">("block");
const localStrumDirection = ref<"down" | "up" | "alternate" | "random">("down");
const localStrumCurve = ref<"linear" | "ease_in" | "ease_out">("linear");
const localStrumSpread = ref(1.0);
const localVelocityCurve = ref<"flat" | "down" | "up" | "swell" | "dip">("flat");
const localDurationGate = ref(0.85);
const localOffsetBeats = ref(0.0);
const localCompGrid = ref("1/8");
const localCompSteps = ref([1, 0, 1, 0, 1, 0, 1, 0]);
const localRetrigger = ref(false);
const localHitParams = ref<{
  hits?: number;
  spacing?: string;
  skip_prob?: number;
  vel_curve?: string;
  source?: string;
  euclid_steps?: number;
  euclid_pulses?: number;
  euclid_rotation?: number;
  polyrhythm_profile_id?: string;
  swing?: number;
  humanize?: number;
  dir?: string;
  rate?: string;
  octaves?: number;
  latch?: boolean;
  tightness?: number;
}>({});

// Chord picker state
const diatonicChords = ref<DiatonicChord[]>([]);
const borrowedChords = ref<DiatonicChord[]>([]);
const showBorrowed = ref(false);

const displayedChords = computed(() => {
  return showBorrowed.value ? borrowedChords.value : diatonicChords.value;
});

async function loadDiatonicChords() {
  if (!props.projectId) return;
  try {
    diatonicChords.value = await theoryApi.getDiatonicChords(props.projectId, false);
  } catch (error) {
    console.error("Failed to load diatonic chords:", error);
  }
}

async function loadBorrowedChords() {
  if (!props.projectId || borrowedChords.value.length > 0) {
    showBorrowed.value = true;
    return;
  }
  try {
    const allChords = await theoryApi.getDiatonicChords(props.projectId, true);
    borrowedChords.value = allChords.filter((c) => c.degree === 0); // Borrowed chords have degree 0
    showBorrowed.value = true;
  } catch (error) {
    console.error("Failed to load borrowed chords:", error);
  }
}

function selectChord(diatonicChord: DiatonicChord) {
  if (!props.chord) return;
  void chordsApi.update(props.chord.id, {
    roman_numeral: diatonicChord.roman_numeral,
    chord_name: diatonicChord.chord_name,
  });
  // Update local state
  if (props.chord) {
    props.chord.roman_numeral = diatonicChord.roman_numeral;
    props.chord.chord_name = diatonicChord.chord_name;
  }
}

watch(
  () => props.chord,
  (newChord) => {
    if (newChord) {
      localIntensity.value = newChord.intensity || 0.85;
      localVoicing.value = newChord.voicing || "root";
      localInversion.value = newChord.inversion || 0;
      // Use beats fields if available, otherwise default to 0
      localStrumBeats.value = newChord.strum_beats ?? 0.0;
      localHumanizeBeats.value = newChord.humanize_beats ?? 0.0;
      localDurationBeats.value = newChord.duration_beats || 1.0;
      localEnabled.value = newChord.is_enabled ?? true;
      localLocked.value = newChord.is_locked ?? false;
      localPatternType.value = (newChord.pattern_type as any) || "block";
      localStrumDirection.value = (newChord.strum_direction as any) || "down";
      localVelocityCurve.value = (newChord.velocity_curve as any) || "flat";
      localDurationGate.value = newChord.duration_gate ?? 0.85;
      localCompGrid.value = newChord.comp_pattern?.grid || "1/8";
      localCompSteps.value = newChord.comp_pattern?.steps || [1, 0, 1, 0, 1, 0, 1, 0];
      localRetrigger.value = newChord.retrigger ?? false;
      localStrumCurve.value = (newChord.strum_curve as any) || "linear";
      localOffsetBeats.value = newChord.offset_beats ?? 0.0;
      localHitParams.value = newChord.hit_params || {};
      updateStrumPreset();
    }
  },
  { immediate: true }
);

function updateStrumPreset() {
  const beats = localStrumBeats.value;
  if (beats === 0) strumPreset.value = "0";
  else if (Math.abs(beats - 0.0625) < 0.001) strumPreset.value = "0.0625";
  else if (Math.abs(beats - 0.125) < 0.001) strumPreset.value = "0.125";
  else if (Math.abs(beats - 0.25) < 0.001) strumPreset.value = "0.25";
  else if (Math.abs(beats - 0.5) < 0.001) strumPreset.value = "0.5";
  else if (Math.abs(beats - 1) < 0.001) strumPreset.value = "1";
  else strumPreset.value = "custom";
}

function applyStrumPreset() {
  if (strumPreset.value !== "custom") {
    localStrumBeats.value = Number.parseFloat(strumPreset.value);
    updateStrum();
  }
}

function setDuration(beats: number) {
  localDurationBeats.value = beats;
  updateDuration();
}

function incrementInversion() {
  if (localInversion.value < 3) {
    localInversion.value++;
    updateInversion();
  }
}

function decrementInversion() {
  if (localInversion.value > 0) {
    localInversion.value--;
    updateInversion();
  }
}

function updateIntensity() {
  if (!props.chord) return;
  void chordsApi.update(props.chord.id, { intensity: localIntensity.value });
}

function updateVoicing() {
  if (!props.chord) return;
  void chordsApi.update(props.chord.id, { voicing: localVoicing.value });
}

function updateInversion() {
  if (!props.chord) return;
  void chordsApi.update(props.chord.id, { inversion: localInversion.value });
}

function updateStrum() {
  if (!props.chord) return;
  updateStrumPreset();
  void chordsApi.update(props.chord.id, { strum_beats: localStrumBeats.value });
}

function updateHumanize() {
  if (!props.chord) return;
  void chordsApi.update(props.chord.id, { humanize_beats: localHumanizeBeats.value });
}

function updateDuration() {
  if (!props.chord) return;
  // Calculate duration_tick from duration_beats
  const PPQ = 480;
  const durationTick = Math.round(localDurationBeats.value * PPQ);
  void chordsApi.update(props.chord.id, {
    duration_beats: localDurationBeats.value,
    duration_tick: durationTick,
  });
}

function updateEnabled() {
  if (!props.chord) return;
  void chordsApi.update(props.chord.id, { is_enabled: localEnabled.value });
}

function updateLocked() {
  if (!props.chord) return;
  void chordsApi.update(props.chord.id, { is_locked: localLocked.value });
}

function setPatternType(mode: "block" | "strum" | "comp" | "arp" | "stabs") {
  localPatternType.value = mode;
  updatePatternType();
}

function updatePatternType() {
  if (!props.chord) return;
  void chordsApi.update(props.chord.id, { pattern_type: localPatternType.value });
}

function updateOffsetBeats() {
  if (!props.chord) return;
  void chordsApi.update(props.chord.id, { offset_beats: localOffsetBeats.value });
}

function updateStrumCurve() {
  if (!props.chord) return;
  void chordsApi.update(props.chord.id, { strum_curve: localStrumCurve.value });
}

function updateHitParams() {
  if (!props.chord) return;
  void chordsApi.update(props.chord.id, { hit_params: localHitParams.value });
}

async function audition() {
  if (!props.chord || !props.bpm) return;

  try {
    // Ensure AudioContext is started (only on user gesture)
    const { ensureAudioStarted } = await import("../audio/ensureAudio");
    await ensureAudioStarted();

    // Use the same renderer as playback for consistency
    const { renderChordEventToNotes } = await import("../music/chordRender");

    // Create a temporary chord event with current UI values
    const tempChord: ChordEvent = {
      ...props.chord,
      intensity: localIntensity.value,
      voicing: localVoicing.value,
      inversion: localInversion.value,
      strum_beats: localStrumBeats.value,
      humanize_beats: localHumanizeBeats.value,
      duration_beats: localDurationBeats.value,
      duration_tick: Math.round(localDurationBeats.value * 480), // PPQ
      duration_gate: localDurationGate.value,
      pattern_type: localPatternType.value,
      velocity_curve: localVelocityCurve.value,
      strum_direction: localStrumDirection.value,
      strum_spread: localStrumSpread.value,
      comp_pattern:
        localPatternType.value === "comp"
          ? {
              grid: localCompGrid.value,
              steps: [...localCompSteps.value],
              accent: localCompSteps.value.map(() => 1.0),
              swing: 0.0,
            }
          : undefined,
      retrigger: localRetrigger.value,
      is_enabled: localEnabled.value,
    };

    // Render chord to notes using the same function as playback
    const PPQ = 480;
    const ticksPerBar = 4 * PPQ; // Assume 4/4 for audition
    const renderedNotes = renderChordEventToNotes(
      tempChord,
      0, // clipStartBar (not relevant for audition)
      0, // clipOffset
      0, // trackOffset
      ticksPerBar,
      "C", // tonic (will be overridden by chord_name/roman)
      "ionian", // mode (will be overridden by chord_name/roman)
      12345, // seed
      props.bpm
    );

    if (renderedNotes.length === 0) {
      console.warn("No notes rendered for chord audition");
      return;
    }

    const synth = new Tone.PolySynth(Tone.Synth).toDestination();
    const bpm = props.bpm || 120;
    Tone.Transport.bpm.value = bpm;

    // Convert MIDI notes to frequencies and schedule
    const duration = localDurationBeats.value * (60 / bpm); // Convert beats to seconds

    for (const note of renderedNotes) {
      // Convert start_tick to seconds (relative to chord start)
      const startSeconds = (note.start_tick / PPQ) * (60 / bpm);
      const noteDuration = (note.duration_tick / PPQ) * (60 / bpm);
      const freq = Tone.Frequency(note.pitch, "midi").toFrequency();
      const velocity = note.velocity / 127;

      synth.triggerAttackRelease(freq, noteDuration, `+${startSeconds}`, velocity);
    }

    // Stop after duration
    setTimeout(
      () => {
        synth.dispose();
      },
      (duration + 1) * 1000
    );
  } catch (error) {
    console.error("Failed to audition chord:", error);
  }
}

async function save() {
  if (!props.chord) return;
  try {
    const PPQ = 480;
    const updateData: any = {
      intensity: localIntensity.value,
      voicing: localVoicing.value,
      inversion: localInversion.value,
      strum_beats: localStrumBeats.value,
      humanize_beats: localHumanizeBeats.value,
      duration_beats: localDurationBeats.value,
      duration_tick: Math.round(localDurationBeats.value * PPQ),
      is_enabled: localEnabled.value,
      is_locked: localLocked.value,
      pattern_type: localPatternType.value,
      duration_gate: localDurationGate.value,
      velocity_curve: localVelocityCurve.value,
    };

    if (localPatternType.value === "strum") {
      updateData.strum_direction = localStrumDirection.value;
      updateData.strum_spread = localStrumSpread.value;
      updateData.strum_curve = localStrumCurve.value;
    }

    if (localPatternType.value === "comp") {
      updateData.comp_pattern = {
        grid: localCompGrid.value,
        steps: [...localCompSteps.value],
        accent: localCompSteps.value.map(() => 1.0),
        swing: 0.0,
      };
      updateData.retrigger = localRetrigger.value;
    }

    if (localPatternType.value === "stabs") {
      updateData.hit_params = localHitParams.value;
    }

    updateData.offset_beats = localOffsetBeats.value;

    const updated = await chordsApi.update(props.chord.id, updateData);
    emit("saved", updated);
    close();
  } catch (error) {
    console.error("Failed to save chord:", error);
    alert("Failed to save chord");
  }
}

function close() {
  emit("close");
}

function handleOverlayClick(event: MouseEvent) {
  if (event.target === event.currentTarget) {
    close();
  }
}

// Keyboard shortcuts
function handleKeydown(event: KeyboardEvent) {
  if (event.key === "Escape" && props.isOpen) {
    close();
  }
}

watch(
  () => props.isOpen,
  (open) => {
    if (open) {
      window.addEventListener("keydown", handleKeydown);
      if (props.projectId) {
        loadDiatonicChords();
      }
    } else {
      window.removeEventListener("keydown", handleKeydown);
    }
  }
);

watch(
  () => props.projectId,
  () => {
    if (props.isOpen && props.projectId) {
      loadDiatonicChords();
    }
  }
);

onMounted(() => {
  if (props.isOpen && props.projectId) {
    loadDiatonicChords();
  }
});
</script>

<style scoped>
.editor-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
}

.chord-editor {
  background: #2a2a2a;
  border: 1px solid #555;
  border-radius: 8px;
  width: 550px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  color: #e0e0e0;
  font-family: "Inter", sans-serif;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #444;
  background: #333;
  position: sticky;
  top: 0;
  z-index: 10;
}

.editor-header h3 {
  margin: 0;
  color: #fff;
  font-size: 1.3em;
}

.close-btn {
  background: none;
  border: none;
  color: #aaa;
  font-size: 28px;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.2s;
}

.close-btn:hover {
  background: #444;
  color: #fff;
}

.editor-content {
  padding: 20px;
}

.chord-info {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #444;
}

.info-row {
  display: flex;
  gap: 12px;
  align-items: center;
}

.label {
  font-weight: 600;
  color: #aaa;
  font-size: 0.95em;
}

.value {
  color: #fff;
  font-size: 1.1em;
}

.controls {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.control-group label {
  min-width: 140px;
  color: #ccc;
  font-size: 0.95em;
  font-weight: 500;
}

.duration-control {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.duration-input {
  width: 80px;
  padding: 8px;
  border-radius: 4px;
  border: 1px solid #444;
  background: #333;
  color: #fff;
  font-size: 0.95em;
}

.quick-buttons {
  display: flex;
  gap: 6px;
}

.quick-btn {
  padding: 6px 12px;
  border: 1px solid #555;
  border-radius: 4px;
  background: #3a3a3a;
  color: #ccc;
  cursor: pointer;
  font-size: 0.9em;
  transition: all 0.2s;
}

.quick-btn:hover {
  background: #444;
  border-color: #666;
}

.quick-btn.active {
  background: #4a9eff;
  border-color: #4a9eff;
  color: #fff;
}

.strum-control,
.humanize-control {
  display: flex;
  align-items: center;
  gap: 10px;
  flex: 1;
}

.strum-slider,
.humanize-slider {
  flex: 1;
}

.strum-input,
.humanize-input {
  width: 80px;
  padding: 6px;
  border-radius: 4px;
  border: 1px solid #444;
  background: #333;
  color: #fff;
  font-size: 0.9em;
}

.preset-select {
  width: 100px;
  padding: 6px;
  border-radius: 4px;
  border: 1px solid #444;
  background: #333;
  color: #fff;
  font-size: 0.9em;
  cursor: pointer;
}

.control-group input[type="range"] {
  flex: 1;
  height: 6px;
  -webkit-appearance: none;
  background: #555;
  border-radius: 3px;
  outline: none;
}

.control-group input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #4a9eff;
  cursor: pointer;
  border: 2px solid #fff;
}

.control-group input[type="range"]::-moz-range-thumb {
  width: 16px;
  height: 16px;
  border-radius: 50%;
  background: #4a9eff;
  cursor: pointer;
  border: 2px solid #fff;
}

.control-group select {
  flex: 1;
  padding: 8px;
  border-radius: 4px;
  border: 1px solid #444;
  background: #333;
  color: #fff;
  font-size: 0.95em;
  cursor: pointer;
}

.inversion-control {
  display: flex;
  align-items: center;
  gap: 12px;
}

.inversion-btn {
  width: 32px;
  height: 32px;
  border: 1px solid #555;
  border-radius: 4px;
  background: #3a3a3a;
  color: #fff;
  cursor: pointer;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.inversion-btn:hover:not(:disabled) {
  background: #444;
  border-color: #666;
}

.inversion-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.inversion-value {
  min-width: 30px;
  text-align: center;
  font-size: 1.1em;
  color: #fff;
  font-weight: 600;
}

.timing-preview {
  padding: 12px;
  background: #333;
  border-radius: 4px;
  border: 1px solid #444;
  margin-top: 8px;
}

.preview-text {
  font-size: 0.85em;
  color: #aaa;
  line-height: 1.4;
}

.toggles {
  display: flex;
  gap: 20px;
  margin-top: 8px;
}

.toggle-label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  user-select: none;
}

.toggle-label input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.editor-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
  margin-top: 24px;
  padding-top: 20px;
  border-top: 1px solid #444;
}

.btn {
  padding: 10px 20px;
  border-radius: 4px;
  border: none;
  cursor: pointer;
  font-size: 0.95em;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-primary {
  background: #4a9eff;
  color: #fff;
}

.btn-primary:hover {
  background: #3a8ee0;
}

.btn-secondary {
  background: #555;
  color: #fff;
}

.btn-secondary:hover {
  background: #666;
}

.btn-audition {
  background: #6b46c1;
  color: #fff;
}

.btn-audition:hover:not(:disabled) {
  background: #5b21b6;
}

.btn-audition:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.chord-picker-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
  padding: 15px;
  background: #333;
  border-radius: 6px;
  border: 1px solid #444;
  margin-bottom: 20px;
}

.chord-picker-section label {
  color: #e0e0e0;
  font-size: 0.95em;
  font-weight: 500;
}

.chord-picker-tabs {
  display: flex;
  gap: 5px;
}

.tab-btn {
  flex: 1;
  padding: 8px 12px;
  background: #444;
  border: 1px solid #555;
  color: #fff;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9em;
  transition: all 0.2s;
}

.tab-btn:hover {
  background: #555;
}

.tab-btn.active {
  background: #4a9eff;
  border-color: #4a9eff;
}

.chord-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.chord-chip {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 8px 12px;
  background: #444;
  border: 1px solid #555;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 60px;
}

.chord-chip:hover {
  background: #555;
  border-color: #666;
}

.chord-chip.active {
  background: #4a9eff;
  border-color: #4a9eff;
  color: #fff;
}

.chord-chip.tension {
  border-color: #ff6b6b;
}

.chip-roman {
  font-weight: bold;
  font-size: 1.1em;
  color: #fff;
}

.chip-name {
  font-size: 0.85em;
  color: #bbb;
  margin-top: 2px;
}

.chord-chip.active .chip-name {
  color: #fff;
}
</style>


.comp-pattern-editor {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.pattern-steps {
  display: grid;
  grid-template-columns: repeat(8, 1fr);
  gap: 0.25rem;
}

.step-btn {
  padding: 0.5rem;
  border: 1px solid #444;
  background: #333;
  color: #fff;
  cursor: pointer;
  border-radius: 4px;
  transition: all 0.2s;
  font-size: 0.85rem;
}

.step-btn:hover {
  background: #444;
}

.step-btn.active {
  background: #4caf50;
  color: white;
  border-color: #4caf50;
}
