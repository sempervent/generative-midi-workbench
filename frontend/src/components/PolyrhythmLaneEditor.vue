<template>
  <div class="polyrhythm-lane-editor">
    <div class="header">
      <h4>Polyrhythm Lanes</h4>
      <button v-if="clipId" @click="addLane" class="primary">+ Add Lane</button>
    </div>

    <div v-if="lanes.length === 0" class="empty">
      No lanes configured. Add a lane to start.
    </div>

    <div v-else class="lanes-list">
      <div
        v-for="(lane, index) in sortedLanes"
        :key="lane.id"
        class="lane-row"
        :class="{ muted: lane.mute, soloed: lane.solo }"
      >
        <div class="lane-controls">
          <div class="lane-header">
            <input
              v-model="lane.lane_name"
              type="text"
              @blur="updateLane(lane)"
              class="lane-name"
            />
            <div class="lane-actions">
              <button @click="moveLane(lane.id, -1)" :disabled="index === 0">↑</button>
              <button @click="moveLane(lane.id, 1)" :disabled="index === sortedLanes.length - 1">↓</button>
              <button @click="deleteLane(lane.id)" class="danger">×</button>
            </div>
          </div>

          <div class="lane-fields">
            <div class="field">
              <label>Profile</label>
              <select
                :value="lane.polyrhythm_profile_id"
                @change="updateLaneProfile(lane, $event)"
              >
                <option v-for="profile in profiles" :key="profile.id" :value="profile.id">
                  {{ profile.name }} ({{ getRatio(profile) }})
                </option>
              </select>
            </div>

            <div class="field-row">
              <div class="field">
                <label>Pitch</label>
                <input
                  v-model.number="lane.pitch"
                  type="number"
                  min="0"
                  max="127"
                  @change="updateLane(lane)"
                />
              </div>
              <div class="field">
                <label>Velocity</label>
                <input
                  v-model.number="lane.velocity"
                  type="number"
                  min="1"
                  max="127"
                  @change="updateLane(lane)"
                />
              </div>
            </div>

            <div class="field-row">
              <div class="field">
                <label>Seed Offset</label>
                <input
                  v-model.number="lane.seed_offset"
                  type="number"
                  @change="updateLane(lane)"
                />
              </div>
              <div class="field">
                <label>Role</label>
                <input
                  v-model="lane.instrument_role"
                  type="text"
                  placeholder="kick/snare/hat"
                  @blur="updateLane(lane)"
                />
              </div>
            </div>

            <div class="field-row">
              <label class="checkbox-label">
                <input
                  type="checkbox"
                  v-model="lane.mute"
                  @change="updateLane(lane)"
                />
                Mute
              </label>
              <label class="checkbox-label">
                <input
                  type="checkbox"
                  v-model="lane.solo"
                  @change="updateLane(lane)"
                />
                Solo
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { polyrhythmLanesApi } from "../api/polyrhythm-lanes";
import { polyrhythmsApi } from "../api/polyrhythms";
import type { PolyrhythmLane, PolyrhythmProfile } from "../types";

const props = defineProps<{
  clipId: string | null;
}>();

const emit = defineEmits<{
  lanesUpdated: [];
}>();

const lanes = ref<PolyrhythmLane[]>([]);
const profiles = ref<PolyrhythmProfile[]>([]);

const sortedLanes = computed(() => {
  return [...lanes.value].sort((a, b) => a.order_index - b.order_index);
});

onMounted(async () => {
  await loadProfiles();
  if (props.clipId) {
    await loadLanes();
  }
});

async function loadProfiles() {
  try {
    profiles.value = await polyrhythmsApi.list();
  } catch (error) {
    console.error("Failed to load profiles:", error);
  }
}

async function loadLanes() {
  if (!props.clipId) return;
  try {
    lanes.value = await polyrhythmLanesApi.list(props.clipId);
  } catch (error) {
    console.error("Failed to load lanes:", error);
  }
}

async function addLane() {
  if (!props.clipId || profiles.value.length === 0) return;
  try {
    const newLane = await polyrhythmLanesApi.create(props.clipId, {
      polyrhythm_profile_id: profiles.value[0].id,
      lane_name: `Lane ${lanes.value.length + 1}`,
      pitch: 60,
      velocity: 100,
      order_index: lanes.value.length,
    });
    lanes.value.push(newLane);
    emit("lanesUpdated");
  } catch (error) {
    console.error("Failed to create lane:", error);
  }
}

async function updateLane(lane: PolyrhythmLane) {
  try {
    await polyrhythmLanesApi.update(lane.id, lane);
    emit("lanesUpdated");
  } catch (error) {
    console.error("Failed to update lane:", error);
  }
}

async function updateLaneProfile(lane: PolyrhythmLane, event: Event) {
  const target = event.target as HTMLSelectElement;
  lane.polyrhythm_profile_id = target.value;
  await updateLane(lane);
}

async function deleteLane(laneId: string) {
  try {
    await polyrhythmLanesApi.delete(laneId);
    lanes.value = lanes.value.filter((l) => l.id !== laneId);
    emit("lanesUpdated");
  } catch (error) {
    console.error("Failed to delete lane:", error);
  }
}

async function moveLane(laneId: string, direction: number) {
  const lane = lanes.value.find((l) => l.id === laneId);
  if (!lane) return;

  const currentIndex = sortedLanes.value.findIndex((l) => l.id === laneId);
  const newIndex = currentIndex + direction;

  if (newIndex < 0 || newIndex >= sortedLanes.value.length) return;

  // Swap order_index values
  const otherLane = sortedLanes.value[newIndex];
  const temp = lane.order_index;
  lane.order_index = otherLane.order_index;
  otherLane.order_index = temp;

  await Promise.all([updateLane(lane), updateLane(otherLane)]);
}

function getRatio(profile: PolyrhythmProfile): string {
  const gcd = (a: number, b: number): number => (b === 0 ? a : gcd(b, a % b));
  const divisor = gcd(profile.steps, profile.pulses);
  return `${profile.pulses / divisor}:${profile.steps / divisor}`;
}
</script>

<style scoped>
.polyrhythm-lane-editor {
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 4px;
  padding: 15px;
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 15px;
}

.header h4 {
  margin: 0;
  color: #fff;
}

.lanes-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.lane-row {
  background: #333;
  border: 1px solid #555;
  border-radius: 4px;
  padding: 12px;
}

.lane-row.muted {
  opacity: 0.5;
}

.lane-row.soloed {
  border-color: #4ecdc4;
}

.lane-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.lane-name {
  flex: 1;
  font-weight: bold;
  background: transparent;
  border: none;
  color: #fff;
  padding: 4px;
}

.lane-actions {
  display: flex;
  gap: 5px;
}

.lane-actions button {
  padding: 4px 8px;
  font-size: 12px;
}

.lane-actions button.danger {
  background: #cc4444;
}

.lane-actions button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.lane-fields {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.field label {
  font-size: 11px;
  color: #aaa;
}

.field input,
.field select {
  width: 100%;
  font-size: 12px;
}

.field-row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
}

.checkbox-label {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: #aaa;
}

.empty {
  text-align: center;
  padding: 20px;
  color: #666;
  font-size: 14px;
}
</style>

