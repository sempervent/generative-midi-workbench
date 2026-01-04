<template>
  <div class="theory-overlay-panel">
    <div class="panel-header">
      <h3>Theory Overlay</h3>
    </div>

    <div v-if="analysis" class="analysis-section">
      <div class="analysis-info">
        <div class="info-item">
          <label>Key:</label>
          <span>{{ analysis.detected_key || project?.key_tonic || 'C' }}</span>
        </div>
        <div class="info-item">
          <label>Mode:</label>
          <span>{{ analysis.detected_mode || project?.mode || 'ionian' }}</span>
        </div>
        <div class="info-item">
          <label>Harmonic Rhythm:</label>
          <span>{{ analysis.harmonic_rhythm.toFixed(2) }} chords/bar</span>
        </div>
      </div>
    </div>

    <div class="controls-section">
      <div class="control-group">
        <label>Seed</label>
        <input v-model.number="localSeed" type="number" />
      </div>
      <div class="control-group">
        <label>Complexity</label>
        <input v-model.number="params.complexity" type="range" min="0" max="1" step="0.1" />
        <span>{{ params.complexity.toFixed(1) }}</span>
      </div>
      <div class="control-group">
        <label>Tension</label>
        <input v-model.number="params.tension" type="range" min="0" max="1" step="0.1" />
        <span>{{ params.tension.toFixed(1) }}</span>
      </div>
      <div class="control-group">
        <label>Density</label>
        <input v-model.number="params.density" type="range" min="0" max="1" step="0.1" />
        <span>{{ params.density.toFixed(1) }}</span>
      </div>
      <button @click="generateSuggestions" class="primary" :disabled="loading">
        {{ loading ? 'Generating...' : 'Generate Suggestions' }}
      </button>
    </div>

    <div v-if="currentRun" class="suggestions-section">
      <div class="tabs">
        <button
          v-for="kind in ['harmony', 'rhythm', 'melody']"
          :key="kind"
          :class="{ active: activeTab === kind }"
          @click="activeTab = kind"
        >
          {{ kind }}
        </button>
      </div>

      <div class="suggestions-list">
        <SuggestionCard
          v-for="suggestion in filteredSuggestions"
          :key="suggestion.id"
          :suggestion="suggestion"
          @audition="handleAudition"
          @commit="handleCommit"
        />
        <div v-if="filteredSuggestions.length === 0" class="empty">
          No {{ activeTab }} suggestions
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import * as Tone from "tone";
import { computed, onMounted, ref, watch } from "vue";
import { type Suggestion, type SuggestionRun, suggestionsApi } from "../api/suggestions";
import { usePlayback } from "../music/playback";
import type { Project } from "../types";
import SuggestionCard from "./SuggestionCard.vue";

const props = defineProps<{
  project: Project | null;
}>();

const emit = defineEmits<{
  suggestionsCommitted: [];
}>();

const analysis = ref<{
  detected_key: string | null;
  detected_mode: string | null;
  harmonic_rhythm: number;
} | null>(null);
const currentRun = ref<SuggestionRun | null>(null);
const loading = ref(false);
const activeTab = ref<"harmony" | "rhythm" | "melody">("harmony");
const localSeed = ref<number>(0);
const params = ref({
  complexity: 0.5,
  tension: 0.5,
  density: 0.5,
});

const filteredSuggestions = computed(() => {
  if (!currentRun.value) return [];
  return currentRun.value.suggestions.filter((s) => s.kind === activeTab.value);
});

const playback = usePlayback();
let auditionEvents: Array<{
  pitch: number;
  velocity: number;
  start_tick: number;
  duration_tick: number;
}> = [];

watch(
  () => props.project,
  (newProject) => {
    if (newProject) {
      localSeed.value = newProject.seed;
      // TODO: Load analysis from backend
      analysis.value = {
        detected_key: newProject.key_tonic,
        detected_mode: newProject.mode,
        harmonic_rhythm: 1.0,
      };
    }
  },
  { immediate: true }
);

async function generateSuggestions() {
  if (!props.project) return;

  loading.value = true;
  try {
    const run = await suggestionsApi.createRun(
      props.project.id,
      localSeed.value || undefined,
      params.value
    );
    currentRun.value = run;
  } catch (error) {
    console.error("Failed to generate suggestions:", error);
    alert("Failed to generate suggestions");
  } finally {
    loading.value = false;
  }
}

async function handleAudition(suggestion: Suggestion) {
  if (!props.project) return;

  // Stop any current audition
  playback.stop();

  // Get preview events
  const previewEvents = suggestion.payload_json.preview_events;

  // Convert to playback format
  const PPQ = 480;
  const quarterNotesPerBar =
    (props.project.time_signature_num * 4) / props.project.time_signature_den;
  const ticksPerBar = quarterNotesPerBar * PPQ;
  const secondsPerTick = 60 / (props.project.bpm * PPQ);

  // Schedule events with Tone.js (only on user gesture)
  const { ensureAudioStarted } = await import("../audio/ensureAudio");
  await ensureAudioStarted();

  const synth = new Tone.PolySynth(Tone.Synth).toDestination();
  const scheduleId = Tone.now();

  for (const event of previewEvents) {
    const startTime = scheduleId + event.start_tick * secondsPerTick;
    const duration = Math.max(event.duration_tick * secondsPerTick, 0.1);
    const freq = Tone.Frequency(event.pitch, "midi").toFrequency();

    synth.triggerAttackRelease(freq, duration, startTime, event.velocity / 127);
  }

  Tone.Transport.start(scheduleId);

  // Store for cleanup
  auditionEvents = previewEvents;

  // Auto-stop after a few seconds
  setTimeout(() => {
    Tone.Transport.stop();
    Tone.Transport.cancel();
    synth.releaseAll();
    synth.dispose();
  }, 5000);
}

async function handleCommit(suggestion: Suggestion) {
  if (!props.project) return;

  try {
    await suggestionsApi.commitSuggestion(suggestion.id);
    // Refresh run to update committed status
    if (currentRun.value) {
      currentRun.value = await suggestionsApi.getRun(currentRun.value.id);
    }
    emit("suggestionsCommitted");
    alert(`Committed: ${suggestion.title}`);
  } catch (error) {
    console.error("Failed to commit suggestion:", error);
    alert("Failed to commit suggestion");
  }
}
</script>

<style scoped>
.theory-overlay-panel {
  background: #1e1e1e;
  border: 1px solid #444;
  border-radius: 4px;
  padding: 15px;
  max-height: 600px;
  overflow-y: auto;
}

.panel-header h3 {
  margin: 0 0 15px 0;
  color: #fff;
  font-size: 16px;
}

.analysis-section {
  margin-bottom: 20px;
  padding: 10px;
  background: #2a2a2a;
  border-radius: 4px;
}

.analysis-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-item {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
}

.info-item label {
  color: #aaa;
}

.info-item span {
  color: #fff;
  font-weight: bold;
}

.controls-section {
  margin-bottom: 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 10px;
}

.control-group label {
  min-width: 80px;
  font-size: 12px;
  color: #aaa;
}

.control-group input[type="number"] {
  width: 80px;
}

.control-group input[type="range"] {
  flex: 1;
}

.control-group span {
  min-width: 30px;
  font-size: 11px;
  color: #aaa;
  text-align: right;
}

.tabs {
  display: flex;
  gap: 5px;
  margin-bottom: 15px;
  border-bottom: 1px solid #444;
}

.tabs button {
  padding: 8px 16px;
  background: transparent;
  border: none;
  border-bottom: 2px solid transparent;
  color: #aaa;
  cursor: pointer;
  font-size: 12px;
}

.tabs button.active {
  color: #fff;
  border-bottom-color: #4ecdc4;
}

.suggestions-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.empty {
  text-align: center;
  padding: 20px;
  color: #666;
  font-size: 12px;
}
</style>

