<template>
  <Teleport to="body">
    <div
      v-if="isOpen"
      class="popover-overlay"
      @click="handleOverlayClick"
    >
      <div
        ref="popoverRef"
        class="track-popover"
        :class="`kind-${context.kind}`"
        :style="popoverStyle"
        @click.stop
      >
        <!-- Header -->
        <div class="popover-header">
          <div class="header-left">
            <span class="kind-icon">{{ getKindIcon(context.kind) }}</span>
            <span class="kind-name">{{ context.kind }}</span>
          </div>
          <button class="close-btn" @click="close" title="Close (Esc)">×</button>
        </div>

        <!-- Section A: Overview -->
        <div class="section">
          <div class="section-header" @click="toggleSection('overview')">
            <h3>Overview</h3>
            <span class="toggle-icon">{{ sections.overview ? "−" : "+" }}</span>
          </div>
          <div v-if="sections.overview" class="section-content">
            <div class="overview-grid">
              <div class="info-item">
                <label>Start Bar</label>
                <input
                  v-model.number="localStartBar"
                  type="number"
                  min="0"
                  step="0.25"
                  @input="updatePreview({ start_bar: localStartBar })"
                />
              </div>
              <div class="info-item">
                <label>Length</label>
                <input
                  v-model.number="localLengthBars"
                  type="number"
                  min="0.25"
                  step="0.25"
                  @input="updatePreview({ length_bars: localLengthBars })"
                />
              </div>
              <div class="info-item intensity-item">
                <label>Intensity</label>
                <div class="intensity-control">
                  <input
                    v-model.number="localIntensity"
                    type="range"
                    min="0"
                    max="2"
                    step="0.05"
                    @input="updatePreview({ intensity: localIntensity })"
                  />
                  <span>{{ localIntensity.toFixed(2) }}</span>
                </div>
              </div>
            </div>
            <div class="quick-toggles">
              <label>
                <input
                  v-model="localMuted"
                  type="checkbox"
                  @change="updatePreview({ mute: localMuted })"
                />
                Mute
              </label>
              <label>
                <input
                  v-model="localSoloed"
                  type="checkbox"
                  @change="updatePreview({ is_soloed: localSoloed })"
                />
                Solo
              </label>
              <label>
                <input
                  v-model="localLocked"
                  type="checkbox"
                  @change="updatePreview({ is_locked: localLocked })"
                />
                Lock
              </label>
            </div>
            <div class="quick-actions">
              <button @click="handleDuplicate">Duplicate</button>
              <button @click="handleHalfTime">Half Time</button>
              <button @click="handleDoubleTime">Double Time</button>
              <button class="danger" @click="handleDelete">Delete</button>
            </div>
          </div>
        </div>

        <!-- Section B: Generate / Regenerate -->
        <div class="section">
          <div class="section-header" @click="toggleSection('regenerate')">
            <h3>Generate / Regenerate</h3>
            <span class="toggle-icon">{{ sections.regenerate ? "−" : "+" }}</span>
          </div>
          <div v-if="sections.regenerate" class="section-content">
            <div class="regenerate-controls">
              <div class="seed-control">
                <label>
                  <input
                    v-model="seedLocked"
                    type="checkbox"
                  />
                  Lock Seed
                </label>
                <input
                  v-model.number="localSeed"
                  type="number"
                  :disabled="seedLocked"
                />
              </div>
              <div class="variation-control">
                <label>Variation</label>
                <input
                  v-model.number="variationAmount"
                  type="range"
                  min="0"
                  max="1"
                  step="0.1"
                />
                <span>{{ variationAmount.toFixed(1) }}</span>
              </div>
              <div class="scope-control">
                <label>Scope</label>
                <select v-model="regenerateScope">
                  <option value="all">All</option>
                  <option value="rhythm">Rhythm Only</option>
                  <option value="notes">Notes Only</option>
                  <option value="velocity">Velocity Only</option>
                  <option value="timing">Timing Only</option>
                </select>
              </div>
              <label class="keep-structure">
                <input
                  v-model="keepStructure"
                  type="checkbox"
                />
                Keep Structure
              </label>
              <div class="regenerate-actions">
                <button
                  v-if="context?.kind === 'chords'"
                  @click="openChordGenModal"
                  class="btn-regenerate"
                >
                  Generate Chord Progression
                </button>
                <button
                  v-else
                  @click="openGenerateModal"
                  class="btn-regenerate"
                >
                  Open Regenerate Modal
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Section C: Transform -->
        <div class="section">
          <div class="section-header" @click="toggleSection('transform')">
            <h3>Transform</h3>
            <span class="toggle-icon">{{ sections.transform ? "−" : "+" }}</span>
          </div>
          <div v-if="sections.transform" class="section-content">
            <div class="transform-controls">
              <div class="time-scaling">
                <label>Time Scaling</label>
                <div class="button-group">
                  <button @click="handleHalfTime">Half Time</button>
                  <button @click="handleDoubleTime">Double Time</button>
                </div>
              </div>
              <div class="offset-control">
                <label>Offset</label>
                <div class="offset-inputs">
                  <button @click="offsetBars(-1)">−1</button>
                  <input
                    v-model.number="offsetBarsValue"
                    type="number"
                    step="1"
                    @change="applyOffset"
                  />
                  <button @click="offsetBars(1)">+1</button>
                </div>
              </div>
              <div class="swing-control">
                <label>Swing</label>
                <input
                  v-model.number="swingAmount"
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  @input="updateSwing"
                />
                <span>{{ swingAmount.toFixed(2) }}</span>
              </div>
              <div class="density-control">
                <label>Density</label>
                <input
                  v-model.number="density"
                  type="range"
                  min="0"
                  max="1"
                  step="0.05"
                  @input="updateDensity"
                />
                <span>{{ density.toFixed(2) }}</span>
              </div>
            </div>
          </div>
        </div>

        <!-- Section D: Advanced (Kind-Specific) -->
        <div class="section">
          <div class="section-header" @click="toggleSection('advanced')">
            <h3>Advanced</h3>
            <span class="toggle-icon">{{ sections.advanced ? "−" : "+" }}</span>
          </div>
          <div v-if="sections.advanced" class="section-content">
            <component
              :is="advancedComponent"
              :context="context"
              :params="localParams"
              @update:params="updateParams"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- Generate Modal -->
    <GenerateModal
      v-if="context?.kind !== 'chords'"
      :is-open="generateModalOpen"
      :clip-id="props.context?.clipId || null"
      :clip-kind="props.context?.kind || null"
      @close="generateModalOpen = false"
      @applied="handleGenerateApplied"
    />

    <!-- Chord Generation Modal V2 -->
    <ChordGenerationModalV2
      v-if="context?.kind === 'chords'"
      :is-open="chordGenModalOpen"
      :project-id="props.projectId || ''"
      :clip-id="props.context?.clipId || null"
      :start-bar="props.context?.startBar"
      :length-bars="props.context?.lengthBars"
      :bpm="props.bpm || 120"
      :time-signature-num="props.timeSignatureNum || 4"
      :time-signature-den="props.timeSignatureDen || 4"
      @close="chordGenModalOpen = false"
      @applied="handleChordGenApplied"
    />
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { clipsApi } from "../api/clips";
import { usePreviewSession } from "../composables/usePreviewSession";
import type { ArrangementSegment } from "../types";
import ChordGenerationModal from "./ChordGenerationModal.vue";
import ChordGenerationModalV2 from "./ChordGenerationModalV2.vue";
import GenerateModal from "./GenerateModal.vue";
import BassAdvanced from "./TrackPopover/BassAdvanced.vue";
import BeatsAdvanced from "./TrackPopover/BeatsAdvanced.vue";
import ChordsAdvanced from "./TrackPopover/ChordsAdvanced.vue";
import MelodyAdvanced from "./TrackPopover/MelodyAdvanced.vue";

export interface TrackPopoverContext {
  clipId: string;
  kind: "drums" | "chords" | "bass" | "melody";
  startBar: number;
  lengthBars: number;
  params: Record<string, any>;
  segment: ArrangementSegment;
  anchorElement?: HTMLElement;
}

const props = defineProps<{
  context: TrackPopoverContext | null;
  isOpen: boolean;
  projectId?: string;
  bpm?: number;
  timeSignatureNum?: number;
  timeSignatureDen?: number;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "apply", segment: ArrangementSegment): void;
  (e: "preview", segment: ArrangementSegment): void;
}>();

const {
  startPreview,
  updatePreview: updatePreviewState,
  applyPreview,
  cancelPreview,
} = usePreviewSession();

const popoverRef = ref<HTMLElement | null>(null);
const sections = ref({
  overview: true,
  regenerate: false,
  transform: false,
  advanced: false,
});

const localStartBar = ref(0);
const localLengthBars = ref(0);
const localIntensity = ref(1.0);
const localMuted = ref(false);
const localSoloed = ref(false);
const localLocked = ref(false);
const localSeed = ref(0);
const seedLocked = ref(true);
const variationAmount = ref(0.3);
const regenerateScope = ref("all");
const keepStructure = ref(true);
const swingAmount = ref(0.0);
const density = ref(0.7);
const offsetBarsValue = ref(0);
const localParams = ref<Record<string, any>>({});
const hasPreviewChanges = ref(false);
const generateModalOpen = ref(false);

const popoverStyle = computed(() => {
  if (!props.context?.anchorElement) return {};
  const rect = props.context.anchorElement.getBoundingClientRect();
  const viewportWidth = window.innerWidth;
  const viewportHeight = window.innerHeight;
  const popoverWidth = 400;
  const popoverHeight = 600;

  let left = rect.left + rect.width / 2 - popoverWidth / 2;
  let top = rect.bottom + 10;

  // Keep within viewport
  if (left < 10) left = 10;
  if (left + popoverWidth > viewportWidth - 10) {
    left = viewportWidth - popoverWidth - 10;
  }
  if (top + popoverHeight > viewportHeight - 10) {
    top = rect.top - popoverHeight - 10;
  }
  if (top < 10) top = 10;

  return {
    left: `${left}px`,
    top: `${top}px`,
  };
});

const advancedComponent = computed(() => {
  switch (props.context?.kind) {
    case "drums":
      return BeatsAdvanced;
    case "chords":
      return ChordsAdvanced;
    case "bass":
      return BassAdvanced;
    case "melody":
      return MelodyAdvanced;
    default:
      return null;
  }
});

function getKindIcon(kind: string): string {
  const icons: Record<string, string> = {
    drums: "🥁",
    chords: "🎹",
    bass: "🎸",
    melody: "🎵",
  };
  return icons[kind] || "🎵";
}

function toggleSection(section: keyof typeof sections.value) {
  sections.value[section] = !sections.value[section];
}

function updatePreview(updates: Partial<ArrangementSegment>) {
  if (!props.context) return;
  hasPreviewChanges.value = true;
  updatePreviewState(updates);
  // Emit preview event for live playback
  emit("preview", { ...props.context.segment, ...updates });
}

function updateParams(newParams: Record<string, any>) {
  localParams.value = { ...localParams.value, ...newParams };
  updatePreview({ params: localParams.value });
}

function updateSwing() {
  updateParams({ swing: swingAmount.value });
}

function updateDensity() {
  updateParams({ density: density.value });
}

function offsetBars(delta: number) {
  offsetBarsValue.value += delta;
  applyOffset();
}

function applyOffset() {
  localStartBar.value = Math.max(0, props.context!.startBar + offsetBarsValue.value);
  updatePreview({ start_bar: localStartBar.value });
}

function openGenerateModal() {
  generateModalOpen.value = true;
}

function openChordGenModal() {
  chordGenModalOpen.value = true;
}

async function handleChordGenApplied() {
  // Refresh arrangement after chord generation
  if (props.context) {
    emit("apply", props.context.segment);
  }
  chordGenModalOpen.value = false;
}

async function handleGenerateApplied() {
  // Refresh arrangement after regeneration
  if (props.context) {
    // Emit apply to refresh parent
    emit("apply", props.context.segment);
  }
  generateModalOpen.value = false;
}

function handleApply() {
  if (!props.context) return;
  const applied = applyPreview();
  emit("apply", applied);
  close();
}

function handleCancel() {
  if (!props.context) return;
  cancelPreview();
  hasPreviewChanges.value = false;
  close();
}

function handleDuplicate() {
  // TODO: Implement duplicate
}

function handleHalfTime() {
  localLengthBars.value = props.context!.lengthBars * 2;
  updatePreview({ length_bars: localLengthBars.value });
}

function handleDoubleTime() {
  localLengthBars.value = Math.max(0.25, props.context!.lengthBars / 2);
  updatePreview({ length_bars: localLengthBars.value });
}

function handleDelete() {
  if (confirm("Delete this clip?")) {
    // TODO: Implement delete
    close();
  }
}

function close() {
  if (hasPreviewChanges.value) {
    if (!confirm("You have unsaved changes. Close anyway?")) {
      return;
    }
  }
  cancelPreview();
  hasPreviewChanges.value = false;
  emit("close");
}

function handleOverlayClick(event: MouseEvent) {
  // Only close if clicking directly on overlay, not on popover or anchor element
  if (event.target === event.currentTarget) {
    close();
  }
}

// Initialize local state from context
watch(
  () => props.context,
  (newContext) => {
    if (newContext) {
      localStartBar.value = newContext.startBar;
      localLengthBars.value = newContext.lengthBars;
      localIntensity.value = newContext.segment.intensity;
      localMuted.value = newContext.segment.mute;
      localSoloed.value = newContext.segment.is_soloed || false;
      localLocked.value = newContext.segment.is_locked || false;
      localParams.value = { ...newContext.params };
      swingAmount.value = newContext.params.swing || 0.0;
      density.value = newContext.params.density || 0.7;
      offsetBarsValue.value = 0;
      hasPreviewChanges.value = false;
      startPreview(newContext.segment);
    }
  },
  { immediate: true }
);

// Keyboard shortcuts
function handleKeydown(event: KeyboardEvent) {
  if (!props.isOpen) return;
  if (event.key === "Escape") {
    close();
  } else if (event.key === "Enter" && (event.metaKey || event.ctrlKey)) {
    event.preventDefault();
    handleApply();
  }
}

onMounted(() => {
  document.addEventListener("keydown", handleKeydown);
});

onUnmounted(() => {
  document.removeEventListener("keydown", handleKeydown);
});
</script>

<style scoped>
.popover-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 1000;
  background: transparent;
}

.track-popover {
  position: fixed;
  width: 400px;
  max-height: 80vh;
  background: #2a2a2a;
  border: 1px solid #555;
  border-radius: 8px;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  overflow-y: auto;
  z-index: 1001;
}

.popover-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #444;
  background: #333;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.kind-icon {
  font-size: 20px;
}

.kind-name {
  font-weight: bold;
  text-transform: capitalize;
  color: #fff;
}

.close-btn {
  width: 24px;
  height: 24px;
  padding: 0;
  background: transparent;
  border: none;
  color: #ccc;
  font-size: 20px;
  cursor: pointer;
  border-radius: 4px;
}

.close-btn:hover {
  background: #444;
  color: #fff;
}

.section {
  border-bottom: 1px solid #444;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  cursor: pointer;
  user-select: none;
}

.section-header:hover {
  background: #333;
}

.section-header h3 {
  margin: 0;
  font-size: 14px;
  color: #fff;
}

.toggle-icon {
  color: #aaa;
  font-size: 18px;
}

.section-content {
  padding: 12px 16px;
  background: #1e1e1e;
}

.overview-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 12px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.info-item label {
  font-size: 12px;
  color: #aaa;
}

.info-item input[type="number"] {
  padding: 6px;
  background: #333;
  border: 1px solid #555;
  border-radius: 4px;
  color: #fff;
  font-size: 13px;
}

.intensity-item {
  grid-column: 1 / -1;
}

.intensity-control {
  display: flex;
  align-items: center;
  gap: 8px;
}

.intensity-control input[type="range"] {
  flex: 1;
}

.intensity-control span {
  color: #fff;
  font-size: 12px;
  min-width: 40px;
  text-align: right;
}

.quick-toggles {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
}

.quick-toggles label {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #ccc;
  cursor: pointer;
}

.quick-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.quick-actions button {
  padding: 6px 12px;
  background: #4a4a4a;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.quick-actions button:hover {
  background: #5a5a5a;
}

.quick-actions button.danger {
  background: #8b2e2e;
}

.quick-actions button.danger:hover {
  background: #a03a3a;
}

.regenerate-controls,
.transform-controls {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.seed-control,
.variation-control,
.scope-control,
.swing-control,
.density-control {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.seed-control label,
.variation-control label,
.scope-control label,
.swing-control label,
.density-control label {
  font-size: 12px;
  color: #aaa;
}

.keep-structure {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 12px;
  color: #ccc;
}

.regenerate-actions {
  display: flex;
  gap: 8px;
  margin-top: 8px;
}

.regenerate-actions button {
  padding: 8px 16px;
  background: #4a4a4a;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}

.regenerate-actions button.primary {
  background: #007bff;
}

.regenerate-actions button.primary:hover {
  background: #0056b3;
}

.time-scaling,
.offset-control {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.button-group {
  display: flex;
  gap: 8px;
}

.offset-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
}

.offset-inputs button {
  width: 32px;
  height: 32px;
  padding: 0;
  background: #4a4a4a;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.offset-inputs input {
  flex: 1;
  padding: 6px;
  background: #333;
  border: 1px solid #555;
  border-radius: 4px;
  color: #fff;
  text-align: center;
}
</style>

