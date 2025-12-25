<template>
  <div class="composer-view">
    <div class="header">
      <button @click="$router.push('/projects')">← Back</button>
      <h1>{{ project?.name || 'Loading...' }}</h1>
      <button class="primary" @click="exportMidi">Export MIDI</button>
    </div>

    <div v-if="loading" class="loading">Loading...</div>

    <div v-else class="composer-layout">
      <!-- Left Panel -->
      <div class="left-panel">
        <div class="section">
          <h3>Key & Mode</h3>
          <CircleOfFifths
            :tonic="project?.key_tonic || 'C'"
            :mode="project?.mode || 'ionian'"
            @update:tonic="updateKey"
            @update:mode="updateMode"
          />
        </div>

        <div class="section">
          <h3>Settings</h3>
          <div class="setting">
            <label>BPM</label>
            <input
              type="number"
              :value="project?.bpm"
              @change="updateBPM"
              min="20"
              max="300"
            />
          </div>
          <div class="setting">
            <label>Bars</label>
            <input
              type="number"
              :value="project?.bars"
              @change="updateBars"
              min="1"
              max="256"
            />
          </div>
          <div class="setting">
            <label>Time Signature</label>
            <div class="time-sig">
              <input
                type="number"
                :value="project?.time_signature_num"
                @change="updateTimeSigNum"
                min="1"
                max="32"
              />
              /
              <input
                type="number"
                :value="project?.time_signature_den"
                @change="updateTimeSigDen"
                min="1"
                max="32"
              />
            </div>
          </div>
        </div>

        <div class="section">
          <h3>Generate</h3>
          <div class="generate-buttons">
            <button @click="generate('full')">Full</button>
            <button @click="generate('drums')">Drums</button>
            <button @click="generate('chords')">Chords</button>
            <button @click="generate('bass')">Bass</button>
            <button @click="generate('melody')">Melody</button>
          </div>
        </div>

        <div class="section">
          <h3>Polyrhythms</h3>
          <PolyrhythmEditor
            v-if="project"
            :model-value="selectedPolyrhythmProfile"
            :project-id="project.id"
            @update:model-value="selectedPolyrhythmProfile = $event"
          />
        </div>
      </div>

      <!-- Center: Arrangement -->
      <div class="center-panel">
        <div class="transport">
          <button @click="togglePlayback">{{ isPlaying ? '⏸' : '▶' }}</button>
          <button @click="stop">⏹</button>
          <button
            :class="{ active: playbackState.loopEnabled }"
            @click="toggleLoop"
            :title="playbackState.loopEnabled ? 'Loop enabled (L)' : 'Loop disabled (L)'"
          >
            🔁
          </button>
          <div class="range-selector">
            <label>
              <input
                type="radio"
                :value="'project'"
                v-model="rangeKind"
                @change="updateRange"
              />
              Project
            </label>
            <label>
              <input
                type="radio"
                :value="'bars'"
                v-model="rangeKind"
                @change="updateRange"
              />
              Bars
            </label>
          </div>
          <div v-if="rangeKind === 'bars'" class="bar-range-inputs">
            <input
              type="number"
              v-model.number="barRange.startBar"
              @change="updateBarRange"
              min="0"
              :max="maxBar"
              placeholder="Start"
            />
            <span>–</span>
            <input
              type="number"
              v-model.number="barRange.endBar"
              @change="updateBarRange"
              :min="barRange.startBar + 1"
              :max="maxBar + 1"
              placeholder="End"
            />
          </div>
          <div v-if="playbackState.range.kind === 'bars'" class="range-label">
            Loop: bars {{ playbackState.range.startBar }}–{{ playbackState.range.endBar }}
          </div>
        </div>

        <div class="arrangement">
          <div
            v-for="track in arrangement?.tracks || []"
            :key="track.id"
            class="track"
          >
            <div class="track-header">
              <span>{{ track.name }}</span>
              <label>
                <input
                  type="checkbox"
                  :checked="!track.is_muted"
                  @change="toggleMute(track.id, !track.is_muted)"
                />
                Mute
              </label>
            </div>
            <PianoRoll :track="track" :bpm="project?.bpm || 120" />
          </div>
        </div>
      </div>

      <!-- Right Panel -->
      <div class="right-panel">
        <div class="section">
          <h3>Chord Timeline</h3>
          <ChordTimeline :arrangement="arrangement" />
        </div>

        <div class="section">
          <TheoryOverlayPanel
            :project="project"
            @suggestions-committed="handleSuggestionsCommitted"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { useRoute } from "vue-router";
import { projectsApi } from "../api/projects";
import { tracksApi } from "../api/tracks";
import ChordTimeline from "../components/ChordTimeline.vue";
import CircleOfFifths from "../components/CircleOfFifths.vue";
import PianoRoll from "../components/PianoRoll.vue";
import PolyrhythmEditor from "../components/PolyrhythmEditor.vue";
import TheoryOverlayPanel from "../components/TheoryOverlayPanel.vue";
import { usePlayback } from "../music/playback";
import { computeProjectLengthBars } from "../music/transportLoop";
import { useProjectStore } from "../stores/project";
import type { PlaybackRange, PlaybackState, PolyrhythmProfile } from "../types";

const route = useRoute();
const store = useProjectStore();
const playback = usePlayback();

const project = computed(() => store.currentProject);
const arrangement = computed(() => store.currentArrangement);
const loading = computed(() => store.loading);
const isPlaying = ref(false);
const selectedPolyrhythmProfile = ref<PolyrhythmProfile | null>(null);

// Playback state
const playbackState = ref<PlaybackState>({
  isPlaying: false,
  loopEnabled: true, // default true
  range: { kind: "project" }, // default project
});

// Range selector state
const rangeKind = ref<"project" | "bars">("project");
const barRange = ref({ startBar: 0, endBar: 8 });

// Load from localStorage
function loadPlaybackState() {
  const saved = localStorage.getItem("midinecromancer-playback-state");
  if (saved) {
    try {
      const parsed = JSON.parse(saved);
      playbackState.value.loopEnabled = parsed.loopEnabled ?? true;
      playbackState.value.range = parsed.range ?? { kind: "project" };
      rangeKind.value = parsed.range?.kind === "bars" ? "bars" : "project";
      if (parsed.range?.kind === "bars") {
        barRange.value = {
          startBar: parsed.range.startBar ?? 0,
          endBar: parsed.range.endBar ?? 8,
        };
      }
    } catch (e) {
      // Use defaults
    }
  }
}

// Save to localStorage
function savePlaybackState() {
  localStorage.setItem(
    "midinecromancer-playback-state",
    JSON.stringify({
      loopEnabled: playbackState.value.loopEnabled,
      range: playbackState.value.range,
    })
  );
}

// Compute max bar for range inputs
const maxBar = computed(() => {
  if (!arrangement.value) return 0;
  return computeProjectLengthBars(arrangement.value);
});

onMounted(async () => {
  const id = route.params.id as string;
  await store.loadProject(id);
  loadPlaybackState();

  // Keyboard shortcut: L toggles loop
  window.addEventListener("keydown", handleKeydown);
});

onUnmounted(() => {
  window.removeEventListener("keydown", handleKeydown);
  // Stop playback when leaving view
  if (isPlaying.value) {
    stop();
  }
});

// Stop playback when project changes
watch(
  () => route.params.id,
  () => {
    if (isPlaying.value) {
      stop();
    }
  }
);

function handleKeydown(e: KeyboardEvent) {
  // L toggles loop (only if not typing in an input)
  if (e.key === "l" || e.key === "L") {
    const target = e.target as HTMLElement;
    if (target.tagName !== "INPUT" && target.tagName !== "TEXTAREA") {
      e.preventDefault();
      toggleLoop();
    }
  }
}

function toggleLoop() {
  playbackState.value.loopEnabled = !playbackState.value.loopEnabled;
  savePlaybackState();

  // If currently playing, update loop state
  if (isPlaying.value && arrangement.value && project.value) {
    // Restart with new loop state
    playback.stop();
    isPlaying.value = false;
    setTimeout(() => {
      togglePlayback();
    }, 100);
  }
}

function updateRange() {
  if (rangeKind.value === "project") {
    playbackState.value.range = { kind: "project" };
  } else {
    playbackState.value.range = {
      kind: "bars",
      startBar: barRange.value.startBar,
      endBar: barRange.value.endBar,
    };
  }
  savePlaybackState();
}

function updateBarRange() {
  // Validate range
  if (barRange.value.endBar <= barRange.value.startBar) {
    // Auto-fix: set endBar to startBar + 1
    barRange.value.endBar = barRange.value.startBar + 1;
  }

  playbackState.value.range = {
    kind: "bars",
    startBar: barRange.value.startBar,
    endBar: barRange.value.endBar,
  };
  savePlaybackState();
}

// Watch arrangement changes to update max bar
watch(arrangement, (newArr) => {
  if (newArr && rangeKind.value === "bars") {
    const max = computeProjectLengthBars(newArr);
    if (barRange.value.endBar > max) {
      barRange.value.endBar = max;
      updateBarRange();
    }
  }
});

function updateKey(tonic: string) {
  if (!project.value) return;
  store.updateProject(project.value.id, { key_tonic: tonic });
}

function updateMode(mode: string) {
  if (!project.value) return;
  store.updateProject(project.value.id, { mode });
}

function updateBPM(e: Event) {
  const value = Number.parseInt((e.target as HTMLInputElement).value);
  if (!project.value) return;
  store.updateProject(project.value.id, { bpm: value });
}

function updateBars(e: Event) {
  const value = Number.parseInt((e.target as HTMLInputElement).value);
  if (!project.value) return;
  store.updateProject(project.value.id, { bars: value });
}

function updateTimeSigNum(e: Event) {
  const value = Number.parseInt((e.target as HTMLInputElement).value);
  if (!project.value) return;
  store.updateProject(project.value.id, { time_signature_num: value });
}

function updateTimeSigDen(e: Event) {
  const value = Number.parseInt((e.target as HTMLInputElement).value);
  if (!project.value) return;
  store.updateProject(project.value.id, { time_signature_den: value });
}

async function generate(kind: string) {
  if (!project.value) return;
  await store.generate(kind);
}

async function toggleMute(trackId: string, muted: boolean) {
  if (!project.value) return;
  try {
    await tracksApi.toggleMute(trackId, muted);
    // Reload arrangement to get updated state
    await store.loadArrangement(project.value.id);
  } catch (error) {
    console.error("Failed to toggle mute:", error);
    alert("Failed to toggle mute");
  }
}

async function togglePlayback() {
  if (!arrangement.value || !project.value) {
    console.warn("Cannot play: missing arrangement or project", {
      arrangement: arrangement.value,
      project: project.value,
    });
    return;
  }

  // Validate range if bars
  if (playbackState.value.range.kind === "bars") {
    const range = playbackState.value.range;
    if (range.endBar <= range.startBar) {
      alert(
        `Invalid range: end bar (${range.endBar}) must be greater than start bar (${range.startBar})`
      );
      return;
    }
  }

  if (isPlaying.value) {
    playback.stop();
    isPlaying.value = false;
    playbackState.value.isPlaying = false;
  } else {
    try {
      await playback.start(
        arrangement.value,
        project.value.bpm,
        playbackState.value.loopEnabled,
        playbackState.value.range
      );
      isPlaying.value = playback.getIsPlaying();
      playbackState.value.isPlaying = isPlaying.value;
    } catch (error) {
      console.error("Playback error:", error);
      isPlaying.value = false;
      playbackState.value.isPlaying = false;
    }
  }
}

function stop() {
  playback.stop();
  isPlaying.value = false;
  playbackState.value.isPlaying = false;
}

async function exportMidi() {
  if (!project.value) return;
  try {
    const blob = await projectsApi.exportMidi(project.value.id);
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `${project.value.name}.mid`;
    a.click();
    URL.revokeObjectURL(url);
  } catch (error) {
    console.error("Export failed:", error);
    alert("Failed to export MIDI");
  }
}

async function handleSuggestionsCommitted() {
  // Refresh arrangement after commit
  if (project.value) {
    await store.loadArrangement(project.value.id);
  }
}
</script>

<style scoped>
.composer-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.header {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px;
  border-bottom: 1px solid #444;
  background: #222;
}

.header h1 {
  flex: 1;
  font-size: 24px;
}

.composer-layout {
  display: flex;
  flex: 1;
  overflow: hidden;
}

.left-panel {
  width: 300px;
  border-right: 1px solid #444;
  overflow-y: auto;
  padding: 20px;
  background: #1e1e1e;
}

.section {
  margin-bottom: 30px;
}

.section h3 {
  margin-bottom: 15px;
  color: #fff;
  font-size: 16px;
}

.setting {
  margin-bottom: 15px;
}

.setting label {
  display: block;
  margin-bottom: 5px;
  color: #aaa;
  font-size: 14px;
}

.setting input {
  width: 100%;
}

.time-sig {
  display: flex;
  align-items: center;
  gap: 8px;
}

.time-sig input {
  width: 60px;
}

.generate-buttons {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.generate-buttons button {
  width: 100%;
}

.center-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.transport {
  padding: 15px 20px;
  border-bottom: 1px solid #444;
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.transport button {
  padding: 8px 16px;
  border: 1px solid #444;
  border-radius: 4px;
  background: #2a2a2a;
  color: #fff;
  cursor: pointer;
  font-size: 16px;
}

.transport button:hover {
  background: #333;
}

.transport button.active {
  background: #0066cc;
  border-color: #0066cc;
}

.range-selector {
  display: flex;
  gap: 10px;
  margin-left: 10px;
}

.range-selector label {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #aaa;
  font-size: 14px;
  cursor: pointer;
}

.bar-range-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-left: 10px;
}

.bar-range-inputs input {
  width: 60px;
  padding: 4px 8px;
  border: 1px solid #444;
  border-radius: 4px;
  background: #1a1a1a;
  color: #fff;
  font-size: 14px;
}

.range-label {
  margin-left: 10px;
  color: #aaa;
  font-size: 12px;
}

.arrangement {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.track {
  margin-bottom: 30px;
  background: #2a2a2a;
  border-radius: 4px;
  padding: 15px;
}

.track-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  color: #fff;
}

.right-panel {
  width: 300px;
  border-left: 1px solid #444;
  overflow-y: auto;
  padding: 20px;
  background: #1e1e1e;
}

.loading {
  text-align: center;
  padding: 40px;
  color: #aaa;
}
</style>

