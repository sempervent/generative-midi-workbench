<template>
  <div class="melody-advanced">
    <div class="control-group">
      <label>
        <input
          v-model="localScaleLock"
          type="checkbox"
          @change="updateScaleLock"
        />
        Scale Lock
      </label>
    </div>
    <div class="control-group">
      <label>Register Range</label>
      <div class="range-inputs">
        <input
          v-model.number="localRegisterLow"
          type="number"
          min="3"
          max="6"
          @input="updateRegisterRange"
        />
        <span>to</span>
        <input
          v-model.number="localRegisterHigh"
          type="number"
          min="4"
          max="7"
          @input="updateRegisterRange"
        />
      </div>
    </div>
    <div class="control-group">
      <label>Leapiness</label>
      <input
        v-model.number="localLeapiness"
        type="range"
        min="0"
        max="1"
        step="0.1"
        @input="updateLeapiness"
      />
      <span>{{ localLeapiness.toFixed(1) }}</span>
    </div>
    <div class="control-group">
      <label>Motif Repeat Probability</label>
      <input
        v-model.number="localMotifRepeat"
        type="range"
        min="0"
        max="1"
        step="0.1"
        @input="updateMotifRepeat"
      />
      <span>{{ localMotifRepeat.toFixed(1) }}</span>
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

const localScaleLock = ref(true);
const localRegisterLow = ref(4);
const localRegisterHigh = ref(6);
const localLeapiness = ref(0.3);
const localMotifRepeat = ref(0.5);

function updateScaleLock() {
  emit("update:params", { scale_lock: localScaleLock.value });
}

function updateRegisterRange() {
  emit("update:params", {
    register_low: localRegisterLow.value,
    register_high: localRegisterHigh.value,
  });
}

function updateLeapiness() {
  emit("update:params", { leapiness: localLeapiness.value });
}

function updateMotifRepeat() {
  emit("update:params", { motif_repeat_probability: localMotifRepeat.value });
}

watch(
  () => props.params,
  (newParams) => {
    localScaleLock.value = newParams.scale_lock ?? true;
    localRegisterLow.value = newParams.register_low || 4;
    localRegisterHigh.value = newParams.register_high || 6;
    localLeapiness.value = newParams.leapiness || 0.3;
    localMotifRepeat.value = newParams.motif_repeat_probability || 0.5;
  },
  { immediate: true }
);
</script>

<style scoped>
.melody-advanced {
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

.control-group input[type="range"] {
  width: 100%;
}
</style>

