<template>
  <div class="chord-timeline">
    <div
      v-for="chord in chords"
      :key="chord.id"
      class="chord-item"
    >
      <div class="roman">{{ chord.roman_numeral }}</div>
      <div class="name">{{ chord.chord_name }}</div>
    </div>
    <div v-if="chords.length === 0" class="empty">
      No chords generated yet
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { Arrangement } from "../types";

const props = defineProps<{
  arrangement: Arrangement | null;
}>();

const chords = computed(() => {
  if (!props.arrangement) return [];
  const allChords: Array<{ id: string; roman_numeral: string; chord_name: string }> = [];
  for (const track of props.arrangement.tracks) {
    if (track.role === "chords") {
      for (const clip of track.clips) {
        for (const chord of clip.chord_events) {
          allChords.push(chord);
        }
      }
    }
  }
  return allChords;
});
</script>

<style scoped>
.chord-timeline {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.chord-item {
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 4px;
  padding: 12px;
}

.roman {
  font-size: 18px;
  font-weight: bold;
  color: #4ecdc4;
  margin-bottom: 4px;
}

.name {
  font-size: 14px;
  color: #aaa;
}

.empty {
  text-align: center;
  color: #666;
  padding: 20px;
  font-size: 14px;
}
</style>

