<template>
  <div class="beats-advanced">
    <div class="control-group">
      <label>Style</label>
      <select v-model="localStyle" @change="updateStyle">
        <option value="boom_bap">Boom Bap</option>
        <option value="trap">Trap</option>
        <option value="drill">Drill</option>
        <option value="lofi">Lo-Fi</option>
        <option value="minimal">Minimal</option>
      </select>
    </div>
    <div class="control-group">
      <label>Hat Mode</label>
      <select v-model="localHatMode" @change="updateHatMode">
        <option value="straight_8">Straight 8ths</option>
        <option value="straight_16">Straight 16ths</option>
        <option value="skip_step">Skip Step</option>
        <option value="roll">Roll</option>
      </select>
    </div>
    <div class="control-group">
      <label>
        <input
          v-model="localGhostNotes"
          type="checkbox"
          @change="updateGhostNotes"
        />
        Ghost Notes
      </label>
    </div>
    <div class="control-group">
      <label>Pause Probability</label>
      <input
        v-model.number="localPauseProb"
        type="range"
        min="0"
        max="1"
        step="0.1"
        @input="updatePauseProb"
      />
      <span>{{ localPauseProb.toFixed(1) }}</span>
    </div>
    <div class="control-group">
      <label>Accent Strength</label>
      <input
        v-model.number="localAccentStrength"
        type="range"
        min="0"
        max="1"
        step="0.1"
        @input="updateAccentStrength"
      />
      <span>{{ localAccentStrength.toFixed(1) }}</span>
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

const localStyle = ref("boom_bap");
const localHatMode = ref("straight_16");
const localGhostNotes = ref(true);
const localPauseProb = ref(0.0);
const localAccentStrength = ref(0.5);

function updateStyle() {
  emit("update:params", { style: localStyle.value });
}

function updateHatMode() {
  emit("update:params", { hat_mode: localHatMode.value });
}

function updateGhostNotes() {
  emit("update:params", { ghost_notes: localGhostNotes.value });
}

function updatePauseProb() {
  emit("update:params", { pause_probability: localPauseProb.value });
}

function updateAccentStrength() {
  emit("update:params", { accent_strength: localAccentStrength.value });
}

watch(
  () => props.params,
  (newParams) => {
    localStyle.value = newParams.style || "boom_bap";
    localHatMode.value = newParams.hat_mode || "straight_16";
    localGhostNotes.value = newParams.ghost_notes ?? true;
    localPauseProb.value = newParams.pause_probability || 0.0;
    localAccentStrength.value = newParams.accent_strength || 0.5;
  },
  { immediate: true }
);
</script>

<style scoped>
.beats-advanced {
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
.control-group input[type="range"] {
  padding: 6px;
  background: #333;
  border: 1px solid #555;
  border-radius: 4px;
  color: #fff;
  font-size: 13px;
}

.control-group input[type="checkbox"] {
  margin-right: 6px;
}
</style>

