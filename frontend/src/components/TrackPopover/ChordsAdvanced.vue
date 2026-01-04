<template>
  <div class="chords-advanced">
    <div class="control-group">
      <label>Projection</label>
      <select v-model="localProjection" @change="updateProjection">
        <option value="block">Block</option>
        <option value="arpeggio">Arpeggio</option>
        <option value="broken">Broken</option>
        <option value="rhythm_pattern">Rhythm Pattern</option>
      </select>
    </div>
    <div class="control-group">
      <label>Gate %</label>
      <input
        v-model.number="localGatePct"
        type="range"
        min="0"
        max="100"
        step="5"
        @input="updateGatePct"
      />
      <span>{{ localGatePct }}%</span>
    </div>
    <div class="control-group">
      <label>Strum (ms)</label>
      <input
        v-model.number="localStrumMs"
        type="number"
        min="0"
        max="100"
        step="5"
        @input="updateStrumMs"
      />
    </div>
    <div class="control-group">
      <label>Humanize (ms)</label>
      <input
        v-model.number="localHumanizeMs"
        type="number"
        min="0"
        max="50"
        step="5"
        @input="updateHumanizeMs"
      />
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

const localProjection = ref("block");
const localGatePct = ref(85);
const localStrumMs = ref(0);
const localHumanizeMs = ref(10);

function updateProjection() {
  emit("update:params", { projection: localProjection.value });
}

function updateGatePct() {
  emit("update:params", { gate_pct: localGatePct.value });
}

function updateStrumMs() {
  emit("update:params", { strum_ms: localStrumMs.value });
}

function updateHumanizeMs() {
  emit("update:params", { humanize_ms: localHumanizeMs.value });
}

watch(
  () => props.params,
  (newParams) => {
    localProjection.value = newParams.projection || "block";
    localGatePct.value = newParams.gate_pct || 85;
    localStrumMs.value = newParams.strum_ms || 0;
    localHumanizeMs.value = newParams.humanize_ms || 10;
  },
  { immediate: true }
);
</script>

<style scoped>
.chords-advanced {
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

.control-group input[type="range"] {
  width: 100%;
}
</style>

