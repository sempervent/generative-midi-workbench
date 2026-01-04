<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay" @click="handleOverlayClick">
      <div class="chord-gen-modal" @click.stop>
        <div class="modal-header">
          <h2>Generate Chord Progression</h2>
          <button class="close-btn" @click="close">×</button>
        </div>

        <div class="modal-content">
          <!-- Left: Generation Controls -->
          <div class="controls-panel">
            <div class="control-group">
              <label>Style</label>
              <select v-model="params.style">
                <option value="guitar">Guitar</option>
                <option value="piano">Piano</option>
                <option value="pads">Pads</option>
              </select>
            </div>

            <div class="control-group">
              <label>Complexity</label>
              <input
                v-model.number="params.complexity"
                type="range"
                min="0"
                max="1"
                step="0.1"
              />
              <span>{{ params.complexity.toFixed(1) }}</span>
            </div>

            <div class="control-group">
              <label>Tension</label>
              <input
                v-model.number="params.tension"
                type="range"
                min="0"
                max="1"
                step="0.1"
              />
              <span>{{ params.tension.toFixed(1) }}</span>
            </div>

            <div class="control-group">
              <label>Harmonic Rhythm</label>
              <select v-model="params.harmonic_rhythm">
                <option value="1chord/bar">1 chord/bar</option>
                <option value="2chords/bar">2 chords/bar</option>
                <option value="slow">Slow</option>
                <option value="custom">Custom</option>
              </select>
            </div>

            <div class="control-group">
              <label>Progression Style</label>
              <select v-model="params.progression_style">
                <option value="pop">Pop</option>
                <option value="rap_minor">Rap Minor</option>
                <option value="jazzy">Jazzy</option>
                <option value="modal">Modal</option>
                <option value="circle_fifths">Circle of Fifths</option>
              </select>
            </div>

            <div class="control-group">
              <label>
                <input v-model="params.cadence_ending" type="checkbox" />
                Cadence Ending
              </label>
            </div>

            <div class="control-group">
              <label>Seed</label>
              <input v-model.number="seed" type="number" />
              <button @click="randomizeSeed">Randomize</button>
            </div>

            <div class="control-group">
              <label>Scope</label>
              <select v-model="scope">
                <option value="clip">This Clip</option>
                <option value="range">Bar Range</option>
                <option value="project">Whole Project</option>
              </select>
            </div>

            <div v-if="scope === 'range'" class="control-group">
              <label>Bar Range</label>
              <div class="range-inputs">
                <input v-model.number="barStart" type="number" min="0" placeholder="Start" />
                <span>to</span>
                <input v-model.number="barEnd" type="number" min="1" placeholder="End" />
              </div>
            </div>

            <div class="control-group">
              <label>
                <input v-model="lockExisting" type="checkbox" />
                Lock Existing Chords
              </label>
            </div>

            <button class="btn-generate" @click="generate" :disabled="generating">
              {{ generating ? "Generating..." : "Generate Options" }}
            </button>
          </div>

          <!-- Middle: Current Progression Timeline -->
          <div class="timeline-panel">
            <h3>Current Progression</h3>
            <div class="progression-slots">
              <div
                v-for="(slot, idx) in currentProgression"
                :key="idx"
                class="progression-slot"
                :class="{ locked: slot.locked }"
              >
                <div class="slot-header">
                  <span class="slot-roman">{{ slot.roman_numeral }}</span>
                  <span class="slot-name">{{ slot.chord_name }}</span>
                  <button
                    class="lock-btn"
                    :class="{ active: slot.locked }"
                    @click="toggleLock(idx)"
                    title="Lock this chord"
                  >
                    🔒
                  </button>
                </div>
                <div class="slot-duration">{{ slot.length_bars }} bars</div>
              </div>
              <div v-if="currentProgression.length === 0" class="empty-progression">
                No chords yet. Generate to create a progression.
              </div>
            </div>
          </div>

              <!-- Right: Suggestions List -->
              <div class="suggestions-panel">
                <h3>Suggestions</h3>
                <div v-if="!clipId && startBar !== undefined" class="quick-insert-section">
                  <h4>Quick Insert</h4>
                  <p class="quick-insert-hint">Select a chord to insert directly:</p>
                  <div v-if="quickInsertChords.length > 0" class="quick-insert-chips">
                    <button
                      v-for="chord in quickInsertChords"
                      :key="chord.roman_numeral"
                      class="quick-insert-chip"
                      @click="quickInsert(chord)"
                    >
                      <span class="chip-roman">{{ chord.roman_numeral }}</span>
                      <span class="chip-name">{{ chord.chord_name }}</span>
                    </button>
                  </div>
                  <div v-else class="loading-chords">Loading chords...</div>
                </div>
                <div v-if="suggestions.length === 0 && clipId" class="no-suggestions">
                  Click "Generate Options" to see suggestions
                </div>
            <div v-else class="suggestions-list">
              <div
                v-for="suggestion in suggestions"
                :key="suggestion.id"
                class="suggestion-item"
                :class="{ selected: selectedSuggestionId === suggestion.id }"
                @click="selectSuggestion(suggestion)"
              >
                <div class="suggestion-header">
                  <span class="suggestion-rank">#{{ suggestion.rank + 1 }}</span>
                  <span class="suggestion-title">{{ suggestion.title || `Candidate ${suggestion.rank + 1}` }}</span>
                  <span class="suggestion-score">{{ suggestion.score.toFixed(2) }}</span>
                </div>
                <div class="suggestion-explanation">{{ suggestion.explanation }}</div>
                <div class="suggestion-actions">
                  <button @click.stop="previewSuggestion(suggestion)" class="btn-preview">
                    Preview
                  </button>
                  <button @click.stop="applySuggestion(suggestion)" class="btn-apply">
                    Apply
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-secondary" @click="close">Cancel</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from "vue";
import { chordGenApi } from "../api/chordGen";
import { chordsApi } from "../api/chords";
import { type DiatonicChord, theoryApi } from "../api/theory";
import type {
  ChordGenParams,
  ChordGenRun,
  ChordGenSuggestion,
  ChordProgressionItem,
} from "../types";

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

const params = ref<ChordGenParams>({
  style: "pads",
  complexity: 0.5,
  tension: 0.5,
  harmonic_rhythm: "1chord/bar",
  progression_style: "pop",
  cadence_ending: true,
});

const seed = ref(Math.floor(Math.random() * 1000000));
const scope = ref<"clip" | "range" | "project">("clip");
const barStart = ref(0);
const barEnd = ref(4);
const lockExisting = ref(false);

const generating = ref(false);
const run = ref<ChordGenRun | null>(null);
const suggestions = ref<ChordGenSuggestion[]>([]);
const selectedSuggestionId = ref<string | null>(null);
const currentProgression = ref<Array<ChordProgressionItem & { locked: boolean }>>([]);

// Quick insert state
const quickInsertChords = ref<DiatonicChord[]>([]);

async function loadQuickInsertChords() {
  if (!props.projectId) return;
  try {
    quickInsertChords.value = await theoryApi.getDiatonicChords(props.projectId, false);
  } catch (error) {
    console.error("Failed to load quick insert chords:", error);
  }
}

async function quickInsert(chord: DiatonicChord) {
  if (!props.projectId || props.startBar === undefined) {
    alert("Missing project ID or start bar");
    return;
  }

  try {
    await chordsApi.insert({
      project_id: props.projectId,
      start_bar: props.startBar,
      duration_bars: props.lengthBars || 1.0,
      roman_numeral: chord.roman_numeral,
      chord_name: chord.chord_name,
      intensity: 0.85,
      voicing: "root",
      inversion: 0,
      strum_beats: 0.0,
      humanize_beats: 0.0,
      duration_gate: 0.85,
      pattern_type: "block",
      velocity_curve: "flat",
    });
    emit("applied");
    close();
  } catch (error) {
    console.error("Failed to insert chord:", error);
    alert("Failed to insert chord");
  }
}

watch(
  () => props.isOpen,
  (open) => {
    if (open) {
      if (props.startBar !== undefined && props.lengthBars !== undefined) {
        barStart.value = props.startBar;
        barEnd.value = props.startBar + props.lengthBars;
      }
      if (!props.clipId) {
        // Load quick insert chords when opening for empty space
        loadQuickInsertChords();
      }
    }
  }
);

onMounted(() => {
  if (props.isOpen && !props.clipId) {
    loadQuickInsertChords();
  }
});

function randomizeSeed() {
  seed.value = Math.floor(Math.random() * 1000000);
}

async function generate() {
  if (!props.projectId) return;

  generating.value = true;
  try {
    let finalBarStart = barStart.value;
    let finalBarEnd = barEnd.value;

    if (
      scope.value === "clip" &&
      props.clipId &&
      props.startBar !== undefined &&
      props.lengthBars !== undefined
    ) {
      finalBarStart = props.startBar;
      finalBarEnd = props.startBar + props.lengthBars;
    } else if (scope.value === "project") {
      // TODO: Get project length from store
      finalBarStart = 0;
      finalBarEnd = 16; // Default
    }

    const result = await chordGenApi.createRun({
      project_id: props.projectId,
      clip_id: scope.value === "clip" ? props.clipId || null : null,
      bar_start: finalBarStart,
      bar_end: finalBarEnd,
      seed: seed.value,
      params: params.value,
      locks:
        lockExisting.value && currentProgression.value.length > 0
          ? Object.fromEntries(
              currentProgression.value
                .filter((s) => s.locked)
                .map((s, idx) => [idx.toString(), s.roman_numeral])
            )
          : undefined,
    });

    run.value = result;
    suggestions.value = result.suggestions;
    if (suggestions.value.length > 0) {
      selectedSuggestionId.value = suggestions.value[0].id;
      // Update current progression from first suggestion
      currentProgression.value = suggestions.value[0].progression.map((chord) => ({
        ...chord,
        locked: false,
      }));
    }
  } catch (error) {
    console.error("Failed to generate chords:", error);
    alert("Failed to generate chord progression");
  } finally {
    generating.value = false;
  }
}

function selectSuggestion(suggestion: ChordGenSuggestion) {
  selectedSuggestionId.value = suggestion.id;
  // Update current progression from selected suggestion
  currentProgression.value = suggestion.progression.map((chord, idx) => ({
    ...chord,
    locked: currentProgression.value[idx]?.locked || false,
  }));
}

function toggleLock(idx: number) {
  if (currentProgression.value[idx]) {
    currentProgression.value[idx].locked = !currentProgression.value[idx].locked;
  }
}

async function previewSuggestion(suggestion: ChordGenSuggestion) {
  if (!props.bpm) {
    alert("BPM not available for preview");
    return;
  }

  try {
    const preview = await chordGenApi.previewSuggestion(suggestion.id, {
      bpm: props.bpm,
      time_signature_num: props.timeSignatureNum || 4,
      time_signature_den: props.timeSignatureDen || 4,
    });

    // TODO: Play preview notes using playback system
    console.log("Preview notes:", preview.notes);
    alert(`Preview: ${preview.chord_count} chords, ${preview.notes.length} notes`);
  } catch (error) {
    console.error("Failed to preview suggestion:", error);
    alert("Failed to preview suggestion");
  }
}

async function applySuggestion(suggestion: ChordGenSuggestion) {
  if (!props.clipId) {
    alert("No clip ID available");
    return;
  }

  try {
    const result = await chordGenApi.applySuggestion(suggestion.id, {
      clip_id: props.clipId,
      replace_existing: true,
    });

    alert(`Applied: ${result.chords_created} chords created`);
    emit("applied");
    close();
  } catch (error) {
    console.error("Failed to apply suggestion:", error);
    alert("Failed to apply suggestion");
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

.chord-gen-modal {
  background: white;
  border-radius: 8px;
  width: 90vw;
  max-width: 1200px;
  max-height: 90vh;
  display: flex;
  flex-direction: column;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
}

.modal-header {
  padding: 1rem;
  border-bottom: 1px solid #e0e0e0;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.modal-header h2 {
  margin: 0;
  font-size: 1.5rem;
}

.close-btn {
  background: none;
  border: none;
  font-size: 2rem;
  cursor: pointer;
  color: #666;
}

.close-btn:hover {
  color: #000;
}

.modal-content {
  display: grid;
  grid-template-columns: 300px 1fr 350px;
  gap: 1rem;
  padding: 1rem;
  overflow-y: auto;
  flex: 1;
}

.controls-panel,
.timeline-panel,
.suggestions-panel {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.control-group label {
  font-weight: 500;
}

.range-inputs {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.btn-generate {
  padding: 0.75rem;
  background: #4caf50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-weight: 500;
}

.btn-generate:hover:not(:disabled) {
  background: #45a049;
}

.btn-generate:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.progression-slots {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.progression-slot {
  padding: 0.75rem;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  background: #f9f9f9;
}

.progression-slot.locked {
  background: #fff3cd;
  border-color: #ffc107;
}

.slot-header {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.slot-roman {
  font-weight: bold;
  font-size: 1.1rem;
}

.slot-name {
  flex: 1;
}

.lock-btn {
  background: none;
  border: none;
  cursor: pointer;
  opacity: 0.5;
}

.lock-btn.active {
  opacity: 1;
}

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.suggestion-item {
  padding: 1rem;
  border: 2px solid #e0e0e0;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.suggestion-item:hover {
  border-color: #4caf50;
}

.suggestion-item.selected {
  border-color: #4caf50;
  background: #f1f8f4;
}

.suggestion-header {
  display: flex;
  gap: 0.5rem;
  align-items: center;
  margin-bottom: 0.5rem;
}

.suggestion-rank {
  font-weight: bold;
  color: #666;
}

.suggestion-title {
  flex: 1;
  font-weight: 500;
}

.suggestion-score {
  color: #4caf50;
  font-weight: bold;
}

.suggestion-actions {
  display: flex;
  gap: 0.5rem;
  margin-top: 0.5rem;
}

.btn-preview,
.btn-apply {
  padding: 0.5rem 1rem;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.9rem;
}

.btn-preview {
  background: #2196f3;
  color: white;
}

.btn-apply {
  background: #4caf50;
  color: white;
}

.modal-footer {
  padding: 1rem;
  border-top: 1px solid #e0e0e0;
  display: flex;
  justify-content: flex-end;
}

.empty-progression,
.no-suggestions {
  padding: 2rem;
  text-align: center;
  color: #999;
  font-style: italic;
}

.quick-insert-section {
  margin-bottom: 1.5rem;
  padding: 1rem;
  background: #f5f5f5;
  border-radius: 4px;
}

.quick-insert-section h4 {
  margin: 0 0 0.5rem 0;
  font-size: 1em;
  color: #333;
}

.quick-insert-hint {
  margin: 0 0 0.75rem 0;
  font-size: 0.9em;
  color: #666;
}

.quick-insert-chips {
  display: flex;
  flex-wrap: wrap;
  gap: 0.5rem;
}

.quick-insert-chip {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 0.5rem 0.75rem;
  background: #fff;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 50px;
}

.quick-insert-chip:hover {
  background: #e8f4f8;
  border-color: #4caf50;
}

.quick-insert-chip .chip-roman {
  font-weight: bold;
  font-size: 1em;
  color: #333;
}

.quick-insert-chip .chip-name {
  font-size: 0.8em;
  color: #666;
  margin-top: 2px;
}

.loading-chords {
  padding: 1rem;
  text-align: center;
  color: #999;
  font-style: italic;
}
</style>

