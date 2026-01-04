<template>
  <div
    ref="cardRef"
    class="arrangement-card"
    :class="{
      muted: segment.mute,
      selected: isSelected,
      active: isActive,
      dragging: isDragging,
      resizing: isResizing,
    }"
    :style="cardStyle"
    @mousedown="handleMouseDown"
    @click.stop="handleClick"
    @contextmenu.prevent="handleContextMenu"
  >
    <!-- Resize handles -->
    <div
      class="resize-handle resize-handle-left"
      @mousedown.stop="handleResizeStart('left', $event)"
    ></div>
    <div
      class="resize-handle resize-handle-right"
      @mousedown.stop="handleResizeStart('right', $event)"
    ></div>

    <!-- Ghost outline when dragging -->
    <div
      v-if="isDragging && dragState"
      class="ghost-outline"
      :style="ghostStyle"
    ></div>

    <!-- Card content -->
    <div class="card-content">
      <div class="card-title">{{ segment.name || segment.kind }}</div>
      <div class="card-badges">
        <span class="badge">{{ segment.length_bars }} bars</span>
        <span
          class="badge intensity"
          @mousedown.stop="handleIntensityDragStart"
        >
          Intensity: {{ segment.intensity.toFixed(2) }}
        </span>
        <span v-if="segment.chord_count !== undefined" class="badge">
          {{ segment.chord_count }} chords
        </span>
        <span v-if="segment.lane_count !== undefined" class="badge">
          {{ segment.lane_count }} lanes
        </span>
      </div>
      <div v-if="segment.chord_summary" class="card-summary">
        {{ segment.chord_summary }}
      </div>
      <div v-if="segment.lane_summary" class="card-summary">
        {{ segment.lane_summary }}
      </div>
    </div>

    <!-- Quick toggles on hover -->
    <div class="quick-toggles">
      <button
        class="toggle-btn"
        :class="{ active: segment.mute }"
        @click.stop="toggleMute"
        title="Mute"
      >
        🔇
      </button>
      <button
        class="toggle-btn"
        :class="{ active: segment.is_soloed }"
        @click.stop="toggleSolo"
        title="Solo"
      >
        🎯
      </button>
      <button
        class="toggle-btn"
        @click.stop="duplicate"
        title="Duplicate (Cmd+D)"
      >
        📋
      </button>
    </div>

    <!-- Tooltip -->
    <div v-if="tooltipText" class="tooltip">{{ tooltipText }}</div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import type { ArrangementSegment } from "../types";

const props = defineProps<{
  segment: ArrangementSegment;
  pixelsPerBar: number;
  isSelected?: boolean;
  isActive?: boolean;
  snapToGrid: (value: number, fine?: boolean) => number;
}>();

const emit = defineEmits<{
  (e: "click", segment: ArrangementSegment, shift: boolean): void;
  (e: "drag-start", segment: ArrangementSegment): void;
  (e: "drag", segment: ArrangementSegment, newStartBar: number): void;
  (e: "drag-end", segment: ArrangementSegment, newStartBar: number): void;
  (e: "resize-start", segment: ArrangementSegment, side: "left" | "right"): void;
  (e: "resize", segment: ArrangementSegment, newStartBar: number, newLengthBars: number): void;
  (e: "resize-end", segment: ArrangementSegment, newStartBar: number, newLengthBars: number): void;
  (e: "intensity-change", segment: ArrangementSegment, newIntensity: number): void;
  (e: "duplicate", segment: ArrangementSegment): void;
  (e: "mute-toggle", segment: ArrangementSegment): void;
  (e: "solo-toggle", segment: ArrangementSegment): void;
  (e: "context-menu", segment: ArrangementSegment, event: MouseEvent): void;
}>();

const cardRef = ref<HTMLElement | null>(null);
const isDragging = ref(false);
const isResizing = ref(false);
const tooltipText = ref("");
const dragState = ref<{ x: number; snappedX: number; startBar: number } | null>(null);
const dragStartPos = ref<{ x: number; y: number } | null>(null);
const resizeState = ref<{
  side: "left" | "right";
  startX: number;
  startStartBar: number;
  startLengthBars: number;
} | null>(null);

const cardStyle = computed(() => {
  let left = props.segment.start_bar * props.pixelsPerBar;
  let width = props.segment.length_bars * props.pixelsPerBar;

  // Apply drag/resize transforms
  if (dragState.value) {
    left = dragState.value.snappedX;
  }
  if (resizeState.value) {
    if (resizeState.value.side === "left") {
      const deltaX =
        resizeState.value.startX -
        (resizeState.value.startX - (left - resizeState.value.startStartBar * props.pixelsPerBar));
      const deltaBars = -deltaX / props.pixelsPerBar;
      const newStartBar = props.snapToGrid(resizeState.value.startStartBar + deltaBars);
      const newLengthBars =
        resizeState.value.startLengthBars - (newStartBar - resizeState.value.startStartBar);
      left = newStartBar * props.pixelsPerBar;
      width = Math.max(props.pixelsPerBar / 4, newLengthBars * props.pixelsPerBar);
    } else {
      const deltaX =
        resizeState.value.startX -
        left -
        (resizeState.value.startX - resizeState.value.startStartBar * props.pixelsPerBar);
      const deltaBars = deltaX / props.pixelsPerBar;
      width = Math.max(
        props.pixelsPerBar / 4,
        (resizeState.value.startLengthBars + deltaBars) * props.pixelsPerBar
      );
    }
  }

  const opacity = props.segment.mute ? 0.5 : Math.min(1.0, 0.7 + props.segment.intensity * 0.3);
  const borderThickness = Math.max(1, Math.round(props.segment.intensity * 3));
  const saturation = Math.min(100, props.segment.intensity * 100);

  return {
    left: `${left}px`,
    width: `${Math.max(width, 40)}px`,
    opacity: `${opacity}`,
    borderWidth: `${borderThickness}px`,
    filter: `saturate(${saturation}%)`,
    transition: isDragging.value || isResizing.value ? "none" : "all 0.15s ease-out",
  };
});

const ghostStyle = computed(() => {
  if (!dragState.value) return {};
  return {
    left: `${dragState.value.snappedX}px`,
    width: `${props.segment.length_bars * props.pixelsPerBar}px`,
  };
});

function handleMouseDown(event: MouseEvent) {
  if (event.button !== 0) return; // Only left click
  if (event.altKey) {
    // Alt-drag = duplicate
    event.preventDefault();
    emit("duplicate", props.segment);
    return;
  }

  // Record initial mouse position for click detection
  dragStartPos.value = { x: event.clientX, y: event.clientY };

  const fine = event.shiftKey;
  const startX = event.clientX;
  const startBar = props.segment.start_bar;

  isDragging.value = true;
  dragState.value = {
    x: startX,
    snappedX: props.segment.start_bar * props.pixelsPerBar,
    startBar,
  };

  emit("drag-start", props.segment);

  const handleMove = (e: MouseEvent) => {
    if (!dragState.value) return;
    const deltaX = e.clientX - startX;
    const deltaBars = deltaX / props.pixelsPerBar;
    const newBar = props.snapToGrid(startBar + deltaBars, fine);
    dragState.value.x = e.clientX;
    dragState.value.snappedX = newBar * props.pixelsPerBar;
    tooltipText.value = `Start: bar ${newBar.toFixed(2)}`;
    emit("drag", props.segment, newBar);
  };

  const handleEnd = () => {
    if (!dragState.value) return;
    const finalBar = dragState.value.snappedX / props.pixelsPerBar;
    if (Math.abs(finalBar - props.segment.start_bar) > 0.01) {
      emit("drag-end", props.segment, finalBar);
    }
    isDragging.value = false;
    dragState.value = null;
    dragStartPos.value = null;
    tooltipText.value = "";
  };

  document.addEventListener("mousemove", handleMove);
  document.addEventListener("mouseup", handleEnd, { once: true });
}

function handleResizeStart(side: "left" | "right", event: MouseEvent) {
  event.stopPropagation();
  isResizing.value = true;
  resizeState.value = {
    side,
    startX: event.clientX,
    startStartBar: props.segment.start_bar,
    startLengthBars: props.segment.length_bars,
  };

  const handleMove = (e: MouseEvent) => {
    if (!resizeState.value) return;
    const deltaX = e.clientX - resizeState.value.startX;
    const deltaBars = deltaX / props.pixelsPerBar;

    if (side === "left") {
      const newStartBar = props.snapToGrid(resizeState.value.startStartBar - deltaBars);
      const newLengthBars =
        resizeState.value.startLengthBars + (resizeState.value.startStartBar - newStartBar);
      tooltipText.value = `Length: ${Math.max(0.25, newLengthBars).toFixed(2)} bars`;
      emit("resize", props.segment, newStartBar, Math.max(0.25, newLengthBars));
    } else {
      const newLengthBars = props.snapToGrid(resizeState.value.startLengthBars + deltaBars);
      tooltipText.value = `Length: ${Math.max(0.25, newLengthBars).toFixed(2)} bars`;
      emit("resize", props.segment, props.segment.start_bar, Math.max(0.25, newLengthBars));
    }
  };

  const handleEnd = () => {
    if (!resizeState.value) return;
    const deltaX =
      resizeState.value.startX -
      (resizeState.value.startX -
        (props.segment.start_bar * props.pixelsPerBar -
          resizeState.value.startStartBar * props.pixelsPerBar));
    const deltaBars = -deltaX / props.pixelsPerBar;

    if (side === "left") {
      const newStartBar = props.snapToGrid(resizeState.value.startStartBar - deltaBars);
      const newLengthBars = Math.max(
        0.25,
        resizeState.value.startLengthBars + (resizeState.value.startStartBar - newStartBar)
      );
      emit("resize-end", props.segment, newStartBar, newLengthBars);
    } else {
      const newLengthBars = Math.max(
        0.25,
        props.snapToGrid(resizeState.value.startLengthBars + deltaBars)
      );
      emit("resize-end", props.segment, props.segment.start_bar, newLengthBars);
    }

    isResizing.value = false;
    resizeState.value = null;
    tooltipText.value = "";
  };

  document.addEventListener("mousemove", handleMove);
  document.addEventListener("mouseup", handleEnd, { once: true });
}

function handleClick(event: MouseEvent) {
  // Don't emit click if this was a drag (mouse moved significantly)
  if (dragStartPos) {
    const deltaX = Math.abs(event.clientX - dragStartPos.x);
    const deltaY = Math.abs(event.clientY - dragStartPos.y);
    if (deltaX > 5 || deltaY > 5) {
      // This was a drag, not a click
      return;
    }
  }
  emit("click", props.segment, event.shiftKey);
}

function handleContextMenu(event: MouseEvent) {
  emit("context-menu", props.segment, event);
}

function handleIntensityDragStart(event: MouseEvent) {
  event.stopPropagation();
  const startY = event.clientY;
  const startIntensity = props.segment.intensity;
  const fine = event.shiftKey;

  const handleMove = (e: MouseEvent) => {
    const deltaY = startY - e.clientY;
    const deltaIntensity = (deltaY / 100) * (fine ? 0.01 : 0.05);
    const newIntensity = Math.max(0, Math.min(2, startIntensity + deltaIntensity));
    tooltipText.value = `Intensity: ${newIntensity.toFixed(2)}`;
    emit("intensity-change", props.segment, newIntensity);
  };

  const handleEnd = () => {
    tooltipText.value = "";
    document.removeEventListener("mousemove", handleMove);
    document.removeEventListener("mouseup", handleEnd);
  };

  document.addEventListener("mousemove", handleMove);
  document.addEventListener("mouseup", handleEnd, { once: true });
}

function toggleMute() {
  emit("mute-toggle", props.segment);
}

function toggleSolo() {
  emit("solo-toggle", props.segment);
}

function duplicate() {
  emit("duplicate", props.segment);
}
</script>

<style scoped>
.arrangement-card {
  position: absolute;
  top: 0;
  height: 100%;
  min-width: 40px;
  background: #4a4a4a;
  border: 2px solid rgba(255, 255, 255, 0.5);
  border-radius: 4px;
  cursor: move;
  padding: 4px 8px;
  box-sizing: border-box;
  overflow: hidden;
  user-select: none;
  z-index: 10;
}

.arrangement-card:hover {
  border-color: rgba(255, 255, 255, 0.9);
  z-index: 10;
  box-shadow: 0 2px 8px rgba(255, 255, 255, 0.2);
  transform: translateY(-1px);
  transition: all 0.15s ease-out;
}

.arrangement-card.selected {
  border-color: #4a9eff;
  box-shadow: 0 0 0 2px rgba(74, 158, 255, 0.3);
}

.arrangement-card.active {
  border-color: #4a9eff;
  box-shadow: 0 0 0 3px rgba(74, 158, 255, 0.5), 0 0 20px rgba(74, 158, 255, 0.3);
  z-index: 100;
}

.arrangement-card.dragging {
  opacity: 0.7;
  cursor: grabbing;
}

.arrangement-card.resizing {
  cursor: ew-resize;
}

.arrangement-card.resizing .card-content {
  background-image: repeating-linear-gradient(
    45deg,
    transparent,
    transparent 4px,
    rgba(255, 255, 255, 0.1) 4px,
    rgba(255, 255, 255, 0.1) 8px
  );
}

.arrangement-card.muted {
  opacity: 0.3;
}

.resize-handle {
  position: absolute;
  top: 0;
  width: 8px;
  height: 100%;
  cursor: ew-resize;
  z-index: 20;
}

.resize-handle-left {
  left: 0;
}

.resize-handle-right {
  right: 0;
}

.resize-handle:hover {
  background: rgba(255, 255, 255, 0.2);
}

.ghost-outline {
  position: absolute;
  top: 0;
  height: 100%;
  border: 2px dashed rgba(255, 255, 255, 0.6);
  border-radius: 4px;
  pointer-events: none;
  z-index: 5;
}

.card-content {
  display: flex;
  flex-direction: column;
  gap: 4px;
  height: 100%;
}

.card-title {
  font-weight: bold;
  font-size: 12px;
  color: #fff;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.card-badges {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.badge {
  font-size: 10px;
  padding: 2px 6px;
  background: rgba(0, 0, 0, 0.3);
  border-radius: 3px;
  color: #ccc;
  cursor: default;
}

.badge.intensity {
  background: rgba(100, 150, 255, 0.3);
  cursor: ns-resize;
}

.badge.intensity:hover {
  background: rgba(100, 150, 255, 0.5);
}

.card-summary {
  font-size: 10px;
  color: #aaa;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: auto;
}

.quick-toggles {
  position: absolute;
  top: 4px;
  right: 4px;
  display: flex;
  gap: 4px;
  z-index: 30;
  opacity: 0;
  transition: opacity 0.15s ease-out;
  pointer-events: none;
}

.arrangement-card:hover .quick-toggles {
  opacity: 1;
  pointer-events: auto;
}

.toggle-btn {
  width: 20px;
  height: 20px;
  padding: 0;
  background: rgba(0, 0, 0, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 3px;
  cursor: pointer;
  font-size: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.toggle-btn:hover {
  background: rgba(0, 0, 0, 0.8);
  border-color: rgba(255, 255, 255, 0.6);
}

.toggle-btn.active {
  background: rgba(255, 100, 100, 0.6);
}

.tooltip {
  position: absolute;
  bottom: -24px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.9);
  color: #fff;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  white-space: nowrap;
  z-index: 100;
  pointer-events: none;
}
</style>
