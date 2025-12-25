<template>
  <div class="polyrhythm-lane-grid">
    <div v-if="preview" class="grid-header">
      <div class="grid-info">
        <span>LCM Grid: {{ preview.grid_spec.lcm_steps }} steps</span>
        <span>{{ preview.grid_spec.grid_steps_per_bar }} steps/bar</span>
      </div>
    </div>

    <div class="lanes-stack">
      <div
        v-for="laneInfo in preview?.lanes || []"
        :key="laneInfo.lane_id"
        class="lane-row"
        :class="{ muted: laneInfo.mute, soloed: laneInfo.solo }"
      >
        <div class="lane-label">
          <span class="lane-name">{{ laneInfo.lane_name }}</span>
          <span class="lane-ratio">{{ laneInfo.ratio }}</span>
          <span class="lane-pitch">P{{ laneInfo.pitch }}</span>
        </div>
        <div class="lane-grid">
          <div
            v-for="step in gridSteps"
            :key="step"
            class="grid-cell"
            :class="{ active: isStepActive(laneInfo.lane_id, step) }"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from "vue";
import type { PolyrhythmLanesPreview } from "../types";

const props = defineProps<{
  preview: PolyrhythmLanesPreview | null;
  bars?: number;
}>();

const bars = computed(() => props.bars || 1);

const gridSteps = computed(() => {
  if (!props.preview) return [];
  const stepsPerBar = props.preview.grid_spec.grid_steps_per_bar;
  return Array.from({ length: stepsPerBar * bars.value }, (_, i) => i);
});

function isStepActive(laneId: string, step: number): boolean {
  if (!props.preview) return false;

  const stepsPerBar = props.preview.grid_spec.grid_steps_per_bar;
  const bar = Math.floor(step / stepsPerBar);
  const stepInBar = step % stepsPerBar;

  // Find events for this lane in this bar
  const laneEvents = props.preview.events.filter((e) => {
    // This is simplified - in reality we'd need to map events to grid steps
    // For now, just check if there's an event near this step
    return true; // Placeholder
  });

  // For now, show a simple pattern based on lane index
  const laneIndex = props.preview.lanes.findIndex((l) => l.lane_id === laneId);
  return stepInBar % (laneIndex + 2) === 0;
}
</script>

<style scoped>
.polyrhythm-lane-grid {
  background: #1a1a1a;
  border: 1px solid #444;
  border-radius: 4px;
  padding: 15px;
}

.grid-header {
  margin-bottom: 15px;
  padding-bottom: 10px;
  border-bottom: 1px solid #444;
}

.grid-info {
  display: flex;
  gap: 15px;
  font-size: 12px;
  color: #aaa;
}

.lanes-stack {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.lane-row {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  background: #2a2a2a;
  border-radius: 4px;
}

.lane-row.muted {
  opacity: 0.4;
}

.lane-row.soloed {
  border: 1px solid #4ecdc4;
}

.lane-label {
  display: flex;
  flex-direction: column;
  min-width: 120px;
  font-size: 11px;
}

.lane-name {
  font-weight: bold;
  color: #fff;
}

.lane-ratio {
  color: #4ecdc4;
}

.lane-pitch {
  color: #888;
}

.lane-grid {
  display: flex;
  gap: 2px;
  flex: 1;
}

.grid-cell {
  flex: 1;
  height: 20px;
  background: #333;
  border: 1px solid #444;
  border-radius: 2px;
}

.grid-cell.active {
  background: #4ecdc4;
  border-color: #4ecdc4;
}
</style>

