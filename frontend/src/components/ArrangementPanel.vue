<template>
  <div
    ref="panelRef"
    class="arrangement-panel"
    @wheel="handleWheel"
    @keydown="handleKeydown"
    tabindex="0"
  >
    <div class="panel-header">
      <h3>Arrangement</h3>
      <div class="header-controls">
        <div class="grid-selector">
          <label>Grid:</label>
          <select v-model="gridResolution" @change="updateGrid">
            <option value="1bar">1 bar</option>
            <option value="1/2">1/2</option>
            <option value="1/4">1/4</option>
            <option value="1beat">1 beat</option>
            <option value="off">Off</option>
          </select>
        </div>
        <div class="zoom-controls">
          <button @click="zoomOut" title="Zoom Out">−</button>
          <span>{{ Math.round(zoomLevel * 100) }}%</span>
          <button @click="zoomIn" title="Zoom In">+</button>
          <button @click="resetZoom" title="Reset Zoom">⌂</button>
        </div>
        <button v-if="panel" @click="refresh" class="refresh-btn">Refresh</button>
      </div>
    </div>
    <div v-if="loading" class="loading">Loading arrangement...</div>
    <div v-else-if="!panel || panel.lanes.length === 0" class="empty">
      No arrangement data. Generate content to see clips.
    </div>
    <div v-else ref="lanesContainerRef" class="lanes-container" @scroll="handleScroll">
      <div
        v-for="lane in panel.lanes"
        :key="lane.track_id"
        class="lane"
      >
        <div class="lane-header">
          <span class="lane-name">{{ lane.name || lane.kind }}</span>
        </div>
        <div
          ref="laneContentRefs"
          class="lane-content"
          :style="laneStyle"
        >
          <!-- Grid lines -->
          <div v-if="showGrid" class="grid-lines">
            <div
              v-for="bar in gridLines"
              :key="bar"
              class="grid-line"
              :class="{ 'grid-line-strong': bar % 1 === 0 }"
              :style="{ left: `${bar * pixelsPerBar}px` }"
            ></div>
          </div>

          <!-- Empty space indicator -->
          <div
            class="empty-space-indicator"
            :style="{ width: `${(panel?.bars || 1) * pixelsPerBar}px` }"
            @click="handleEmptySpaceClick($event, lane)"
          >
            <div class="empty-space-hint">+ Click to create</div>
          </div>

          <!-- Cards -->
          <ArrangementCard
            v-for="segment in lane.segments"
            :key="segment.id"
            :ref="(el) => setCardRef(segment.id, el)"
            :segment="segment"
            :pixels-per-bar="pixelsPerBar"
            :is-selected="selectedSegments.has(segment.id)"
            :is-active="activeCardId === segment.id"
            :snap-to-grid="snapToGrid"
            @click="handleCardClick($event, segment)"
            @drag-start="handleDragStart"
            @drag="handleDrag"
            @drag-end="handleDragEnd"
            @resize-start="handleResizeStart"
            @resize="handleResize"
            @resize-end="handleResizeEnd"
            @intensity-change="handleIntensityChange"
            @duplicate="handleDuplicate"
            @mute-toggle="handleMuteToggle"
            @solo-toggle="handleSoloToggle"
            @context-menu="handleContextMenu"
          />
        </div>
      </div>
    </div>

    <!-- Context menu -->
    <div
      v-if="contextMenu"
      class="context-menu"
      :style="{ left: `${contextMenu.x}px`, top: `${contextMenu.y}px` }"
      @click.stop
    >
      <div class="context-menu-item" @click="handleContextDuplicate">Duplicate</div>
      <div class="context-menu-item" @click="handleContextHalfTime">Half Time</div>
      <div class="context-menu-item" @click="handleContextDoubleTime">Double Time</div>
      <div class="context-menu-divider"></div>
      <div class="context-menu-item" @click="handleContextMute">
        {{ contextMenuSegment?.mute ? "Unmute" : "Mute" }}
      </div>
    </div>

    <!-- Track Popover -->
    <TrackPopover
      :context="popoverContext"
      :is-open="popoverOpen"
      :project-id="projectId"
      :bpm="bpm"
      :time-signature-num="timeSignatureNum"
      :time-signature-den="4"
      @close="handlePopoverClose"
      @apply="handlePopoverApply"
      @preview="handlePopoverPreview"
    />

    <!-- Segment Creation Modal -->
    <SegmentCreationModal
      :is-open="segmentModalOpen"
      :project-id="projectId"
      :start-bar="segmentModalContext?.startBar"
      :default-length-bars="4"
      @close="handleSegmentModalClose"
      @applied="handleSegmentModalApplied"
    />

    <!-- Chord Generation Modal V2 (for chords lane empty space) -->
    <ChordGenerationModalV2
      v-if="segmentModalContext?.laneKind === 'chords'"
      :is-open="chordGenModalOpen"
      :project-id="projectId"
      :start-bar="segmentModalContext?.startBar"
      :length-bars="4"
      :bpm="bpm"
      :time-signature-num="timeSignatureNum"
      :time-signature-den="4"
      @close="chordGenModalOpen = false"
      @applied="handleChordGenFromEmptyApplied"
    />
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { arrangementApi } from "../api/arrangement";
import { clipsApi } from "../api/clips";
import { useGrid } from "../composables/useGrid";
import { useZoom } from "../composables/useZoom";
import type { ArrangementLane, ArrangementPanel, ArrangementSegment } from "../types";
import ArrangementCard from "./ArrangementCard.vue";
import ChordGenerationModal from "./ChordGenerationModal.vue";
import ChordGenerationModalV2 from "./ChordGenerationModalV2.vue";
import SegmentCreationModal from "./SegmentCreationModal.vue";
import TrackPopover, { type TrackPopoverContext } from "./TrackPopover.vue";

const props = defineProps<{
  projectId: string;
  timeSignatureNum?: number;
}>();

const emit = defineEmits<(e: "card-click", segment: ArrangementSegment) => void>();

const panelRef = ref<HTMLElement | null>(null);
const lanesContainerRef = ref<HTMLElement | null>(null);
const laneContentRefs = ref<HTMLElement[]>([]);
const panel = ref<ArrangementPanel | null>(null);
const loading = ref(false);
const selectedSegments = ref<Set<string>>(new Set());
const contextMenu = ref<{ x: number; y: number } | null>(null);
const contextMenuSegment = ref<ArrangementSegment | null>(null);
const activeCardId = ref<string | null>(null);
const popoverOpen = ref(false);
const popoverContext = ref<TrackPopoverContext | null>(null);
const cardRefs = ref<Map<string, HTMLElement>>(new Map());

// Segment creation modal state
const segmentModalOpen = ref(false);
const segmentModalContext = ref<{ startBar: number; laneKind?: string } | null>(null);
const chordGenModalOpen = ref(false);
const bpm = ref(120); // TODO: Get from store/context
const timeSignatureNum = ref(4); // TODO: Get from store/context

const timeSigNum = computed(() => props.timeSignatureNum || 4);
const { gridResolution, snapToGrid, setGrid } = useGrid(timeSigNum.value);

// Watch time signature changes
watch(timeSigNum, (newVal) => {
  // Grid will recompute automatically
});
const {
  zoomLevel,
  pixelsPerBar,
  zoomIn,
  zoomOut,
  resetZoom,
  handleWheel: handleZoomWheel,
} = useZoom(60);

const showGrid = computed(() => gridResolution.value !== "off");

const gridLines = computed(() => {
  if (!panel.value || !showGrid.value) return [];
  const lines: number[] = [];
  const gridValue =
    gridResolution.value === "1bar"
      ? 1.0
      : gridResolution.value === "1/2"
        ? 0.5
        : gridResolution.value === "1/4"
          ? 0.25
          : gridResolution.value === "1beat"
            ? 1.0 / timeSigNum.value
            : 0;

  if (gridValue === 0) return [];

  for (let i = 0; i <= panel.value.bars; i += gridValue) {
    lines.push(i);
  }
  return lines;
});

const laneStyle = computed(() => {
  if (!panel.value) return { width: "100%" };
  const totalWidth = panel.value.bars * pixelsPerBar.value;
  return {
    width: `${Math.max(totalWidth, 800)}px`,
    minWidth: "100%",
  };
});

function updateGrid() {
  // Grid is reactive, no action needed
}

function handleWheel(event: WheelEvent) {
  if (event.ctrlKey || event.metaKey) {
    event.preventDefault();
    const containerWidth = lanesContainerRef.value?.clientWidth || 800;
    const centerX = event.clientX - (lanesContainerRef.value?.getBoundingClientRect().left || 0);
    handleZoomWheel(event, centerX, containerWidth);
  }
}

function handleKeydown(event: KeyboardEvent) {
  // Don't handle shortcuts if typing in an input
  const target = event.target as HTMLElement;
  if (target.tagName === "INPUT" || target.tagName === "TEXTAREA") {
    return;
  }

  // Cmd/Ctrl + D: Duplicate selected
  if ((event.metaKey || event.ctrlKey) && event.key === "d") {
    event.preventDefault();
    if (selectedSegments.value.size > 0) {
      const firstSelected = Array.from(selectedSegments.value)[0];
      const segment = findSegmentById(firstSelected);
      if (segment) {
        handleDuplicate(segment);
      }
    }
  }
  // Escape: Close popover, context menu, deselect
  if (event.key === "Escape") {
    if (popoverOpen.value) {
      handlePopoverClose();
    } else {
      contextMenu.value = null;
      selectedSegments.value.clear();
    }
  }
  // Delete: Delete selected (if implemented)
  if (event.key === "Delete" && selectedSegments.value.size > 0) {
    // TODO: Implement delete
  }
  // [ / ]: Nudge start (when popover is open)
  if (popoverOpen.value && (event.key === "[" || event.key === "]")) {
    event.preventDefault();
    if (popoverContext.value) {
      const delta = event.key === "[" ? -0.25 : 0.25;
      // This will be handled by the popover component
    }
  }
}

function setCardRef(segmentId: string, el: any) {
  if (el) {
    cardRefs.value.set(segmentId, el.$el || el);
  }
}

function handleCardClick(event: MouseEvent, segment: ArrangementSegment) {
  // Don't open popover if dragging (handled by mousedown)
  // Check if this was a synthetic click from drag/resize end
  if (event.detail === 0) return;

  const shift = event.shiftKey;
  if (shift) {
    // Multi-select
    if (selectedSegments.value.has(segment.id)) {
      selectedSegments.value.delete(segment.id);
    } else {
      selectedSegments.value.add(segment.id);
    }
  } else {
    // Single select and open popover
    selectedSegments.value.clear();
    selectedSegments.value.add(segment.id);
    activeCardId.value = segment.id;
    const cardElement = cardRefs.value.get(segment.id);
    if (cardElement) {
      openPopover(segment, cardElement);
    }
    emit("card-click", segment);
  }
}

function handleEmptySpaceClick(event: MouseEvent, lane: ArrangementLane) {
  // Only open if not clicking on a card
  if ((event.target as HTMLElement).closest(".arrangement-card")) {
    return;
  }

  const rect = (event.currentTarget as HTMLElement).getBoundingClientRect();
  const clickX = event.clientX - rect.left;
  const startBar = snapToGrid(clickX / pixelsPerBar.value);

  // For chords lane, open chord generation modal directly
  if (lane.kind === "chords") {
    segmentModalContext.value = {
      startBar,
      laneKind: lane.kind,
    };
    chordGenModalOpen.value = true;
  } else {
    // For other lanes, open segment creation modal
    segmentModalContext.value = {
      startBar,
      laneKind: lane.kind,
    };
    segmentModalOpen.value = true;
  }
}

function openPopover(segment: ArrangementSegment, anchorElement: HTMLElement, isNew = false) {
  popoverContext.value = {
    clipId: segment.id,
    kind: segment.kind,
    startBar: segment.start_bar,
    lengthBars: segment.length_bars,
    params: segment.params || {},
    segment,
    anchorElement,
  };
  popoverOpen.value = true;
}

function handlePopoverClose() {
  popoverOpen.value = false;
  activeCardId.value = null;
  popoverContext.value = null;
}

async function handlePopoverApply(segment: ArrangementSegment) {
  if (!popoverContext.value) return;

  try {
    if (segment.id.startsWith("new-")) {
      // Create new clip
      // TODO: Implement create clip endpoint
    } else {
      // Update existing clip
      await clipsApi.update(popoverContext.value.clipId, {
        start_bar: segment.start_bar,
        length_bars: segment.length_bars,
        intensity: segment.intensity,
        is_muted: segment.is_muted,
        is_soloed: segment.is_soloed || false,
        params: segment.params,
      });
    }
    await refresh();
    handlePopoverClose();
  } catch (error) {
    console.error("Failed to apply changes:", error);
    // Show error toast
  }
}

function handlePopoverPreview(segment: ArrangementSegment) {
  // TODO: Implement live preview with Tone.js
  console.log("Preview:", segment);
}

function handleDragStart(segment: ArrangementSegment) {
  // Could add visual feedback
}

function handleDrag(segment: ArrangementSegment, newStartBar: number) {
  // Live preview during drag
}

async function handleDragEnd(segment: ArrangementSegment, newStartBar: number) {
  if (Math.abs(newStartBar - segment.start_bar) < 0.01) return;

  try {
    await clipsApi.update(segment.id, { start_bar: Math.max(0, newStartBar) });
    await refresh();
  } catch (error) {
    console.error("Failed to update clip:", error);
    // Shake animation would go here
  }
}

function handleResizeStart(segment: ArrangementSegment, side: "left" | "right") {
  // Visual feedback
}

function handleResize(segment: ArrangementSegment, newStartBar: number, newLengthBars: number) {
  // Live preview
}

async function handleResizeEnd(
  segment: ArrangementSegment,
  newStartBar: number,
  newLengthBars: number
) {
  try {
    await clipsApi.update(segment.id, {
      start_bar: Math.max(0, newStartBar),
      length_bars: Math.max(0.25, newLengthBars),
    });
    await refresh();
  } catch (error) {
    console.error("Failed to resize clip:", error);
  }
}

async function handleIntensityChange(segment: ArrangementSegment, newIntensity: number) {
  try {
    await clipsApi.update(segment.id, { intensity: newIntensity });
    await refresh();
  } catch (error) {
    console.error("Failed to update intensity:", error);
  }
}

async function handleDuplicate(segment: ArrangementSegment) {
  try {
    const newStartBar = snapToGrid(segment.start_bar + segment.length_bars);
    await clipsApi.duplicate(segment.id, { new_start_bar: newStartBar });
    await refresh();
    // Select the new card
    // TODO: Get the new segment ID from response
  } catch (error) {
    console.error("Failed to duplicate clip:", error);
  }
}

async function handleMuteToggle(segment: ArrangementSegment) {
  const newMuteState = !segment.is_muted;
  if (import.meta.env.DEV || localStorage.getItem("midinecromancer:debug:muteSolo") === "true") {
    console.log("[Mute Toggle]", {
      clipId: segment.id,
      currentMute: segment.is_muted,
      newMuteState,
      kind: segment.kind,
    });
  }
  try {
    await clipsApi.update(segment.id, { is_muted: newMuteState });
    await refresh();
  } catch (error) {
    console.error("Failed to toggle mute:", error);
  }
}

async function handleSoloToggle(segment: ArrangementSegment) {
  const newSoloState = !segment.is_soloed;
  if (import.meta.env.DEV || localStorage.getItem("midinecromancer:debug:muteSolo") === "true") {
    console.log("[Solo Toggle]", {
      clipId: segment.id,
      currentSolo: segment.is_soloed,
      newSoloState,
      kind: segment.kind,
    });
  }
  try {
    await clipsApi.update(segment.id, { is_soloed: newSoloState });
    await refresh();
  } catch (error) {
    console.error("Failed to toggle solo:", error);
  }
}

function handleContextMenu(segment: ArrangementSegment, event: MouseEvent) {
  contextMenu.value = { x: event.clientX, y: event.clientY };
  contextMenuSegment.value = segment;
}

function handleContextDuplicate() {
  if (contextMenuSegment.value) {
    handleDuplicate(contextMenuSegment.value);
  }
  contextMenu.value = null;
}

async function handleContextHalfTime() {
  if (!contextMenuSegment.value) return;
  try {
    await clipsApi.timeScale(contextMenuSegment.value.id, { mode: "half" });
    await refresh();
    contextMenu.value = null;
  } catch (error) {
    console.error("Failed to scale time:", error);
  }
}

async function handleContextDoubleTime() {
  if (!contextMenuSegment.value) return;
  try {
    await clipsApi.timeScale(contextMenuSegment.value.id, { mode: "double" });
    await refresh();
    contextMenu.value = null;
  } catch (error) {
    console.error("Failed to scale time:", error);
  }
}

function handleContextMute() {
  if (contextMenuSegment.value) {
    handleMuteToggle(contextMenuSegment.value);
  }
  contextMenu.value = null;
}

function handleScroll() {
  // Sync scroll with other panes if needed
}

function findSegmentById(id: string): ArrangementSegment | null {
  if (!panel.value) return null;
  for (const lane of panel.value.lanes) {
    const segment = lane.segments.find((s) => s.id === id);
    if (segment) return segment;
  }
  return null;
}

async function loadPanel() {
  loading.value = true;
  try {
    panel.value = await arrangementApi.getPanel(props.projectId);
  } catch (error) {
    console.error("Failed to load arrangement panel:", error);
    panel.value = null;
  } finally {
    loading.value = false;
  }
}

async function refresh() {
  await loadPanel();
}

function handleSegmentModalClose() {
  segmentModalOpen.value = false;
  segmentModalContext.value = null;
}

async function handleSegmentModalApplied() {
  // Refresh arrangement to show new clips
  await refresh();
  handleSegmentModalClose();
}

async function handleChordGenFromEmptyApplied() {
  // Refresh arrangement to show new chord clips
  await refresh();
  chordGenModalOpen.value = false;
  segmentModalContext.value = null;
}

// Close context menu on outside click
onMounted(() => {
  document.addEventListener("click", () => {
    contextMenu.value = null;
  });
  loadPanel();
});

onUnmounted(() => {
  document.removeEventListener("click", () => {});
});
</script>

<style scoped>
.arrangement-panel {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #1e1e1e;
  border-radius: 4px;
  overflow: hidden;
  outline: none;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #2a2a2a;
  border-bottom: 1px solid #444;
  flex-wrap: wrap;
  gap: 12px;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  color: #fff;
}

.header-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.grid-selector {
  display: flex;
  align-items: center;
  gap: 6px;
}

.grid-selector label {
  color: #ccc;
  font-size: 12px;
}

.grid-selector select {
  padding: 4px 8px;
  background: #333;
  color: #fff;
  border: 1px solid #555;
  border-radius: 4px;
  font-size: 12px;
}

.zoom-controls {
  display: flex;
  align-items: center;
  gap: 6px;
}

.zoom-controls button {
  width: 24px;
  height: 24px;
  padding: 0;
  background: #4a4a4a;
  color: #fff;
  border: 1px solid #555;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.zoom-controls button:hover {
  background: #5a5a5a;
}

.zoom-controls span {
  color: #ccc;
  font-size: 12px;
  min-width: 40px;
  text-align: center;
}

.refresh-btn {
  padding: 6px 12px;
  background: #4a4a4a;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 12px;
}

.refresh-btn:hover {
  background: #5a5a5a;
}

.loading,
.empty {
  padding: 40px;
  text-align: center;
  color: #666;
  font-size: 14px;
}

.lanes-container {
  flex: 1;
  overflow-y: auto;
  overflow-x: auto;
  padding: 16px;
}

.lane {
  margin-bottom: 24px;
  background: #2a2a2a;
  border-radius: 4px;
  overflow: hidden;
}

.lane-header {
  padding: 8px 12px;
  background: #333;
  border-bottom: 1px solid #444;
}

.lane-name {
  font-weight: bold;
  color: #fff;
  font-size: 14px;
  text-transform: capitalize;
}

.lane-content {
  position: relative;
  min-height: 80px;
  height: 80px;
  background: #1e1e1e;
  border: 1px solid #444;
  border-radius: 4px;
  overflow-x: auto;
  overflow-y: hidden;
}

.empty-space-indicator {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  pointer-events: none;
}

.empty-space-hint {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  color: #666;
  font-size: 12px;
  opacity: 0;
  transition: opacity 0.2s;
  pointer-events: none;
}

.lane-content:hover .empty-space-hint {
  opacity: 0.6;
}

.lane-content:hover {
  background: #222;
}

.empty-space-indicator {
  pointer-events: auto;
  cursor: pointer;
  z-index: 0;
}

.grid-lines {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 1;
}

.grid-line {
  position: absolute;
  top: 0;
  width: 1px;
  height: 100%;
  background: rgba(255, 255, 255, 0.1);
}

.grid-line-strong {
  background: rgba(255, 255, 255, 0.2);
  width: 2px;
}

.context-menu {
  position: fixed;
  background: #2a2a2a;
  border: 1px solid #555;
  border-radius: 4px;
  padding: 4px 0;
  z-index: 1000;
  min-width: 150px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
}

.context-menu-item {
  padding: 8px 16px;
  color: #fff;
  cursor: pointer;
  font-size: 13px;
}

.context-menu-item:hover {
  background: #3a3a3a;
}

.context-menu-divider {
  height: 1px;
  background: #444;
  margin: 4px 0;
}
</style>
