<template>
  <div class="piano-roll">
    <div class="piano-roll-content">
      <div class="grid" :style="gridStyle">
        <div
          v-for="note in notes"
          :key="note.id"
          class="note-block"
          :style="getNoteStyle(note)"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { TrackInArrangement } from "../types";

const props = defineProps<{
  track: TrackInArrangement;
  bpm: number;
}>();

const notes = computed(() => {
  const allNotes: Array<{ id: string; pitch: number; start_tick: number; duration_tick: number }> =
    [];
  for (const clip of props.track.clips) {
    for (const note of clip.notes) {
      allNotes.push({
        ...note,
        start_tick: clip.start_bar * 1920 + note.start_tick, // Approximate ticks per bar
      });
    }
  }
  return allNotes.sort((a, b) => a.start_tick - b.start_tick);
});

const gridStyle = computed(() => {
  // Simple grid visualization
  return {
    minHeight: "200px",
    position: "relative",
  };
});

function getNoteStyle(note: { pitch: number; start_tick: number; duration_tick: number }) {
  const minPitch = Math.min(...notes.value.map((n) => n.pitch), 60);
  const maxPitch = Math.max(...notes.value.map((n) => n.pitch), 84);
  const pitchRange = maxPitch - minPitch || 24;

  const left = (note.start_tick / 1920) * 100; // Simplified: assuming 4/4, 480 PPQ
  const width = (note.duration_tick / 1920) * 100;
  const bottom = ((note.pitch - minPitch) / pitchRange) * 100;

  return {
    left: `${left}%`,
    width: `${Math.max(width, 0.5)}%`,
    bottom: `${bottom}%`,
    height: "8px",
    background: props.track.role === "drums" ? "#ff6b6b" : "#4ecdc4",
    position: "absolute",
    borderRadius: "2px",
  };
}
</script>

<style scoped>
.piano-roll {
  width: 100%;
  overflow-x: auto;
}

.piano-roll-content {
  min-width: 100%;
}

.grid {
  background: #333;
  border: 1px solid #555;
  border-radius: 4px;
  min-height: 200px;
  position: relative;
}

.note-block {
  cursor: pointer;
  transition: opacity 0.2s;
}

.note-block:hover {
  opacity: 0.7;
}
</style>

