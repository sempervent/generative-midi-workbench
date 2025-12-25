<template>
  <div class="polyrhythm-editor">
    <div class="editor-header">
      <h4>Polyrhythm Profile</h4>
      <select v-if="profiles.length > 0" v-model="selectedProfileId" @change="loadProfile">
        <option value="">Create New...</option>
        <option v-for="profile in profiles" :key="profile.id" :value="profile.id">
          {{ profile.name }}
        </option>
      </select>
    </div>

    <div class="editor-fields">
      <div class="field">
        <label>Name</label>
        <input v-model="localProfile.name" type="text" placeholder="Profile name" />
      </div>

      <div class="field-row">
        <div class="field">
          <label>Steps</label>
          <input v-model.number="localProfile.steps" type="number" min="1" max="128" />
        </div>
        <div class="field">
          <label>Pulses</label>
          <input v-model.number="localProfile.pulses" type="number" min="1" max="128" />
        </div>
      </div>

      <div class="field-row">
        <div class="field">
          <label>Rotation</label>
          <input v-model.number="localProfile.rotation" type="number" min="0" />
        </div>
        <div class="field">
          <label>Cycle Beats</label>
          <input v-model.number="localProfile.cycle_beats" type="number" min="0.1" max="32" step="0.1" />
        </div>
      </div>

      <div class="field">
        <label>Swing (0.0-1.0)</label>
        <input v-model.number="localProfile.swing" type="number" min="0" max="1" step="0.1" />
      </div>

      <div class="ratio-display">
        <strong>Ratio:</strong> {{ calculatedRatio }}
      </div>

      <div class="editor-actions">
        <button @click="preview">Preview</button>
        <button class="primary" @click="save">Save Profile</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from "vue";
import { polyrhythmsApi } from "../api/polyrhythms";
import type { PolyrhythmProfile } from "../types";

const props = defineProps<{
  modelValue: PolyrhythmProfile | null;
  projectId: string;
}>();

const emit = defineEmits<{
  "update:modelValue": [value: PolyrhythmProfile | null];
}>();

const profiles = ref<PolyrhythmProfile[]>([]);
const selectedProfileId = ref<string>("");
const localProfile = ref<Partial<PolyrhythmProfile>>({
  name: "",
  steps: 5,
  pulses: 3,
  rotation: 0,
  cycle_beats: 4.0,
  swing: null,
  humanize_ms: null,
});

const calculatedRatio = computed(() => {
  const steps = localProfile.value.steps || 1;
  const pulses = localProfile.value.pulses || 0;
  if (pulses === 0) return "0:1";

  const gcd = (a: number, b: number): number => (b === 0 ? a : gcd(b, a % b));
  const divisor = gcd(steps, pulses);
  const simplifiedSteps = steps / divisor;
  const simplifiedPulses = pulses / divisor;

  return `${simplifiedPulses}:${simplifiedSteps}`;
});

async function loadProfiles() {
  try {
    profiles.value = await polyrhythmsApi.list();
  } catch (error) {
    console.error("Failed to load profiles:", error);
  }
}

function loadProfile() {
  if (!selectedProfileId.value) {
    return;
  }
  const profile = profiles.value.find((p) => p.id === selectedProfileId.value);
  if (profile) {
    localProfile.value = { ...profile };
    emit("update:modelValue", profile);
  }
}

async function preview() {
  if (!localProfile.value.steps || !localProfile.value.pulses) return;

  try {
    const events = await polyrhythmsApi.preview(props.projectId, {
      steps: localProfile.value.steps,
      pulses: localProfile.value.pulses,
      rotation: localProfile.value.rotation || 0,
      cycle_beats: localProfile.value.cycle_beats || 4.0,
      swing: localProfile.value.swing,
    });
    console.log("Preview events:", events);
    // TODO: Visualize preview in piano roll
  } catch (error) {
    console.error("Preview failed:", error);
  }
}

async function save() {
  if (!localProfile.value.name) {
    alert("Please enter a profile name");
    return;
  }

  try {
    const saved = await polyrhythmsApi.create(localProfile.value as PolyrhythmProfile);
    profiles.value.push(saved);
    selectedProfileId.value = saved.id;
    emit("update:modelValue", saved);
  } catch (error) {
    console.error("Save failed:", error);
    alert("Failed to save profile");
  }
}

watch(
  () => props.modelValue,
  (newVal) => {
    if (newVal) {
      localProfile.value = { ...newVal };
      selectedProfileId.value = newVal.id;
    }
  },
  { immediate: true }
);

loadProfiles();
</script>

<style scoped>
.polyrhythm-editor {
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 4px;
  padding: 15px;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.editor-header h4 {
  margin: 0;
  color: #fff;
}

.editor-header select {
  width: 200px;
}

.editor-fields {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 5px;
}

.field label {
  font-size: 12px;
  color: #aaa;
}

.field input {
  width: 100%;
}

.field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.ratio-display {
  padding: 8px;
  background: #333;
  border-radius: 4px;
  color: #4ecdc4;
  font-size: 14px;
}

.editor-actions {
  display: flex;
  gap: 10px;
  margin-top: 10px;
}

.editor-actions button {
  flex: 1;
}
</style>

