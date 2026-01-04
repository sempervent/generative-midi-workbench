<template>
  <div class="chord-timeline">
    <div class="timeline-header">
      <h4>Chord Timeline</h4>
      <button class="add-btn" @click="handleAddChord" title="Add chord">+</button>
    </div>
    <div class="timeline-content">
      <div
        v-for="chord in sortedChords"
        :key="chord.id"
        class="timeline-item"
      >
        <ChordCard
          :chord="chord"
          :beats-per-bar="beatsPerBar"
          @update="handleChordUpdate"
          @delete="handleChordDelete"
        />
      </div>
      <div v-if="sortedChords.length === 0" class="empty">
        No chords generated yet. Click "Generate Chords" to create a progression.
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { Arrangement, ChordEvent } from "../types";
import ChordCard from "./ChordCard.vue";

const props = defineProps<{
  arrangement: Arrangement | null;
}>();

const emit = defineEmits<(e: "chord-updated") => void>();

const beatsPerBar = computed(() => {
  if (!props.arrangement) return 4;
  return (props.arrangement.time_signature_num * 4) / props.arrangement.time_signature_den;
});

const sortedChords = computed(() => {
  if (!props.arrangement) return [];
  const allChords: ChordEvent[] = [];
  const PPQ = 480;
  const quarterNotesPerBar = beatsPerBar.value;
  const ticksPerBar = quarterNotesPerBar * PPQ;

  for (const track of props.arrangement.tracks) {
    if (track.role === "chords") {
      for (const clip of track.clips) {
        for (const chord of clip.chord_events) {
          // Calculate absolute start position for sorting
          const absoluteStartTick = clip.start_bar * ticksPerBar + chord.start_tick;
          allChords.push({
            ...chord,
            start_tick: absoluteStartTick,
          });
        }
      }
    }
  }
  return allChords.sort((a, b) => a.start_tick - b.start_tick);
});

function handleChordUpdate(chord: ChordEvent) {
  emit("chord-updated");
}

function handleChordDelete(chordId: string) {
  emit("chord-updated");
}

function handleAddChord() {
  // TODO: Open add chord dialog
  console.log("Add chord clicked");
}
</script>

<style scoped>
.chord-timeline {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px;
  border-bottom: 1px solid #444;
}

.timeline-header h4 {
  margin: 0;
  color: #fff;
  font-size: 16px;
}

.add-btn {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 1px solid #4ecdc4;
  background: #2a2a2a;
  color: #4ecdc4;
  cursor: pointer;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.2s;
}

.add-btn:hover {
  background: #4ecdc4;
  color: #000;
}

.timeline-content {
  flex: 1;
  overflow-y: auto;
  padding: 10px;
}

.timeline-item {
  margin-bottom: 10px;
}

.empty {
  text-align: center;
  color: #666;
  padding: 40px 20px;
  font-size: 14px;
}
</style>
