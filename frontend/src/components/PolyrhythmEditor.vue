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
import * as Tone from "tone";
import { computed, nextTick, onMounted, onUnmounted, ref, watch } from "vue";
import { polyrhythmsApi } from "../api/polyrhythms";
import type { PolyrhythmProfile } from "../types";

const props = defineProps<{
  modelValue: PolyrhythmProfile | null;
  projectId: string;
  bpm?: number;
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

let previewPart: Tone.Part | null = null;
let previewSynth: Tone.Synth | null = null;

async function preview() {
  if (!localProfile.value.steps || !localProfile.value.pulses) return;

  // Stop any existing preview
  if (previewPart) {
    previewPart.stop();
    previewPart.dispose();
    previewPart = null;
  }
  if (previewSynth) {
    previewSynth.dispose();
    previewSynth = null;
  }

  try {
    // Ensure AudioContext is started (only on user gesture)
    const { ensureAudioStarted } = await import("../audio/ensureAudio");
    await ensureAudioStarted();

    const events = await polyrhythmsApi.preview(props.projectId, {
      steps: localProfile.value.steps,
      pulses: localProfile.value.pulses,
      rotation: localProfile.value.rotation || 0,
      cycle_beats: localProfile.value.cycle_beats || 4.0,
      swing: localProfile.value.swing,
    });

    if (events.length === 0) {
      console.warn("No preview events returned");
      return;
    }

    // Get project BPM from prop or default
    const bpm = props.bpm || 120;
    const PPQ = 480;
    const secondsPerTick = 60 / (bpm * PPQ);

    // Create synth
    previewSynth = new Tone.Synth().toDestination();

    // Convert events to Tone.Part format
    const toneEvents = events.map((event) => {
      const startTime = event.start_tick * secondsPerTick;
      return {
        time: startTime,
        note: {
          pitch: event.pitch,
          velocity: event.velocity / 127,
          duration: Math.max(event.duration_tick * secondsPerTick, 0.1),
        },
      };
    });

    // Create and start Tone.Part
    previewPart = new Tone.Part((time, event) => {
      if (previewSynth) {
        const freq = Tone.Frequency(event.note.pitch, "midi").toFrequency();
        previewSynth.triggerAttackRelease(freq, event.note.duration, time, event.note.velocity);
      }
    }, toneEvents);

    previewPart.start(0);
    Tone.Transport.start();

    // Auto-stop after cycle completes (or 8 seconds max)
    const cycleBeats = localProfile.value.cycle_beats || 4.0;
    const cycleSeconds = (cycleBeats * 60) / bpm;
    const maxDuration = Math.max(cycleSeconds * 2, 8);

    setTimeout(() => {
      if (previewPart) {
        previewPart.stop();
        previewPart.dispose();
        previewPart = null;
      }
      if (previewSynth) {
        previewSynth.dispose();
        previewSynth = null;
      }
      Tone.Transport.stop();
    }, maxDuration * 1000);

    // Debug logging
    if (
      import.meta.env.DEV ||
      localStorage.getItem("midinecromancer:debug:polyrhythm") === "true"
    ) {
      console.log("[Polyrhythm Preview]", {
        eventsCount: events.length,
        cycleBeats,
        toneEventsCount: toneEvents.length,
        firstEvent: toneEvents[0],
      });
    }
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

// Load profiles on mount
onMounted(async () => {
  await nextTick();
  await loadProfiles();
});

// Cleanup on unmount
onUnmounted(() => {
  if (previewPart) {
    previewPart.stop();
    previewPart.dispose();
    previewPart = null;
  }
  if (previewSynth) {
    previewSynth.dispose();
    previewSynth = null;
  }
  Tone.Transport.stop();
  Tone.Transport.cancel();
});
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

