<template>
  <Teleport to="body">
    <div v-if="isOpen" class="modal-overlay" @click="close">
      <div class="modal-content" @click.stop>
        <div class="modal-header">
          <h3>Edit Clip</h3>
          <button class="close-btn" @click="close">×</button>
        </div>
        <div class="modal-body">
          <div class="form-group">
            <label>Start Bar</label>
            <input
              v-model.number="localStartBar"
              type="number"
              min="0"
              step="0.25"
              @keydown.left.prevent="nudgeStart(-0.25, $event)"
              @keydown.right.prevent="nudgeStart(0.25, $event)"
            />
          </div>
          <div class="form-group">
            <label>Length (bars)</label>
            <input
              v-model.number="localLengthBars"
              type="number"
              min="0.25"
              step="0.25"
            />
          </div>
          <div class="form-group">
            <label>Intensity</label>
            <div class="intensity-control">
              <input
                v-model.number="localIntensity"
                type="range"
                min="0"
                max="2"
                step="0.05"
              @keydown.up.prevent="nudgeIntensity(0.05, $event)"
              @keydown.down.prevent="nudgeIntensity(-0.05, $event)"
              />
              <span>{{ localIntensity.toFixed(2) }}</span>
            </div>
          </div>
          <div class="form-group">
            <label>
              <input
                v-model="localMuted"
                type="checkbox"
              />
              Muted
            </label>
          </div>
        </div>
        <div class="modal-footer">
          <div class="shortcuts-hint">
            ←/→: nudge start | ↑/↓: intensity | H: half time | D: double time
          </div>
          <div class="actions">
            <button @click="handleHalfTime">Half Time</button>
            <button @click="handleDoubleTime">Double Time</button>
            <button @click="handleDuplicate">Duplicate</button>
            <button class="primary" @click="save">Save</button>
            <button @click="close">Cancel</button>
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref, watch } from "vue";
import { clipsApi } from "../api/clips";
import type { ArrangementSegment } from "../types";

const props = defineProps<{
  segment: ArrangementSegment | null;
  isOpen: boolean;
  snapToGrid?: (value: number) => number;
}>();

const emit = defineEmits<{
  (e: "close"): void;
  (e: "saved"): void;
}>();

const localStartBar = ref(0);
const localLengthBars = ref(0);
const localIntensity = ref(1.0);
const localMuted = ref(false);
const hasUnsavedChanges = ref(false);

watch(
  () => props.segment,
  (segment) => {
    if (segment) {
      localStartBar.value = segment.start_bar;
      localLengthBars.value = segment.length_bars;
      localIntensity.value = segment.intensity;
      localMuted.value = segment.mute;
      hasUnsavedChanges.value = false;
    }
  },
  { immediate: true }
);

watch([localStartBar, localLengthBars, localIntensity, localMuted], () => {
  hasUnsavedChanges.value = true;
});

function nudgeStart(direction: number) {
  if (!props.snapToGrid) return;
  const grid = 0.25; // Default to 1/4 bar
  localStartBar.value = props.snapToGrid(localStartBar.value + direction * grid);
}

function nudgeIntensity(delta: number, event?: KeyboardEvent) {
  if (event) event.preventDefault();
  localIntensity.value = Math.max(0, Math.min(2, localIntensity.value + delta));
}

async function handleHalfTime() {
  if (!props.segment) return;
  try {
    await clipsApi.timeScale(props.segment.id, { mode: "half" });
    emit("saved");
    close();
  } catch (error) {
    console.error("Failed to scale time:", error);
  }
}

async function handleDoubleTime() {
  if (!props.segment) return;
  try {
    await clipsApi.timeScale(props.segment.id, { mode: "double" });
    emit("saved");
    close();
  } catch (error) {
    console.error("Failed to scale time:", error);
  }
}

async function handleDuplicate() {
  if (!props.segment) return;
  try {
    await clipsApi.duplicate(props.segment.id, {});
    emit("saved");
    close();
  } catch (error) {
    console.error("Failed to duplicate:", error);
  }
}

async function save() {
  if (!props.segment) return;
  try {
    await clipsApi.update(props.segment.id, {
      start_bar: localStartBar.value,
      length_bars: localLengthBars.value,
      intensity: localIntensity.value,
      is_muted: localMuted.value,
    });
    hasUnsavedChanges.value = false;
    emit("saved");
    close();
  } catch (error) {
    console.error("Failed to save:", error);
  }
}

function close() {
  if (hasUnsavedChanges.value) {
    if (!confirm("You have unsaved changes. Close anyway?")) {
      return;
    }
  }
  emit("close");
}

function handleKeydown(event: KeyboardEvent) {
  if (!props.isOpen) return;
  if (event.key === "Escape") {
    close();
  } else if (event.key === "h" || event.key === "H") {
    event.preventDefault();
    handleHalfTime();
  } else if (event.key === "d" || event.key === "D") {
    if (event.metaKey || event.ctrlKey) {
      event.preventDefault();
      handleDuplicate();
    } else {
      event.preventDefault();
      handleDoubleTime();
    }
  }
}

onMounted(() => {
  document.addEventListener("keydown", handleKeydown);
});

onUnmounted(() => {
  document.removeEventListener("keydown", handleKeydown);
});
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
  animation: fadeIn 0.15s ease-out;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.modal-content {
  background: #2a2a2a;
  border-radius: 8px;
  width: 90%;
  max-width: 500px;
  max-height: 90vh;
  overflow-y: auto;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5);
  animation: slideUp 0.2s ease-out;
}

@keyframes slideUp {
  from {
    transform: translateY(20px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  border-bottom: 1px solid #444;
}

.modal-header h3 {
  margin: 0;
  color: #fff;
  font-size: 18px;
}

.close-btn {
  width: 32px;
  height: 32px;
  padding: 0;
  background: transparent;
  border: none;
  color: #ccc;
  font-size: 24px;
  cursor: pointer;
  border-radius: 4px;
}

.close-btn:hover {
  background: #3a3a3a;
  color: #fff;
}

.modal-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  color: #ccc;
  font-size: 14px;
  margin-bottom: 8px;
}

.form-group input[type="number"] {
  width: 100%;
  padding: 8px 12px;
  background: #1e1e1e;
  border: 1px solid #555;
  border-radius: 4px;
  color: #fff;
  font-size: 14px;
}

.intensity-control {
  display: flex;
  align-items: center;
  gap: 12px;
}

.intensity-control input[type="range"] {
  flex: 1;
}

.intensity-control span {
  color: #fff;
  font-size: 14px;
  min-width: 50px;
  text-align: right;
}

.modal-footer {
  padding: 16px 20px;
  border-top: 1px solid #444;
}

.shortcuts-hint {
  font-size: 11px;
  color: #666;
  margin-bottom: 12px;
}

.actions {
  display: flex;
  gap: 8px;
  justify-content: flex-end;
}

.actions button {
  padding: 8px 16px;
  background: #4a4a4a;
  color: #fff;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
}

.actions button:hover {
  background: #5a5a5a;
}

.actions button.primary {
  background: #007bff;
}

.actions button.primary:hover {
  background: #0056b3;
}
</style>

