<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay" @click="handleOverlayClick">
      <div class="chord-gen-modal-v2" @click.stop>
        <!-- Header -->
        <div class="modal-header">
          <h2>Chord Generation & Editing</h2>
          <button class="close-btn" @click="close">×</button>
        </div>

        <!-- Tabs -->
        <div class="tabs">
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'generate' }"
            @click="activeTab = 'generate'"
          >
            Generate
          </button>
          <button
            class="tab-btn"
            :class="{ active: activeTab === 'edit' }"
            @click="activeTab = 'edit'"
          >
            Edit/Insert
          </button>
        </div>

        <!-- Shared Header Controls (Both Tabs) -->
        <div class="shared-header">
          <div class="header-row">
            <div class="control-group">
              <label>Key</label>
              <select v-model="localKey" @change="updateKey">
                <option v-for="key in keys" :key="key" :value="key">{{ key }}</option>
              </select>
            </div>
            <div class="control-group">
              <label>Mode</label>
              <select v-model="localMode" @change="updateMode">
                <option value="ionian">Ionian (Major)</option>
                <option value="dorian">Dorian</option>
                <option value="phrygian">Phrygian</option>
                <option value="lydian">Lydian</option>
                <option value="mixolydian">Mixolydian</option>
                <option value="aeolian">Aeolian (Minor)</option>
                <option value="locrian">Locrian</option>
              </select>
            </div>
            <div class="control-group">
              <label>Style</label>
              <select v-model="localStyle">
                <option value="rap_dark">Rap Dark</option>
                <option value="rap_bright">Rap Bright</option>
                <option value="neo_soul">Neo Soul</option>
                <option value="trap_minimal">Trap Minimal</option>
                <option value="boom_bap">Boom Bap</option>
                <option value="cinematic">Cinematic</option>
                <option value="ambient">Ambient</option>
              </select>
            </div>
          </div>
          <div class="header-row">
            <div class="control-group">
              <label>Start Bar</label>
              <input v-model.number="barStart" type="number" min="0" />
            </div>
            <div class="control-group">
              <label>Length Bars</label>
              <input v-model.number="lengthBars" type="number" min="1" />
            </div>
            <div class="control-group">
              <label>
                <input v-model="snapToGrid" type="checkbox" />
                Snap to Grid
              </label>
            </div>
          </div>
          <div class="header-row">
            <div class="control-group">
              <label>Seed</label>
              <input v-model.number="seed" type="number" />
              <button @click="randomizeSeed" class="btn-small">Randomize</button>
            </div>
            <div class="control-group">
              <label>
                <input v-model="lockSeed" type="checkbox" />
                Lock Seed
              </label>
            </div>
          </div>
        </div>

        <!-- Generate Tab Content -->
        <div v-if="activeTab === 'generate'" class="tab-content">
          <div class="content-grid">
            <!-- Left: Progression Controls -->
            <div class="panel">
              <h3>Progression Controls</h3>
              <div class="control-group">
                <label>Harmonic Rhythm</label>
                <select v-model="genParams.harmonic_rhythm">
                  <option value="every_1_bar">Every 1 bar</option>
                  <option value="every_2_bars">Every 2 bars</option>
                  <option value="every_beat">Every beat</option>
                  <option value="syncopated">Syncopated</option>
                </select>
              </div>
              <div class="control-group">
                <label>Chord Pool</label>
                <select v-model="genParams.chord_pool">
                  <option value="diatonic_only">Diatonic only</option>
                  <option value="borrowed">Borrowed chords</option>
                  <option value="secondary_dominants">Secondary dominants</option>
                  <option value="chromatic">Chromatic approach</option>
                </select>
              </div>
              <div class="control-group">
                <label>Cadence Bias</label>
                <input v-model.number="genParams.cadence_bias" type="range" min="0" max="1" step="0.1" />
                <span>{{ genParams.cadence_bias.toFixed(1) }}</span>
              </div>
              <div class="control-group">
                <label>Tension</label>
                <input v-model.number="genParams.tension" type="range" min="0" max="1" step="0.1" />
                <span>{{ genParams.tension.toFixed(1) }}</span>
              </div>
              <div class="control-group">
                <label>Repetition</label>
                <input v-model.number="genParams.repetition" type="range" min="0" max="1" step="0.1" />
                <span>{{ genParams.repetition.toFixed(1) }}</span>
              </div>
              <div class="control-group">
                <label>Voicing</label>
                <select v-model="genParams.voicing">
                  <option value="triads">Triads</option>
                  <option value="7ths">7ths</option>
                  <option value="9ths">9ths</option>
                  <option value="spread">Spread</option>
                  <option value="cluster">Cluster</option>
                </select>
              </div>
              <div class="control-group">
                <label>Inversion Variance</label>
                <input v-model.number="genParams.inversion_variance" type="range" min="0" max="1" step="0.1" />
                <span>{{ genParams.inversion_variance.toFixed(1) }}</span>
              </div>
            </div>

            <!-- Middle: Strum + Humanization -->
            <div class="panel">
              <h3>Strum + Humanization</h3>
              <div class="control-group">
                <label>Strum Duration (beats)</label>
                <input v-model.number="genParams.strum_beats" type="number" min="0" max="2" step="0.05" />
                <div class="quick-buttons">
                  <button
                    v-for="val in [0, 0.0625, 0.125, 0.25, 0.5, 1]"
                    :key="val"
                    class="quick-btn"
                    :class="{ active: genParams.strum_beats === val }"
                    @click="genParams.strum_beats = val"
                  >
                    {{ val === 0 ? "0" : val === 0.0625 ? "1/16" : val === 0.125 ? "1/8" : val === 0.25 ? "1/4" : val === 0.5 ? "1/2" : "1" }}
                  </button>
                </div>
              </div>
              <div class="control-group">
                <label>Strum Direction</label>
                <select v-model="genParams.strum_direction">
                  <option value="down">Down</option>
                  <option value="up">Up</option>
                  <option value="alternate">Alternate</option>
                  <option value="random">Random</option>
                </select>
              </div>
              <div class="control-group">
                <label>Humanize (beats)</label>
                <input v-model.number="genParams.humanize_beats" type="range" min="0" max="0.25" step="0.001" />
                <span>{{ genParams.humanize_beats.toFixed(3) }}</span>
              </div>
              <div class="control-group">
                <label>Velocity Humanize</label>
                <input v-model.number="genParams.velocity_humanize" type="range" min="0" max="0.5" step="0.01" />
                <span>{{ genParams.velocity_humanize.toFixed(2) }}</span>
              </div>
              <div class="control-group">
                <label>Gate (duration fraction)</label>
                <input v-model.number="genParams.duration_gate" type="range" min="0.1" max="1.0" step="0.05" />
                <span>{{ genParams.duration_gate.toFixed(2) }}</span>
              </div>
            </div>

            <!-- Right: Chord Hit Pattern -->
            <div class="panel">
              <h3>Chord Hit Pattern</h3>
              <div class="control-group">
                <label>Pattern Type</label>
                <select v-model="genParams.pattern_type">
                  <option value="sustain">Sustain (one hit, held)</option>
                  <option value="piano_stabs">Piano Stabs (repeated hits)</option>
                  <option value="guitar_strum">Guitar Strum (repeated strums)</option>
                  <option value="syncopated_pump">Syncopated Pump (offbeat)</option>
                </select>
              </div>
              <template v-if="genParams.pattern_type !== 'sustain'">
                <div class="control-group">
                  <label>Hits per Bar</label>
                  <select v-model="genParams.hits_per_bar">
                    <option value="1">1</option>
                    <option value="2">2</option>
                    <option value="4">4</option>
                    <option value="8">8</option>
                    <option value="16">16</option>
                  </select>
                </div>
                <div class="control-group">
                  <label>Hit Subdivision</label>
                  <select v-model="genParams.hit_subdivision">
                    <option value="1/4">1/4</option>
                    <option value="1/8">1/8</option>
                    <option value="1/16">1/16</option>
                    <option value="1/32">1/32</option>
                    <option value="triplet_1/8">Triplet 1/8</option>
                    <option value="triplet_1/16">Triplet 1/16</option>
                  </select>
                </div>
                <div class="control-group">
                  <label>Hit Accent</label>
                  <input v-model.number="genParams.hit_accent" type="range" min="0" max="1" step="0.1" />
                  <span>{{ genParams.hit_accent.toFixed(1) }}</span>
                </div>
                <div class="control-group">
                  <label>Decay Curve</label>
                  <input v-model.number="genParams.decay_curve" type="range" min="0" max="1" step="0.1" />
                  <span>{{ genParams.decay_curve.toFixed(1) }}</span>
                </div>
                <div class="control-group">
                  <label>Swing (beats)</label>
                  <input v-model.number="genParams.swing_beats" type="range" min="0" max="0.2" step="0.01" />
                  <span>{{ genParams.swing_beats.toFixed(2) }}</span>
                </div>
              </template>
              <div class="control-group">
                <label>Offset (beats)</label>
                <input v-model.number="genParams.offset_beats" type="range" min="-0.5" max="0.5" step="0.0625" />
                <span>{{ genParams.offset_beats.toFixed(3) }}</span>
              </div>
            </div>
          </div>

          <!-- Output Options -->
          <div class="output-options">
            <div class="control-group">
              <label>Apply Mode</label>
              <select v-model="applyMode">
                <option value="replace_range">Replace Range</option>
                <option value="insert_empty_only">Insert into Empty Only</option>
                <option value="layer">Layer (new chord clip)</option>
              </select>
            </div>
            <div class="action-buttons">
              <button @click="previewGenerate" class="btn btn-preview" :disabled="generating">
                Preview
              </button>
              <button @click="applyGenerate" class="btn btn-apply" :disabled="generating">
                Apply
              </button>
              <button @click="close" class="btn btn-cancel">Cancel</button>
            </div>
          </div>
        </div>

        <!-- Edit/Insert Tab Content -->
        <div v-if="activeTab === 'edit'" class="tab-content">
          <div class="content-grid-edit">
            <!-- Left: Chord Palette -->
            <div class="panel">
              <h3>Chord Palette</h3>
              <div class="palette-tabs">
                <button
                  class="palette-tab"
                  :class="{ active: !showBorrowed }"
                  @click="showBorrowed = false"
                >
                  Diatonic
                </button>
                <button class="palette-tab" :class="{ active: showBorrowed }" @click="loadBorrowedChords">
                  Borrowed
                </button>
              </div>
              <div class="chord-chips">
                <button
                  v-for="chord in displayedChords"
                  :key="chord.roman_numeral"
                  class="chord-chip"
                  :class="{ active: selectedChord?.roman_numeral === chord.roman_numeral }"
                  @click="selectChord(chord)"
                >
                  <span class="chip-roman">{{ chord.roman_numeral }}</span>
                  <span class="chip-name">{{ chord.chord_name }}</span>
                </button>
              </div>
              <div class="control-group">
                <label>
                  <input v-model="showExtensions" type="checkbox" />
                  Show Extensions (7/9)
                </label>
              </div>
            </div>

            <!-- Middle: Suggested Chords -->
            <div class="panel">
              <h3>Suggested Chords</h3>
              <button @click="loadSuggestions" class="btn btn-load" :disabled="loadingSuggestions">
                {{ loadingSuggestions ? "Loading..." : "Load Suggestions" }}
              </button>
              <div v-if="suggestions.length > 0" class="suggestions-list">
                <div
                  v-for="(suggestion, idx) in suggestions"
                  :key="idx"
                  class="suggestion-card"
                >
                  <div class="suggestion-header">
                    <span class="suggestion-reason">{{ suggestion.reason }}</span>
                    <span class="suggestion-score">{{ suggestion.score.toFixed(2) }}</span>
                  </div>
                  <div class="suggestion-chord">
                    {{ suggestion.roman_numeral }} ({{ suggestion.chord_name }})
                  </div>
                  <div v-if="suggestion.explanation" class="suggestion-explanation">
                    {{ suggestion.explanation }}
                  </div>
                  <div class="suggestion-actions">
                    <button @click="previewSuggestion(suggestion)" class="btn-small btn-preview">
                      Preview
                    </button>
                    <button @click="insertSuggestion(suggestion)" class="btn-small btn-insert">
                      Insert
                    </button>
                  </div>
                </div>
              </div>
            </div>

            <!-- Right: Timeline -->
            <div class="panel">
              <h3>Timeline</h3>
              <div class="timeline-slots">
                <div
                  v-for="(slot, idx) in timelineSlots"
                  :key="idx"
                  class="timeline-slot"
                  @click="editSlot(idx)"
                >
                  <div class="slot-info">
                    <span class="slot-bar">Bar {{ slot.startBar }}</span>
                    <span class="slot-chord">{{ slot.chord || "Empty" }}</span>
                    <span class="slot-duration">{{ slot.duration }} beats</span>
                  </div>
                </div>
              </div>
              <div class="timeline-actions">
                <button @click="insertAtCursor" class="btn-small">Insert at Cursor</button>
                <button @click="quantizeStarts" class="btn-small">Quantize Starts</button>
                <button @click="humanizeStarts" class="btn-small">Humanize Starts</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { chordGenApi } from "../api/chordGen";
import { chordSuggestApi } from "../api/chordSuggest";
import { chordsApi } from "../api/chords";
import { type DiatonicChord, theoryApi } from "../api/theory";
import { useProjectStore } from "../stores/project";
import type { ChordGenParams, ChordGenSuggestion } from "../types";

const props = defineProps<{
  isOpen: boolean;
  projectId: string;
  clipId?: string | null;
  startBar?: number;
  lengthBars?: number;
  bpm?: number;
  timeSignatureNum?: number;
  timeSignatureDen?: number;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "applied"): void;
}>();

const store = useProjectStore();
const project = computed(() => store.currentProject);

// Tabs
const activeTab = ref<"generate" | "edit">("generate");

// Shared header state
const keys = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"];
const localKey = ref(project.value?.key_tonic || "C");
const localMode = ref(project.value?.mode || "ionian");
const localStyle = ref("rap_dark");
const barStart = ref(props.startBar || 0);
const lengthBars = ref(props.lengthBars || 4);
const snapToGrid = ref(true);
const seed = ref(Math.floor(Math.random() * 1000000));
const lockSeed = ref(false);

// Generate tab state
const genParams = ref({
  harmonic_rhythm: "every_1_bar",
  chord_pool: "diatonic_only",
  cadence_bias: 0.5,
  tension: 0.5,
  repetition: 0.5,
  voicing: "triads",
  inversion_variance: 0.5,
  strum_beats: 0.0,
  strum_direction: "down",
  humanize_beats: 0.0,
  velocity_humanize: 0.0,
  duration_gate: 0.85,
  pattern_type: "sustain",
  hits_per_bar: 4,
  hit_subdivision: "1/8",
  hit_accent: 0.5,
  decay_curve: 0.3,
  swing_beats: 0.0,
  offset_beats: 0.0,
});

const applyMode = ref("replace_range");
const generating = ref(false);

// Edit tab state
const diatonicChords = ref<DiatonicChord[]>([]);
const borrowedChords = ref<DiatonicChord[]>([]);
const showBorrowed = ref(false);
const showExtensions = ref(false);
const selectedChord = ref<DiatonicChord | null>(null);
const suggestions = ref<Awaited<ReturnType<typeof chordSuggestApi.suggest>>["suggestions"]>([]);
const loadingSuggestions = ref(false);
const timelineSlots = ref<Array<{ startBar: number; chord: string | null; duration: number }>>([]);

const displayedChords = computed(() => {
  return showBorrowed.value ? borrowedChords.value : diatonicChords.value;
});

// Watch project changes
watch(
  () => project.value,
  (newProject) => {
    if (newProject) {
      localKey.value = newProject.key_tonic;
      localMode.value = newProject.mode;
    }
  },
  { immediate: true }
);

// Watch modal open
watch(
  () => props.isOpen,
  (open) => {
    if (open) {
      if (props.startBar !== undefined) barStart.value = props.startBar;
      if (props.lengthBars !== undefined) lengthBars.value = props.lengthBars;
      loadDiatonicChords();
      updateTimelineSlots();
    }
  }
);

onMounted(() => {
  if (props.isOpen) {
    loadDiatonicChords();
    updateTimelineSlots();
  }
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
  if (!props.projectId) return;
  showBorrowed.value = true;
  if (borrowedChords.value.length === 0) {
    try {
      const all = await theoryApi.getDiatonicChords(props.projectId, true);
      borrowedChords.value = all.filter((c) => c.degree === 0);
    } catch (error) {
      console.error("Failed to load borrowed chords:", error);
    }
  }
}

async function loadSuggestions() {
  if (!props.projectId) return;
  loadingSuggestions.value = true;
  try {
    const result = await chordSuggestApi.suggest({
      project_id: props.projectId,
      context_bar: barStart.value,
      num_suggestions: 8,
      seed: seed.value,
      style: localStyle.value,
      tension: genParams.value.tension,
      cadence_bias: genParams.value.cadence_bias,
    });
    suggestions.value = result.suggestions;
  } catch (error) {
    console.error("Failed to load suggestions:", error);
  } finally {
    loadingSuggestions.value = false;
  }
}

function updateKey() {
  if (!project.value) return;
  store.updateProject(project.value.id, { key_tonic: localKey.value });
}

function updateMode() {
  if (!project.value) return;
  store.updateProject(project.value.id, { mode: localMode.value });
}

function randomizeSeed() {
  if (!lockSeed.value) {
    seed.value = Math.floor(Math.random() * 1000000);
  }
}

function selectChord(chord: DiatonicChord) {
  selectedChord.value = chord;
}

function updateTimelineSlots() {
  timelineSlots.value = [];
  for (let i = 0; i < lengthBars.value; i++) {
    timelineSlots.value.push({
      startBar: barStart.value + i,
      chord: null, // TODO: Load existing chords
      duration: 1.0,
    });
  }
}

function editSlot(idx: number) {
  // TODO: Open inline editor
  console.log("Edit slot", idx);
}

function insertAtCursor() {
  if (!selectedChord.value || !props.projectId || props.startBar === undefined) return;
  // TODO: Insert chord at cursor
  console.log("Insert chord", selectedChord.value);
}

function quantizeStarts() {
  // TODO: Quantize chord starts
  console.log("Quantize starts");
}

function humanizeStarts() {
  // TODO: Humanize chord starts
  console.log("Humanize starts");
}

async function previewSuggestion(suggestion: Awaited<ReturnType<typeof chordSuggestApi.suggest>>["suggestions"][0]) {
  // TODO: Preview suggestion using playback
  console.log("Preview suggestion", suggestion);
}

async function insertSuggestion(suggestion: Awaited<ReturnType<typeof chordSuggestApi.suggest>>["suggestions"][0]) {
  if (!props.projectId || props.startBar === undefined) return;
  try {
    await chordsApi.insert({
      project_id: props.projectId,
      start_bar: props.startBar,
      duration_bars: props.lengthBars || 1.0,
      roman_numeral: suggestion.roman_numeral,
      chord_name: suggestion.chord_name,
      intensity: 0.85,
      voicing: "root",
      inversion: 0,
      strum_beats: genParams.value.strum_beats,
      humanize_beats: genParams.value.humanize_beats,
      duration_gate: genParams.value.duration_gate,
      pattern_type: genParams.value.pattern_type,
      velocity_curve: "flat",
    });
    emit("applied");
  } catch (error) {
    console.error("Failed to insert suggestion:", error);
    alert("Failed to insert chord");
  }
}

async function previewGenerate() {
  // TODO: Preview generation
  console.log("Preview generate");
}

async function applyGenerate() {
  if (!props.projectId) return;
  generating.value = true;
  try {
    // TODO: Implement generation
    console.log("Apply generate");
    emit("applied");
    close();
  } catch (error) {
    console.error("Failed to generate:", error);
    alert("Failed to generate chords");
  } finally {
    generating.value = false;
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
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10000;
}

.chord-gen-modal-v2 {
  background: #2a2a2a;
  border-radius: 8px;
  width: 95vw;
  max-width: 1400px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  color: #e0e0e0;
}

.modal-header {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #444;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
  color: #fff;
}

.close-btn {
  background: none;
  border: none;
  font-size: 2rem;
  cursor: pointer;
  color: #aaa;
  line-height: 1;
}

.close-btn:hover {
  color: #fff;
}

.tabs {
  display: flex;
  border-bottom: 1px solid #444;
  padding: 0 1.5rem;
}

.tab-btn {
  padding: 0.75rem 1.5rem;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  color: #aaa;
  cursor: pointer;
  font-size: 1rem;
  transition: all 0.2s;
}

.tab-btn:hover {
  color: #fff;
}

.tab-btn.active {
  color: #4a9eff;
  border-bottom-color: #4a9eff;
}

.shared-header {
  padding: 1rem 1.5rem;
  border-bottom: 1px solid #444;
  background: #333;
}

.header-row {
  display: flex;
  gap: 1rem;
  margin-bottom: 0.75rem;
}

.header-row:last-child {
  margin-bottom: 0;
}

.tab-content {
  flex: 1;
  overflow-y: auto;
  padding: 1.5rem;
}

.content-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
  margin-bottom: 1.5rem;
}

.content-grid-edit {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1.5rem;
}

.panel {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  background: #333;
  padding: 1rem;
  border-radius: 6px;
  border: 1px solid #444;
}

.panel h3 {
  margin: 0 0 0.5rem 0;
  font-size: 1.1rem;
  color: #fff;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.control-group label {
  font-size: 0.9rem;
  color: #ccc;
  font-weight: 500;
}

.control-group input[type="range"] {
  width: 100%;
}

.control-group input[type="number"],
.control-group select {
  padding: 0.5rem;
  border-radius: 4px;
  border: 1px solid #555;
  background: #2a2a2a;
  color: #fff;
  font-size: 0.9rem;
}

.quick-buttons {
  display: flex;
  gap: 0.25rem;
  flex-wrap: wrap;
}

.quick-btn {
  padding: 0.25rem 0.5rem;
  background: #444;
  border: 1px solid #555;
  border-radius: 4px;
  color: #ccc;
  cursor: pointer;
  font-size: 0.85rem;
  transition: all 0.2s;
}

.quick-btn:hover {
  background: #555;
}

.quick-btn.active {
  background: #4a9eff;
  border-color: #4a9eff;
  color: #fff;
}

.output-options {
  padding: 1rem;
  background: #333;
  border-radius: 6px;
  border: 1px solid #444;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.action-buttons {
  display: flex;
  gap: 0.5rem;
}

.btn {
  padding: 0.75rem 1.5rem;
  border-radius: 6px;
  border: none;
  cursor: pointer;
  font-weight: 500;
  transition: all 0.2s;
}

.btn-preview {
  background: #2196f3;
  color: white;
}

.btn-preview:hover:not(:disabled) {
  background: #1976d2;
}

.btn-apply {
  background: #4caf50;
  color: white;
}

.btn-apply:hover:not(:disabled) {
  background: #45a049;
}

.btn-cancel {
  background: #666;
  color: white;
}

.btn-cancel:hover {
  background: #777;
}

.btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.btn-small {
  padding: 0.5rem 1rem;
  font-size: 0.85rem;
}

.palette-tabs {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.palette-tab {
  padding: 0.5rem 1rem;
  background: #444;
  border: 1px solid #555;
  border-radius: 4px;
  color: #ccc;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
}

.palette-tab:hover {
  background: #555;
}

.palette-tab.active {
  background: #4a9eff;
  border-color: #4a9eff;
  color: #fff;
}

.chord-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.chord-chip {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.5rem 0.75rem;
  background: #2a2a2a;
  border: 1px solid #555;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 60px;
}

.chord-chip:hover {
  background: #3a3a3a;
  border-color: #777;
}

.chord-chip.active {
  background: #4a9eff;
  border-color: #4a9eff;
  color: #fff;
}

.chip-roman {
  font-weight: bold;
  font-size: 1em;
}

.chip-name {
  font-size: 0.8em;
  margin-top: 2px;
}

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
  margin-top: 0.75rem;
}

.suggestion-card {
  padding: 0.75rem;
  background: #2a2a2a;
  border: 1px solid #555;
  border-radius: 4px;
}

.suggestion-header {
  display: flex;
  justify-content: space-between;
  margin-bottom: 0.5rem;
}

.suggestion-reason {
  font-weight: 500;
  color: #4a9eff;
}

.suggestion-score {
  color: #aaa;
  font-size: 0.85rem;
}

.suggestion-chord {
  font-size: 1.1rem;
  font-weight: 500;
  margin-bottom: 0.25rem;
}

.suggestion-explanation {
  font-size: 0.85rem;
  color: #aaa;
  margin-bottom: 0.5rem;
}

.suggestion-actions {
  display: flex;
  gap: 0.5rem;
}

.btn-insert {
  background: #4caf50;
  color: white;
}

.btn-insert:hover {
  background: #45a049;
}

.timeline-slots {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
  max-height: 300px;
  overflow-y: auto;
}

.timeline-slot {
  padding: 0.75rem;
  background: #2a2a2a;
  border: 1px solid #555;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.timeline-slot:hover {
  background: #3a3a3a;
  border-color: #777;
}

.slot-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.timeline-actions {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.btn-load {
  background: #4a9eff;
  color: white;
  width: 100%;
  margin-bottom: 0.75rem;
}
</style>

