<template>
  <div
    class="chord-card"
    :class="{ disabled: !chord.is_enabled, locked: chord.is_locked }"
    :style="cardStyle"
    @mousedown="handleMouseDown"
  >
    <div class="chord-content">
      <div class="chord-header">
        <div class="roman">{{ chord.roman_numeral }}</div>
        <div class="name">{{ chord.chord_name }}</div>
      </div>
      <div class="chord-controls">
        <div class="control-row">
          <label>Intensity</label>
          <input
            type="range"
            :value="chord.intensity"
            min="0"
            max="1"
            step="0.01"
            @input="updateIntensity"
            :disabled="chord.is_locked"
          />
          <span class="value">{{ (chord.intensity * 100).toFixed(0) }}%</span>
        </div>
        <div class="control-row">
          <label>Voicing</label>
          <select :value="chord.voicing" @change="updateVoicing" :disabled="chord.is_locked">
            <option value="root">Root</option>
            <option value="open">Open</option>
            <option value="drop2">Drop 2</option>
            <option value="smooth">Smooth</option>
          </select>
        </div>
        <div class="control-row">
          <label>Strum</label>
          <input
            type="number"
            :value="chord.strum_ms"
            min="0"
            max="200"
            @input="updateStrum"
            :disabled="chord.is_locked"
          />
          <span>ms</span>
        </div>
        <div class="control-row">
          <label>Humanize</label>
          <input
            type="number"
            :value="chord.humanize_ms"
            min="0"
            max="50"
            @input="updateHumanize"
            :disabled="chord.is_locked"
          />
          <span>ms</span>
        </div>
      </div>
      <div class="chord-actions">
        <button
          class="toggle-btn"
          :class="{ active: chord.is_enabled }"
          @click="toggleEnabled"
          :disabled="chord.is_locked"
        >
          {{ chord.is_enabled ? "On" : "Off" }}
        </button>
        <button
          class="lock-btn"
          :class="{ active: chord.is_locked }"
          @click="toggleLock"
        >
          {{ chord.is_locked ? "🔒" : "🔓" }}
        </button>
      </div>
    </div>
    <div class="resize-handle" @mousedown.stop="handleResizeStart"></div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { chordsApi } from "../api/chords";
import type { ChordEvent } from "../types";

const props = defineProps<{
  chord: ChordEvent;
  beatsPerBar: number;
}>();

const emit = defineEmits<{
  (e: "update", chord: ChordEvent): void;
  (e: "delete", chordId: string): void;
}>();

const cardStyle = computed(() => {
  // Width based on duration_beats
  const widthPercent = (props.chord.duration_beats / props.beatsPerBar) * 100;
  return {
    width: `${Math.max(widthPercent, 5)}%`,
    minWidth: "80px",
  };
});

async function updateIntensity(e: Event) {
  const value = Number.parseFloat((e.target as HTMLInputElement).value);
  await updateChord({ intensity: value });
}

async function updateVoicing(e: Event) {
  const value = (e.target as HTMLSelectElement).value;
  await updateChord({ voicing: value });
}

async function updateStrum(e: Event) {
  const value = Number.parseInt((e.target as HTMLInputElement).value, 10);
  await updateChord({ strum_ms: value });
}

async function updateHumanize(e: Event) {
  const value = Number.parseInt((e.target as HTMLInputElement).value, 10);
  await updateChord({ humanize_ms: value });
}

async function toggleEnabled() {
  await updateChord({ is_enabled: !props.chord.is_enabled });
}

async function toggleLock() {
  await updateChord({ is_locked: !props.chord.is_locked });
}

async function updateChord(updates: Partial<ChordEvent>) {
  try {
    const updated = await chordsApi.update(props.chord.id, updates);
    emit("update", updated);
  } catch (error) {
    console.error("Failed to update chord:", error);
    alert("Failed to update chord");
  }
}

function handleMouseDown(e: MouseEvent) {
  // TODO: Implement drag to move
  if (props.chord.is_locked) return;
}

function handleResizeStart(e: MouseEvent) {
  // TODO: Implement resize
  if (props.chord.is_locked) return;
  e.stopPropagation();
}
</script>

<style scoped>
.chord-card {
  background: #2a2a2a;
  border: 2px solid #4ecdc4;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 10px;
  position: relative;
  transition: all 0.2s;
}

.chord-card:hover {
  border-color: #6ee7e0;
  box-shadow: 0 4px 8px rgba(78, 205, 196, 0.3);
}

.chord-card.disabled {
  opacity: 0.5;
  border-color: #666;
}

.chord-card.locked {
  border-style: dashed;
}

.chord-content {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.chord-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.roman {
  font-size: 20px;
  font-weight: bold;
  color: #4ecdc4;
}

.name {
  font-size: 16px;
  color: #aaa;
}

.chord-controls {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.control-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.control-row label {
  min-width: 70px;
  font-size: 12px;
  color: #bbb;
}

.control-row input[type="range"] {
  flex: 1;
}

.control-row input[type="number"] {
  width: 60px;
  padding: 4px;
  border-radius: 4px;
  border: 1px solid #444;
  background: #333;
  color: #fff;
}

.control-row select {
  flex: 1;
  padding: 4px;
  border-radius: 4px;
  border: 1px solid #444;
  background: #333;
  color: #fff;
}

.value {
  font-size: 12px;
  color: #aaa;
  min-width: 40px;
}

.chord-actions {
  display: flex;
  gap: 8px;
}

.toggle-btn,
.lock-btn {
  padding: 6px 12px;
  border-radius: 4px;
  border: 1px solid #444;
  background: #333;
  color: #fff;
  cursor: pointer;
  font-size: 12px;
  transition: all 0.2s;
}

.toggle-btn:hover,
.lock-btn:hover {
  background: #444;
}

.toggle-btn.active {
  background: #4ecdc4;
  color: #000;
}

.lock-btn.active {
  background: #ff6b6b;
}

.resize-handle {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 8px;
  cursor: ew-resize;
  background: rgba(78, 205, 196, 0.3);
  border-radius: 0 6px 6px 0;
}

.resize-handle:hover {
  background: rgba(78, 205, 196, 0.6);
}
</style>

