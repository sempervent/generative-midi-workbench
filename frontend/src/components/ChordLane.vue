<template>
  <div class="chord-lane" ref="containerRef">
    <div class="lane-header">
      <span>Chords</span>
    </div>
    <div class="lane-content" :style="laneStyle" ref="contentRef">
      <div
        v-for="chord in chords"
        :key="chord.id"
        class="chord-block"
        :class="{ disabled: !chord.is_enabled, locked: chord.is_locked }"
        :style="getChordStyle(chord)"
        @click="handleChordClick(chord)"
      >
        <div class="chord-label">{{ chord.chord_name }}</div>
        <div class="chord-roman">{{ chord.roman_numeral }}</div>
      </div>
      <div v-if="chords.length === 0" class="empty">
        No chords in this range
      </div>
      <div v-if="showDiagnosticsOverlay" class="diagnostics">
        <div>Chords: {{ chords.length }}</div>
        <div>Ticks/Bar: {{ ticksPerBar(props.timeSignatureNum, props.timeSignatureDen) }}</div>
        <div>Total Bars: {{ totalBars }}</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from "vue";
import { clipLocalToProjectTicks, ticksPerBar, validateTick } from "../music/timing";
import type { Arrangement, ChordEvent } from "../types";

const props = defineProps<{
  arrangement: Arrangement | null;
  bpm: number;
  timeSignatureNum: number;
  timeSignatureDen: number;
}>();

const emit = defineEmits<(e: "chord-click", chord: ChordEvent) => void>();

const containerRef = ref<HTMLElement | null>(null);
const contentRef = ref<HTMLElement | null>(null);
const showDiagnostics = ref(false);

// Computed property for diagnostics overlay (only in dev mode)
const showDiagnosticsOverlay = computed(() => {
  return import.meta.env.DEV && showDiagnostics.value;
});

// Calculate total bars
const totalBars = computed(() => {
  if (!props.arrangement) return 1;
  let maxBar = props.arrangement.bars;
  for (const track of props.arrangement.tracks) {
    for (const clip of track.clips) {
      const clipEndBar = clip.start_bar + clip.length_bars;
      if (clipEndBar > maxBar) maxBar = clipEndBar;
    }
  }
  return maxBar;
});

// Extract all chords from arrangement
const chords = computed(() => {
  if (!props.arrangement) return [];
  const allChords: ChordEvent[] = [];
  const tpb = ticksPerBar(props.timeSignatureNum, props.timeSignatureDen);

  for (const track of props.arrangement.tracks) {
    if (track.role === "chords") {
      for (const clip of track.clips) {
        for (const chord of clip.chord_events) {
          if (!chord.is_enabled) continue;
          // Calculate absolute position with offsets
          const absoluteStartTick = clipLocalToProjectTicks(
            chord.start_tick,
            clip.start_bar,
            clip.start_offset_ticks || 0,
            track.start_offset_ticks || 0,
            props.timeSignatureNum,
            props.timeSignatureDen
          );
          allChords.push({
            ...chord,
            start_tick: validateTick(absoluteStartTick, `chord ${chord.id}`),
          });
        }
      }
    }
  }
  return allChords.sort((a, b) => a.start_tick - b.start_tick);
});

const laneStyle = computed(() => {
  // Calculate total width based on project length
  if (!props.arrangement) return { width: "100%", minWidth: "100%" };
  const tpb = ticksPerBar(props.timeSignatureNum, props.timeSignatureDen);
  const totalTicks = totalBars.value * tpb;
  const containerWidth = containerRef.value?.clientWidth || 800;
  const pixelsPerTick = 1;
  const calculatedWidth = Math.max(totalTicks * pixelsPerTick, containerWidth);

  return {
    width: `${calculatedWidth}px`,
    minWidth: "100%",
  };
});

function getChordStyle(chord: ChordEvent) {
  const tpb = ticksPerBar(props.timeSignatureNum, props.timeSignatureDen);
  const containerWidth = containerRef.value?.clientWidth || 800;

  // Calculate total project length
  let maxBar = props.arrangement?.bars || 1;
  if (props.arrangement) {
    for (const track of props.arrangement.tracks) {
      for (const clip of track.clips) {
        const clipEndBar = clip.start_bar + clip.length_bars;
        if (clipEndBar > maxBar) maxBar = clipEndBar;
      }
    }
  }
  const totalTicks = maxBar * tpb;
  const pixelsPerTick = containerWidth / totalTicks;

  const left = validateTick(chord.start_tick * pixelsPerTick, `chord ${chord.id} left`);
  const width = validateTick(chord.duration_tick * pixelsPerTick, `chord ${chord.id} width`);

  // Color based on intensity
  const intensity = chord.intensity || 0.85;
  const hue = 200; // Blue-green
  const saturation = Math.min(100, intensity * 100);
  const lightness = 50 + intensity * 20;

  return {
    left: `${left}px`,
    width: `${Math.max(width, 4)}px`,
    backgroundColor: `hsl(${hue}, ${saturation}%, ${lightness}%)`,
    opacity: chord.is_enabled ? 1 : 0.5,
  };
}

function handleChordClick(chord: ChordEvent) {
  if (chord.is_locked) return;
  emit("chord-click", chord);
}

// ResizeObserver to handle container size changes
let resizeObserver: ResizeObserver | null = null;

onMounted(() => {
  if (containerRef.value && window.ResizeObserver) {
    resizeObserver = new ResizeObserver(() => {
      // Force recomputation of styles
      void laneStyle.value;
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
.chord-lane {
  width: 100%;
  margin-bottom: 20px;
}

.lane-header {
  padding: 8px 12px;
  background: #2a2a2a;
  border-bottom: 1px solid #444;
  font-weight: bold;
  color: #fff;
}

.lane-content {
  position: relative;
  min-height: 60px;
  height: 60px;
  background: #1e1e1e;
  border: 1px solid #444;
  border-radius: 4px;
  overflow-x: auto;
  overflow-y: hidden;
}

.chord-block {
  position: absolute;
  top: 0;
  height: 100%;
  min-height: 60px;
  border: 2px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 4px;
  box-sizing: border-box;
}

.chord-block:hover {
  border-color: rgba(255, 255, 255, 0.6);
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3);
}

.chord-block.disabled {
  opacity: 0.3;
  cursor: not-allowed;
}

.chord-block.locked {
  border-style: dashed;
  cursor: default;
}

.chord-label {
  font-size: 14px;
  font-weight: bold;
  color: #fff;
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
}

.chord-roman {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.8);
  text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.5);
}

.empty {
  text-align: center;
  color: #666;
  padding: 20px;
  font-size: 14px;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 100%;
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

