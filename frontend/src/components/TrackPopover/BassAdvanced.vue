<template>
  <div class="bass-advanced">
    <div class="control-group">
      <label>
        <input
          v-model="localFollowChords"
          type="checkbox"
          @change="updateFollowChords"
        />
        Follow Chords
      </label>
    </div>
    <div class="control-group">
      <label>Octave Range</label>
      <div class="range-inputs">
        <input
          v-model.number="localOctaveLow"
          type="number"
          min="2"
          max="5"
          @input="updateOctaveRange"
        />
        <span>to</span>
        <input
          v-model.number="localOctaveHigh"
          type="number"
          min="3"
          max="6"
          @input="updateOctaveRange"
        />
      </div>
    </div>
    <div class="control-group">
      <label>Movement</label>
      <select v-model="localMovement" @change="updateMovement">
        <option value="static">Static</option>
        <option value="walking">Walking</option>
        <option value="melodic">Melodic</option>
      </select>
    </div>
    <div class="control-group">
      <label>Rhythm Source</label>
      <select v-model="localRhythmSource" @change="updateRhythmSource">
        <option value="chords">Chords</option>
        <option value="drums">Drums</option>
        <option value="grid">Grid</option>
      </select>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import type { TrackPopoverContext } from "../TrackPopover.vue";

const props = defineProps<{
  context: TrackPopoverContext;
  params: Record<string, any>;
}>();

const emit = defineEmits<(e: "update:params", params: Record<string, any>) => void>();

const localFollowChords = ref(true);
const localOctaveLow = ref(3);
const localOctaveHigh = ref(4);
const localMovement = ref("walking");
const localRhythmSource = ref("chords");

function updateFollowChords() {
  emit("update:params", { follow_chords: localFollowChords.value });
}

function updateOctaveRange() {
  emit("update:params", {
    octave_low: localOctaveLow.value,
    octave_high: localOctaveHigh.value,
  });
}

function updateMovement() {
  emit("update:params", { movement: localMovement.value });
}

function updateRhythmSource() {
  emit("update:params", { rhythm_source: localRhythmSource.value });
}

watch(
  () => props.params,
  (newParams) => {
    localFollowChords.value = newParams.follow_chords ?? true;
    localOctaveLow.value = newParams.octave_low || 3;
    localOctaveHigh.value = newParams.octave_high || 4;
    localMovement.value = newParams.movement || "walking";
    localRhythmSource.value = newParams.rhythm_source || "chords";
  },
  { immediate: true }
);
</script>

<style scoped>
.bass-advanced {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.control-group {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.control-group label {
  font-size: 12px;
  color: #aaa;
}

.control-group select,
.control-group input[type="number"] {
  padding: 6px;
  background: #333;
  border: 1px solid #555;
  border-radius: 4px;
  color: #fff;
  font-size: 13px;
}

.range-inputs {
  display: flex;
  align-items: center;
  gap: 8px;
}

.range-inputs input {
  flex: 1;
}

.range-inputs span {
  color: #aaa;
  font-size: 12px;
}
</style>

