<template>
  <div class="piano-roll" ref="containerRef">
    <div class="piano-roll-content">
      <div class="grid" :style="gridStyle" ref="gridRef">
        <div
          v-for="event in visualEvents"
          :key="event.id"
          class="note-block"
          :class="{ 'is-chord': event.kind === 'chord' }"
          :style="getEventStyle(event)"
        />
      </div>
      <div v-if="showDiagnosticsOverlay" class="diagnostics">
        <div>Events: {{ visualEvents.length }}</div>
        <div>Ticks/Bar: {{ ticksPerBarValue }}</div>
        <div>Total Bars: {{ totalBars }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { ticksPerBar } from "../music/timing";
import { notesToVisualEvents } from "../music/visualEvents";
import type { TrackInArrangement } from "../types";

const props = defineProps<{
  track: TrackInArrangement;
  bpm: number;
  timeSignatureNum: number;
  timeSignatureDen: number;
}>();

const containerRef = ref<HTMLElement | null>(null);
const gridRef = ref<HTMLElement | null>(null);
const showDiagnostics = ref(false);

// Computed property for diagnostics overlay (only in dev mode)
const showDiagnosticsOverlay = computed(() => {
  return import.meta.env.DEV && showDiagnostics.value;
});

// Use provided time signature
const timeSigNum = computed(() => props.timeSignatureNum);
const timeSigDen = computed(() => props.timeSignatureDen);
const ticksPerBarValue = computed(() => ticksPerBar(timeSigNum.value, timeSigDen.value));

// Calculate total project length in bars from clips
const totalBars = computed(() => {
  let maxBar = 1;
  for (const clip of props.track.clips) {
    const clipEndBar = clip.start_bar + clip.length_bars;
    if (clipEndBar > maxBar) {
      maxBar = clipEndBar;
    }
  }
  return maxBar;
});

// Convert all notes to visual events with proper timing
const visualEvents = computed(() => {
  const events: ReturnType<typeof notesToVisualEvents> = [];
  for (const clip of props.track.clips) {
    const clipEvents = notesToVisualEvents(
      clip.notes,
      clip.start_bar,
      clip.start_offset_ticks || 0,
      props.track.start_offset_ticks || 0,
      timeSigNum.value,
      timeSigDen.value
    );
    events.push(...clipEvents);
  }
  return events.sort((a, b) => a.startTick - b.startTick);
});

const gridStyle = computed(() => {
  // Calculate width based on total bars
  const totalTicks = totalBars.value * ticksPerBarValue.value;
  const pixelsPerTick = 1; // Base scale
  const minWidth = containerRef.value?.clientWidth || 800;
  const calculatedWidth = Math.max(totalTicks * pixelsPerTick, minWidth);

  return {
    minHeight: "200px",
    height: "200px",
    position: "relative",
    width: `${calculatedWidth}px`,
    minWidth: "100%",
  };
});

function getEventStyle(event: ReturnType<typeof notesToVisualEvents>[0]) {
  if (visualEvents.value.length === 0) {
    return { display: "none" };
  }

  // Calculate pitch range for vertical positioning (only for notes)
  const noteEvents = visualEvents.value.filter((e) => e.kind === "note" && e.pitch !== undefined);
  const pitches = noteEvents.map((e) => e.pitch as number);
  const minPitch = pitches.length > 0 ? Math.min(...pitches) : 60;
  const maxPitch = pitches.length > 0 ? Math.max(...pitches) : 84;
  const pitchRange = maxPitch - minPitch || 24;

  // Calculate position
  const totalTicks = totalBars.value * ticksPerBarValue.value;
  const containerWidth = containerRef.value?.clientWidth || 800;
  const pixelsPerTick = containerWidth / totalTicks;

  const left = event.startTick * pixelsPerTick;
  const width = event.durationTick * pixelsPerTick;

  // For chords, use full height; for notes, use pitch-based positioning
  const style: Record<string, string> = {
    left: `${left}px`,
    width: `${Math.max(width, 2)}px`,
    position: "absolute",
    borderRadius: "2px",
  };

  if (event.kind === "chord") {
    style.top = "0";
    style.height = "100%";
    style.backgroundColor = `hsl(200, ${(event.intensity || 0.85) * 100}%, ${50 + (event.intensity || 0.85) * 20}%)`;
    style.border = "2px solid rgba(255, 255, 255, 0.3)";
  } else {
    const bottom = event.pitch !== undefined ? ((event.pitch - minPitch) / pitchRange) * 100 : 50;
    style.bottom = `${bottom}%`;
    style.height = "8px";
    style.background = props.track.role === "drums" ? "#ff6b6b" : "#4ecdc4";
  }

  return style;
}

// ResizeObserver to handle container size changes
let resizeObserver: ResizeObserver | null = null;

onMounted(() => {
  if (containerRef.value && window.ResizeObserver) {
    resizeObserver = new ResizeObserver(() => {
      // Force recomputation of styles
      if (gridRef.value) {
        // Trigger reactivity by accessing computed
        void gridStyle.value;
      }
    });
    resizeObserver.observe(containerRef.value);
  }

  // Toggle diagnostics with Ctrl+Shift+D
  const handleKeydown = (e: KeyboardEvent) => {
    if (e.ctrlKey && e.shiftKey && e.key === "D") {
      showDiagnostics.value = !showDiagnostics.value;
    }
  };
  window.addEventListener("keydown", handleKeydown);
  onUnmounted(() => {
    window.removeEventListener("keydown", handleKeydown);
  });
});

onUnmounted(() => {
  if (resizeObserver) {
    resizeObserver.disconnect();
  }
});
</script>

<style scoped>
.piano-roll {
  width: 100%;
  overflow-x: auto;
  overflow-y: hidden;
  flex: 1;
  min-height: 200px;
}

.piano-roll-content {
  min-width: 100%;
  position: relative;
  height: 100%;
}

.grid {
  background: #333;
  border: 1px solid #555;
  border-radius: 4px;
  position: relative;
  overflow: visible;
}

.note-block {
  cursor: pointer;
  transition: opacity 0.2s;
  z-index: 1;
}

.note-block:hover {
  opacity: 0.7;
  z-index: 2;
}

.note-block.is-chord {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 4px;
  box-sizing: border-box;
}

.diagnostics {
  position: absolute;
  top: 4px;
  right: 4px;
  background: rgba(0, 0, 0, 0.8);
  color: #fff;
  padding: 8px;
  font-size: 11px;
  font-family: monospace;
  border-radius: 4px;
  z-index: 1000;
  pointer-events: none;
}

.diagnostics div {
  margin: 2px 0;
}
</style>

