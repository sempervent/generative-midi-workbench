<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay" @click="handleOverlayClick">
      <div class="segment-modal" @click.stop>
        <div class="modal-header">
          <h2>Create Segments</h2>
          <button class="close-btn" @click="close" title="Close (Esc)">×</button>
        </div>

        <div class="modal-content">
          <!-- Global Settings -->
          <div class="section">
            <h3>Global Settings</h3>
            <div class="form-grid">
              <div class="form-group">
                <label>Start Bar</label>
                <input
                  v-model.number="localStartBar"
                  type="number"
                  min="0"
                  step="0.25"
                />
              </div>
              <div class="form-group">
                <label>Length (bars)</label>
                <input
                  v-model.number="localLengthBars"
                  type="number"
                  min="1"
                  step="1"
                />
              </div>
              <div class="form-group">
                <label>Seed</label>
                <div class="seed-control">
                  <input
                    v-model.number="localSeed"
                    type="number"
                    min="0"
                  />
                  <button @click="randomizeSeed" class="btn-small">Randomize</button>
                </div>
              </div>
            </div>
          </div>

          <!-- Segment Kind Selection -->
          <div class="section">
            <h3>Select Segments to Generate</h3>
            <div class="kind-badges">
              <button
                v-for="kind in allKinds"
                :key="kind"
                class="kind-badge"
                :class="{ active: selectedKinds.has(kind) }"
                @click="toggleKind(kind)"
              >
                {{ getKindLabel(kind) }}
              </button>
            </div>
          </div>

          <!-- Tabs for Selected Kinds -->
          <div v-if="selectedKinds.size > 0" class="section">
            <div class="tabs">
              <button
                v-for="kind in Array.from(selectedKinds)"
                :key="kind"
                class="tab"
                :class="{ active: activeTab === kind }"
                @click="activeTab = kind"
              >
                {{ getKindLabel(kind) }}
              </button>
            </div>

            <!-- Beats Tab -->
            <div v-if="activeTab === 'beats' && selectedKinds.has('beats')" class="tab-content">
              <div class="form-grid">
                <div class="form-group">
                  <label>Kit</label>
                  <select v-model="beatsModel.kit">
                    <option value="gm_hiphop">Hip-Hop</option>
                    <option value="gm_trap">Trap</option>
                    <option value="gm_boom_bap">Boom Bap</option>
                    <option value="gm_blank">Minimal</option>
                  </select>
                </div>
                <div class="form-group">
                  <label>Pattern</label>
                  <select v-model="beatsModel.pattern">
                    <option value="straight">Straight</option>
                    <option value="syncopated">Syncopated</option>
                    <option value="euclidean">Euclidean</option>
                    <option value="polyrhythm">Polyrhythm</option>
                  </select>
                </div>
                <div class="form-group">
                  <label>Density</label>
                  <input
                    v-model.number="beatsModel.density"
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                  />
                  <span class="value">{{ beatsModel.density.toFixed(2) }}</span>
                </div>
                <div class="form-group">
                  <label>Swing</label>
                  <input
                    v-model.number="beatsModel.swing"
                    type="range"
                    min="0"
                    max="0.75"
                    step="0.05"
                  />
                  <span class="value">{{ beatsModel.swing.toFixed(2) }}</span>
                </div>
                <div class="form-group">
                  <label>Ghost Notes</label>
                  <input
                    v-model="beatsModel.ghost_notes"
                    type="checkbox"
                  />
                </div>
                <div class="form-group">
                  <label>Fills</label>
                  <select v-model="beatsModel.fills">
                    <option value="none">None</option>
                    <option value="ends">Ends</option>
                    <option value="every_4">Every 4 bars</option>
                    <option value="random">Random</option>
                  </select>
                </div>
              </div>
            </div>

            <!-- Chords Tab -->
            <div v-if="activeTab === 'chords' && selectedKinds.has('chords')" class="tab-content">
              <div class="form-grid">
                <div class="form-group">
                  <label>Key</label>
                  <input v-model="chordsModel.key" type="text" placeholder="C" />
                </div>
                <div class="form-group">
                  <label>Mode</label>
                  <select v-model="chordsModel.mode">
                    <option value="ionian">Ionian (Major)</option>
                    <option value="dorian">Dorian</option>
                    <option value="phrygian">Phrygian</option>
                    <option value="lydian">Lydian</option>
                    <option value="mixolydian">Mixolydian</option>
                    <option value="aeolian">Aeolian (Minor)</option>
                    <option value="locrian">Locrian</option>
                  </select>
                </div>
                <div class="form-group">
                  <label>Progression Style</label>
                  <select v-model="chordsModel.progression_style">
                    <option value="pop">Pop</option>
                    <option value="rap_minor">Rap Minor</option>
                    <option value="jazzy">Jazzy</option>
                    <option value="modal">Modal</option>
                    <option value="circle_fifths">Circle of Fifths</option>
                  </select>
                </div>
                <div class="form-group">
                  <label>Voicing</label>
                  <select v-model="chordsModel.voicing">
                    <option value="root">Root</option>
                    <option value="drop2">Drop 2</option>
                    <option value="spread">Spread</option>
                    <option value="tight">Tight</option>
                  </select>
                </div>
                <div class="form-group">
                  <label>Intensity</label>
                  <input
                    v-model.number="chordsModel.intensity"
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                  />
                  <span class="value">{{ chordsModel.intensity.toFixed(2) }}</span>
                </div>
                <div class="form-group">
                  <label>Strum (ms)</label>
                  <input
                    v-model.number="chordsModel.strum_ms"
                    type="number"
                    min="0"
                    max="80"
                  />
                </div>
              </div>
            </div>

            <!-- Bass Tab -->
            <div v-if="activeTab === 'bass' && selectedKinds.has('bass')" class="tab-content">
              <div class="form-grid">
                <div class="form-group">
                  <label>Style</label>
                  <select v-model="bassModel.style">
                    <option value="root">Root</option>
                    <option value="walking">Walking</option>
                    <option value="808">808</option>
                    <option value="syncopated">Syncopated</option>
                  </select>
                </div>
                <div class="form-group">
                  <label>Octave</label>
                  <input
                    v-model.number="bassModel.octave"
                    type="number"
                    min="1"
                    max="4"
                  />
                </div>
                <div class="form-group">
                  <label>Follow Kicks</label>
                  <input
                    v-model.number="bassModel.follow_kicks"
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                  />
                  <span class="value">{{ bassModel.follow_kicks.toFixed(2) }}</span>
                </div>
                <div class="form-group">
                  <label>Rhythmic Density</label>
                  <input
                    v-model.number="bassModel.rhythmic_density"
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                  />
                  <span class="value">{{ bassModel.rhythmic_density.toFixed(2) }}</span>
                </div>
                <div class="form-group">
                  <label>Intensity</label>
                  <input
                    v-model.number="bassModel.intensity"
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                  />
                  <span class="value">{{ bassModel.intensity.toFixed(2) }}</span>
                </div>
              </div>
            </div>

            <!-- Melody Tab -->
            <div v-if="activeTab === 'melody' && selectedKinds.has('melody')" class="tab-content">
              <div class="form-grid">
                <div class="form-group">
                  <label>Range</label>
                  <select v-model="melodyModel.range">
                    <option value="narrow">Narrow</option>
                    <option value="medium">Medium</option>
                    <option value="wide">Wide</option>
                  </select>
                </div>
                <div class="form-group">
                  <label>Motif Repetition</label>
                  <input
                    v-model.number="melodyModel.motif_repetition"
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                  />
                  <span class="value">{{ melodyModel.motif_repetition.toFixed(2) }}</span>
                </div>
                <div class="form-group">
                  <label>Leapiness</label>
                  <input
                    v-model.number="melodyModel.leapiness"
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                  />
                  <span class="value">{{ melodyModel.leapiness.toFixed(2) }}</span>
                </div>
                <div class="form-group">
                  <label>Call & Response</label>
                  <input
                    v-model="melodyModel.call_response"
                    type="checkbox"
                  />
                </div>
                <div class="form-group">
                  <label>Syncopation</label>
                  <input
                    v-model.number="melodyModel.syncopation"
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                  />
                  <span class="value">{{ melodyModel.syncopation.toFixed(2) }}</span>
                </div>
                <div class="form-group">
                  <label>Intensity</label>
                  <input
                    v-model.number="melodyModel.intensity"
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                  />
                  <span class="value">{{ melodyModel.intensity.toFixed(2) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-secondary" @click="handlePreview">Preview</button>
          <button class="btn btn-primary" @click="handleApply" :disabled="selectedKinds.size === 0">
            Create
          </button>
          <button class="btn btn-secondary" @click="close">Cancel</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { segmentsApi } from "../api/segments";
import type {
  BassModel,
  BeatsModel,
  ChordsModel,
  MelodyModel,
  SegmentGenerateResponse,
  SegmentKind,
} from "../types";

const props = defineProps<{
  projectId: string;
  startBar?: number;
  defaultLengthBars?: number;
  isOpen: boolean;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "applied", result: SegmentGenerateResponse): void;
}>();

const allKinds: SegmentKind[] = ["beats", "chords", "bass", "melody"];
const selectedKinds = ref<Set<SegmentKind>>(new Set(["beats", "chords"]));
const activeTab = ref<SegmentKind>("beats");

const localStartBar = ref(0);
const localLengthBars = ref(4);
const localSeed = ref(Math.floor(Math.random() * 1000000));

// Models with defaults
const beatsModel = ref<BeatsModel>({
  kit: "gm_hiphop",
  density: 0.7,
  swing: 0.0,
  humanize_ms: 0,
  pattern: "straight",
  kick_variation: 0.3,
  snare_variation: 0.3,
  hat_variation: 0.3,
  ghost_notes: true,
  fills: "ends",
  mute_probability: 0.0,
  velocity_curve: "accent_2_4",
});

const chordsModel = ref<ChordsModel>({
  key: "C",
  mode: "aeolian",
  progression_style: "rap_minor",
  harmonic_rhythm: "1chord/bar",
  voicing: "root",
  inversion_bias: 0.2,
  intensity: 0.85,
  strum_ms: 0,
  duration_gate: 0.9,
  syncopation: 0.2,
  borrowed_chords: 0.1,
  cadence_strength: 0.7,
});

const bassModel = ref<BassModel>({
  style: "808",
  octave: 2,
  follow_kicks: 0.8,
  approach_notes: 0.3,
  slides: 0.2,
  rhythmic_density: 0.6,
  intensity: 0.85,
});

const melodyModel = ref<MelodyModel>({
  range: "medium",
  motif_repetition: 0.5,
  leapiness: 0.3,
  call_response: true,
  syncopation: 0.3,
  intensity: 0.85,
  avoid_too_unique: true,
});

const previewResult = ref<SegmentGenerateResponse | null>(null);

// Initialize from props
watch(
  () => props.isOpen,
  (open) => {
    if (open) {
      localStartBar.value = props.startBar ?? 0;
      localLengthBars.value = props.defaultLengthBars ?? 4;
      localSeed.value = Math.floor(Math.random() * 1000000);
      previewResult.value = null;
      // Set active tab to first selected kind
      if (selectedKinds.value.size > 0) {
        activeTab.value = Array.from(selectedKinds.value)[0];
      }
    }
  },
  { immediate: true }
);

function toggleKind(kind: SegmentKind) {
  if (selectedKinds.value.has(kind)) {
    selectedKinds.value.delete(kind);
    // Switch to another tab if current tab was deselected
    if (activeTab.value === kind && selectedKinds.value.size > 0) {
      activeTab.value = Array.from(selectedKinds.value)[0];
    }
  } else {
    selectedKinds.value.add(kind);
    activeTab.value = kind;
  }
}

function getKindLabel(kind: SegmentKind): string {
  const labels: Record<SegmentKind, string> = {
    beats: "🥁 Beats",
    chords: "🎹 Chords",
    bass: "🎸 Bass",
    melody: "🎵 Melody",
  };
  return labels[kind];
}

function randomizeSeed() {
  localSeed.value = Math.floor(Math.random() * 1000000);
}

async function handlePreview() {
  if (selectedKinds.value.size === 0) {
    alert("Please select at least one segment kind");
    return;
  }

  try {
    const models: Record<string, any> = {};
    if (selectedKinds.value.has("beats")) {
      models.beats = beatsModel.value;
    }
    if (selectedKinds.value.has("chords")) {
      models.chords = chordsModel.value;
    }
    if (selectedKinds.value.has("bass")) {
      models.bass = bassModel.value;
    }
    if (selectedKinds.value.has("melody")) {
      models.melody = melodyModel.value;
    }

    const request = {
      project_id: props.projectId,
      start_bar: localStartBar.value,
      length_bars: localLengthBars.value,
      seed: localSeed.value,
      kinds: Array.from(selectedKinds.value),
      models,
      preview: true,
    };

    previewResult.value = await segmentsApi.generateSegments(request);
    // TODO: Show preview in UI (ghost cards or play preview)
    console.log("Preview generated:", previewResult.value);
  } catch (error) {
    console.error("Preview failed:", error);
    alert("Failed to generate preview");
  }
}

async function handleApply() {
  if (selectedKinds.value.size === 0) {
    alert("Please select at least one segment kind");
    return;
  }

  try {
    const models: Record<string, any> = {};
    if (selectedKinds.value.has("beats")) {
      models.beats = beatsModel.value;
    }
    if (selectedKinds.value.has("chords")) {
      models.chords = chordsModel.value;
    }
    if (selectedKinds.value.has("bass")) {
      models.bass = bassModel.value;
    }
    if (selectedKinds.value.has("melody")) {
      models.melody = melodyModel.value;
    }

    const request = {
      project_id: props.projectId,
      start_bar: localStartBar.value,
      length_bars: localLengthBars.value,
      seed: localSeed.value,
      kinds: Array.from(selectedKinds.value),
      models,
      preview: false,
    };

    const result = await segmentsApi.generateSegments(request);
    emit("applied", result);
    close();
  } catch (error) {
    console.error("Generation failed:", error);
    alert("Failed to create segments");
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

function handleKeydown(event: KeyboardEvent) {
  if (event.key === "Escape" && props.isOpen) {
    close();
  }
}

onMounted(() => {
  window.addEventListener("keydown", handleKeydown);
});

onUnmounted(() => {
  window.removeEventListener("keydown", handleKeydown);
});
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  justify-content: center;
  align-items: center;
  z-index: 1000;
}

.segment-modal {
  background: #2a2a2a;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
  width: 90vw;
  max-width: 800px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  color: #e0e0e0;
  font-family: "Inter", sans-serif;
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px;
  border-bottom: 1px solid #3a3a3a;
  background: #333;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5em;
  color: #fff;
}

.close-btn {
  background: none;
  border: none;
  font-size: 2em;
  color: #aaa;
  cursor: pointer;
  padding: 0 10px;
  line-height: 1;
}

.close-btn:hover {
  color: #fff;
}

.modal-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.section {
  margin-bottom: 30px;
}

.section h3 {
  margin: 0 0 15px 0;
  font-size: 1.2em;
  color: #fff;
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 15px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.form-group label {
  font-size: 0.9em;
  color: #bbb;
}

.form-group input[type="number"],
.form-group input[type="text"],
.form-group select {
  padding: 8px;
  border-radius: 4px;
  border: 1px solid #444;
  background: #3a3a3a;
  color: #fff;
  font-size: 0.9em;
}

.form-group input[type="range"] {
  width: 100%;
}

.form-group input[type="range"] + .value {
  font-size: 0.9em;
  color: #aaa;
  text-align: right;
}

.form-group input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.kind-badges {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.kind-badge {
  padding: 10px 20px;
  border: 2px solid #555;
  border-radius: 6px;
  background: #3a3a3a;
  color: #ccc;
  cursor: pointer;
  font-size: 0.95em;
  transition: all 0.2s;
}

.kind-badge:hover {
  border-color: #666;
  background: #444;
}

.kind-badge.active {
  border-color: #4a9eff;
  background: #4a9eff;
  color: #fff;
}

.tabs {
  display: flex;
  gap: 5px;
  border-bottom: 1px solid #444;
  margin-bottom: 20px;
}

.tab {
  padding: 10px 20px;
  border: none;
  border-bottom: 2px solid transparent;
  background: transparent;
  color: #aaa;
  cursor: pointer;
  font-size: 0.95em;
  transition: all 0.2s;
}

.tab:hover {
  color: #fff;
}

.tab.active {
  color: #4a9eff;
  border-bottom-color: #4a9eff;
}

.tab-content {
  padding: 10px 0;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 20px;
  border-top: 1px solid #3a3a3a;
  background: #333;
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.95em;
  transition: all 0.2s;
}

.btn-primary {
  background: #4a9eff;
  color: #fff;
}

.btn-primary:hover:not(:disabled) {
  background: #3a8ee0;
}

.btn-primary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-secondary {
  background: #555;
  color: #fff;
}

.btn-secondary:hover {
  background: #666;
}

.btn-small {
  padding: 5px 10px;
  font-size: 0.85em;
  background: #555;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.btn-small:hover {
  background: #666;
}

.seed-control {
  display: flex;
  gap: 10px;
  align-items: center;
}

.seed-control input {
  flex: 1;
}
</style>

