<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay" @click="handleOverlayClick">
      <div class="generate-modal" @click.stop>
        <div class="modal-header">
          <h2>Regenerate Segments</h2>
          <button class="close-btn" @click="close" title="Close (Esc)">×</button>
        </div>

        <div class="modal-content">
          <!-- Global Settings -->
          <div class="section">
            <h3>Global Settings</h3>
            <div class="form-grid">
              <div class="form-group">
                <label>Seed</label>
                <div class="seed-control">
                  <input
                    v-model.number="localSeed"
                    type="number"
                    min="0"
                  />
                  <button @click="randomizeSeed" class="btn-small">🎲 Randomize</button>
                </div>
              </div>
              <div class="form-group">
                <label>Variation</label>
                <input
                  v-model.number="variation"
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                />
                <span class="value">{{ variation.toFixed(2) }}</span>
              </div>
            </div>
          </div>

          <!-- Segment Tabs -->
          <div class="section">
            <div class="tabs">
              <button
                v-for="kind in allKinds"
                :key="kind"
                class="tab"
                :class="{ active: activeTab === kind }"
                @click="activeTab = kind"
              >
                {{ getKindLabel(kind) }}
              </button>
            </div>

            <!-- Beats Tab -->
            <div v-if="activeTab === 'beats'" class="tab-content">
              <div class="enable-toggle">
                <label>
                  <input
                    v-model="enabled.beats"
                    type="checkbox"
                  />
                  Enable Beats Regeneration
                </label>
              </div>
              <div v-if="enabled.beats" class="form-grid">
                <div class="form-group">
                  <label>Kit</label>
                  <select v-model="beatsParams.kit">
                    <option value="gm_hiphop">Hip-Hop</option>
                    <option value="gm_trap">Trap</option>
                    <option value="gm_boom_bap">Boom Bap</option>
                    <option value="gm_blank">Minimal</option>
                  </select>
                </div>
                <div class="form-group">
                  <label>Density</label>
                  <input
                    v-model.number="beatsParams.density"
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                  />
                  <span class="value">{{ beatsParams.density.toFixed(2) }}</span>
                </div>
                <div class="form-group">
                  <label>Swing</label>
                  <input
                    v-model.number="beatsParams.swing"
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                  />
                  <span class="value">{{ beatsParams.swing.toFixed(2) }}</span>
                </div>
                <div class="form-group">
                  <label>Ghost Notes</label>
                  <input
                    v-model="beatsParams.ghost_notes"
                    type="checkbox"
                  />
                </div>
                <div class="form-group">
                  <label>Pause Probability</label>
                  <input
                    v-model.number="beatsParams.pause_probability"
                    type="range"
                    min="0"
                    max="0.5"
                    step="0.05"
                  />
                  <span class="value">{{ beatsParams.pause_probability.toFixed(2) }}</span>
                </div>
                <div class="form-group">
                  <label>Hats Pattern</label>
                  <select v-model="beatsParams.pattern">
                    <option value="straight">Straight</option>
                    <option value="syncopated">Syncopated</option>
                    <option value="euclidean">Euclidean</option>
                    <option value="polyrhythm">Polyrhythm</option>
                  </select>
                </div>
              </div>
            </div>

            <!-- Chords Tab -->
            <div v-if="activeTab === 'chords'" class="tab-content">
              <div class="enable-toggle">
                <label>
                  <input
                    v-model="enabled.chords"
                    type="checkbox"
                  />
                  Enable Chords Regeneration
                </label>
              </div>
              <div v-if="enabled.chords" class="form-grid">
                <div class="form-group">
                  <label>Progression Style</label>
                  <select v-model="chordsParams.progression_style">
                    <option value="pop">Pop</option>
                    <option value="rap_minor">Rap Minor</option>
                    <option value="jazzy">Jazzy</option>
                    <option value="modal">Modal</option>
                    <option value="circle_fifths">Circle of Fifths</option>
                  </select>
                </div>
                <div class="form-group">
                  <label>Chord Rhythm</label>
                  <select v-model="chordsParams.chord_rhythm">
                    <option value="block">Block</option>
                    <option value="syncopated">Syncopated</option>
                    <option value="arp-lite">Arp-lite</option>
                  </select>
                </div>
                <div class="form-group">
                  <label>Strum Preset (beats)</label>
                  <select v-model="chordsParams.strum_beats">
                    <option :value="0">None</option>
                    <option :value="0.0625">1/16</option>
                    <option :value="0.125">1/8</option>
                    <option :value="0.25">1/4</option>
                    <option :value="0.5">1/2</option>
                  </select>
                </div>
                <div class="form-group">
                  <label>Voicing</label>
                  <select v-model="chordsParams.voicing">
                    <option value="root">Root</option>
                    <option value="open">Open</option>
                    <option value="drop2">Drop-2</option>
                    <option value="tight">Tight</option>
                  </select>
                </div>
                <div class="form-group">
                  <label>Tension (borrowed chords)</label>
                  <input
                    v-model.number="chordsParams.borrowed_chords"
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                  />
                  <span class="value">{{ chordsParams.borrowed_chords.toFixed(2) }}</span>
                </div>
              </div>
            </div>

            <!-- Bass Tab -->
            <div v-if="activeTab === 'bass'" class="tab-content">
              <div class="enable-toggle">
                <label>
                  <input
                    v-model="enabled.bass"
                    type="checkbox"
                  />
                  Enable Bass Regeneration
                </label>
              </div>
              <div v-if="enabled.bass" class="form-grid">
                <div class="form-group">
                  <label>Follow Roots</label>
                  <input
                    v-model.number="bassParams.follow_kicks"
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                  />
                  <span class="value">{{ bassParams.follow_kicks.toFixed(2) }}</span>
                </div>
                <div class="form-group">
                  <label>Rhythm Lock</label>
                  <select v-model="bassParams.rhythm_lock">
                    <option value="drums">Lock to Drums</option>
                    <option value="chords">Lock to Chords</option>
                    <option value="free">Free</option>
                  </select>
                </div>
                <div class="form-group">
                  <label>Octave Range</label>
                  <input
                    v-model.number="bassParams.octave"
                    type="number"
                    min="1"
                    max="4"
                  />
                </div>
                <div class="form-group">
                  <label>Syncopation</label>
                  <input
                    v-model.number="bassParams.rhythmic_density"
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                  />
                  <span class="value">{{ bassParams.rhythmic_density.toFixed(2) }}</span>
                </div>
              </div>
            </div>

            <!-- Melody Tab -->
            <div v-if="activeTab === 'melody'" class="tab-content">
              <div class="enable-toggle">
                <label>
                  <input
                    v-model="enabled.melody"
                    type="checkbox"
                  />
                  Enable Melody Regeneration
                </label>
              </div>
              <div v-if="enabled.melody" class="form-grid">
                <div class="form-group">
                  <label>Range</label>
                  <select v-model="melodyParams.range">
                    <option value="narrow">Narrow</option>
                    <option value="medium">Medium</option>
                    <option value="wide">Wide</option>
                  </select>
                </div>
                <div class="form-group">
                  <label>Stepwise vs Leapy</label>
                  <input
                    v-model.number="melodyParams.leapiness"
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                  />
                  <span class="value">{{ melodyParams.leapiness.toFixed(2) }}</span>
                </div>
                <div class="form-group">
                  <label>Motif Repeat</label>
                  <input
                    v-model.number="melodyParams.motif_repetition"
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                  />
                  <span class="value">{{ melodyParams.motif_repetition.toFixed(2) }}</span>
                </div>
                <div class="form-group">
                  <label>Rhythmic Density</label>
                  <input
                    v-model.number="melodyParams.syncopation"
                    type="range"
                    min="0"
                    max="1"
                    step="0.05"
                  />
                  <span class="value">{{ melodyParams.syncopation.toFixed(2) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="modal-footer">
          <button class="btn btn-secondary" @click="handlePreview">Preview</button>
          <button class="btn btn-primary" @click="handleApply" :disabled="!hasEnabledSegment">
            Apply
          </button>
          <button class="btn btn-secondary" @click="close">Cancel</button>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { clipsApi } from "../api/clips";
import type { ArrangementSegment } from "../types";

const props = defineProps<{
  clipId: string | null;
  clipKind: "beats" | "chords" | "bass" | "melody" | null;
  isOpen: boolean;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "applied"): void;
}>();

const allKinds: Array<"beats" | "chords" | "bass" | "melody"> = [
  "beats",
  "chords",
  "bass",
  "melody",
];
const activeTab = ref<"beats" | "chords" | "bass" | "melody">("beats");

const localSeed = ref(Math.floor(Math.random() * 1000000));
const variation = ref(0.3);

const enabled = ref({
  beats: false,
  chords: false,
  bass: false,
  melody: false,
});

const beatsParams = ref({
  kit: "gm_hiphop",
  density: 0.7,
  swing: 0.0,
  ghost_notes: true,
  pause_probability: 0.0,
  pattern: "straight",
});

const chordsParams = ref({
  progression_style: "rap_minor",
  chord_rhythm: "block",
  strum_beats: 0,
  voicing: "root",
  borrowed_chords: 0.1,
});

const bassParams = ref({
  follow_kicks: 0.8,
  rhythm_lock: "drums",
  octave: 2,
  rhythmic_density: 0.6,
});

const melodyParams = ref({
  range: "medium",
  leapiness: 0.3,
  motif_repetition: 0.5,
  syncopation: 0.3,
});

const previewResult = ref<any>(null);

const hasEnabledSegment = computed(() => {
  return enabled.value.beats || enabled.value.chords || enabled.value.bass || enabled.value.melody;
});

// Initialize based on clip kind
watch(
  () => props.isOpen,
  (open) => {
    if (open && props.clipKind) {
      activeTab.value = props.clipKind;
      enabled.value[props.clipKind] = true;
      localSeed.value = Math.floor(Math.random() * 1000000);
      previewResult.value = null;
    }
  },
  { immediate: true }
);

function getKindLabel(kind: string): string {
  const labels: Record<string, string> = {
    beats: "🥁 Beats",
    chords: "🎹 Chords",
    bass: "🎸 Bass",
    melody: "🎵 Melody",
  };
  return labels[kind] || kind;
}

function randomizeSeed() {
  localSeed.value = Math.floor(Math.random() * 1000000);
}

async function handlePreview() {
  if (!props.clipId || !hasEnabledSegment.value) {
    alert("Please enable at least one segment type");
    return;
  }

  try {
    // Preview each enabled segment
    const previews: any[] = [];
    for (const kind of allKinds) {
      if (enabled.value[kind]) {
        const params = getParamsForKind(kind);
        const result = await clipsApi.previewRegenerate(props.clipId, {
          kind,
          seed: localSeed.value,
          variation: variation.value,
          params,
          preview: true,
        });
        previews.push(result);
      }
    }
    previewResult.value = previews;
    // TODO: Show preview in UI (ghost cards or play preview)
    console.log("Preview generated:", previewResult.value);
  } catch (error) {
    console.error("Preview failed:", error);
    alert("Failed to generate preview");
  }
}

async function handleApply() {
  if (!props.clipId || !hasEnabledSegment.value) {
    alert("Please enable at least one segment type");
    return;
  }

  try {
    // Apply each enabled segment
    for (const kind of allKinds) {
      if (enabled.value[kind]) {
        const params = getParamsForKind(kind);
        await clipsApi.regenerate(props.clipId, {
          kind,
          seed: localSeed.value,
          variation: variation.value,
          params,
          preview: false,
        });
      }
    }
    emit("applied");
    close();
  } catch (error) {
    console.error("Regeneration failed:", error);
    alert("Failed to regenerate segments");
  }
}

function getParamsForKind(kind: string): Record<string, any> {
  switch (kind) {
    case "beats":
      return beatsParams.value;
    case "chords":
      return chordsParams.value;
    case "bass":
      return bassParams.value;
    case "melody":
      return melodyParams.value;
    default:
      return {};
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

.generate-modal {
  background: #2a2a2a;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
  width: 90vw;
  max-width: 700px;
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

.seed-control {
  display: flex;
  gap: 10px;
  align-items: center;
}

.seed-control input {
  flex: 1;
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

.enable-toggle {
  margin-bottom: 15px;
  padding: 10px;
  background: #333;
  border-radius: 4px;
}

.enable-toggle label {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  font-weight: 500;
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
</style>

