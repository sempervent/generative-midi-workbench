<template>
  <div class="circle-of-fifths">
    <div class="circle-container">
      <div
        v-for="(key, index) in keys"
        :key="key"
        class="key-button"
        :class="{ active: key === tonic }"
        :style="getKeyPosition(index)"
        @click="$emit('update:tonic', key)"
      >
        {{ key }}
      </div>
    </div>

    <div class="mode-selector">
      <button
        v-for="m in modes"
        :key="m"
        :class="{ active: m === mode }"
        @click="$emit('update:mode', m)"
      >
        {{ m }}
      </button>
    </div>

    <div class="quick-actions">
      <button @click="moveDominant">→ Dominant</button>
      <button @click="moveSubdominant">← Subdominant</button>
      <button @click="toggleRelative">Relative</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";

const props = defineProps<{
  tonic: string;
  mode: string;
}>();

const emit = defineEmits<{
  "update:tonic": [value: string];
  "update:mode": [value: string];
}>();

const keys = [
  "C",
  "G",
  "D",
  "A",
  "E",
  "B",
  "F#",
  "C#",
  "G#",
  "D#",
  "A#",
  "F",
  "Bb",
  "Eb",
  "Ab",
  "Db",
  "Gb",
];

const modes = ["ionian", "dorian", "phrygian", "lydian", "mixolydian", "aeolian", "locrian"];

function getKeyPosition(index: number) {
  const angle = (index / keys.length) * 2 * Math.PI - Math.PI / 2;
  const radius = 80;
  const x = Math.cos(angle) * radius;
  const y = Math.sin(angle) * radius;
  return {
    left: `calc(50% + ${x}px)`,
    top: `calc(50% + ${y}px)`,
  };
}

const circleOfFifths: Record<string, { dominant: string; subdominant: string }> = {
  C: { dominant: "G", subdominant: "F" },
  G: { dominant: "D", subdominant: "C" },
  D: { dominant: "A", subdominant: "G" },
  A: { dominant: "E", subdominant: "D" },
  E: { dominant: "B", subdominant: "A" },
  B: { dominant: "F#", subdominant: "E" },
  "F#": { dominant: "C#", subdominant: "B" },
  "C#": { dominant: "G#", subdominant: "F#" },
  "G#": { dominant: "D#", subdominant: "C#" },
  "D#": { dominant: "A#", subdominant: "G#" },
  "A#": { dominant: "F", subdominant: "D#" },
  F: { dominant: "C", subdominant: "Bb" },
  Bb: { dominant: "F", subdominant: "Eb" },
  Eb: { dominant: "Bb", subdominant: "Ab" },
  Ab: { dominant: "Eb", subdominant: "Db" },
  Db: { dominant: "Ab", subdominant: "Gb" },
  Gb: { dominant: "Db", subdominant: "Cb" },
};

function moveDominant() {
  const next = circleOfFifths[props.tonic]?.dominant;
  if (next) emit("update:tonic", next);
}

function moveSubdominant() {
  const next = circleOfFifths[props.tonic]?.subdominant;
  if (next) emit("update:tonic", next);
}

function toggleRelative() {
  if (props.mode === "ionian") {
    emit("update:mode", "aeolian");
  } else if (props.mode === "aeolian") {
    emit("update:mode", "ionian");
  }
}
</script>

<style scoped>
.circle-of-fifths {
  text-align: center;
}

.circle-container {
  position: relative;
  width: 200px;
  height: 200px;
  margin: 0 auto 20px;
}

.key-button {
  position: absolute;
  width: 30px;
  height: 30px;
  border-radius: 50%;
  background: #3a3a3a;
  border: 2px solid #555;
  color: #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  cursor: pointer;
  transform: translate(-50%, -50%);
  transition: all 0.2s;
}

.key-button:hover {
  background: #4a4a4a;
  border-color: #0066cc;
}

.key-button.active {
  background: #0066cc;
  border-color: #0088ff;
  color: #fff;
}

.mode-selector {
  display: flex;
  flex-wrap: wrap;
  gap: 5px;
  margin-bottom: 15px;
}

.mode-selector button {
  flex: 1;
  min-width: 70px;
  font-size: 11px;
  padding: 6px 8px;
}

.mode-selector button.active {
  background: #0066cc;
  border-color: #0088ff;
}

.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.quick-actions button {
  width: 100%;
  font-size: 12px;
  padding: 6px;
}
</style>

