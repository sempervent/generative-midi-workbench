<template>
  <div class="suggestion-card" :class="{ committed: suggestion.is_committed }">
    <div class="card-header">
      <div class="card-title-row">
        <span class="kind-badge" :class="suggestion.kind">{{ suggestion.kind }}</span>
        <h4>{{ suggestion.title }}</h4>
        <span class="score">Score: {{ suggestion.score.toFixed(2) }}</span>
      </div>
      <div v-if="suggestion.is_committed" class="committed-badge">✓ Committed</div>
    </div>

    <div class="card-body">
      <details>
        <summary>Explanation</summary>
        <p class="explanation">{{ suggestion.explanation }}</p>
      </details>

      <div class="card-actions">
        <button
          v-if="!suggestion.is_committed"
          @click="$emit('audition', suggestion)"
          class="audition-btn"
        >
          🎵 Audition
        </button>
        <button
          v-if="!suggestion.is_committed"
          @click="$emit('commit', suggestion)"
          class="commit-btn primary"
        >
          ✓ Commit
        </button>
        <span v-else class="committed-text">Already committed</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { Suggestion } from "../api/suggestions";

defineProps<{
  suggestion: Suggestion;
}>();

defineEmits<{
  audition: [suggestion: Suggestion];
  commit: [suggestion: Suggestion];
}>();
</script>

<style scoped>
.suggestion-card {
  background: #2a2a2a;
  border: 1px solid #444;
  border-radius: 4px;
  padding: 12px;
  margin-bottom: 10px;
}

.suggestion-card.committed {
  opacity: 0.7;
  border-color: #666;
}

.card-header {
  margin-bottom: 10px;
}

.card-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 5px;
}

.kind-badge {
  padding: 2px 8px;
  border-radius: 3px;
  font-size: 10px;
  font-weight: bold;
  text-transform: uppercase;
}

.kind-badge.harmony {
  background: #4ecdc4;
  color: #000;
}

.kind-badge.rhythm {
  background: #ff6b6b;
  color: #fff;
}

.kind-badge.melody {
  background: #95e1d3;
  color: #000;
}

.card-title-row h4 {
  flex: 1;
  margin: 0;
  font-size: 14px;
  color: #fff;
}

.score {
  font-size: 11px;
  color: #aaa;
}

.committed-badge {
  font-size: 11px;
  color: #4ecdc4;
  font-weight: bold;
}

.card-body {
  font-size: 12px;
}

details {
  margin-bottom: 10px;
}

summary {
  cursor: pointer;
  color: #aaa;
  font-size: 11px;
}

summary:hover {
  color: #fff;
}

.explanation {
  margin-top: 8px;
  color: #ccc;
  font-size: 12px;
  line-height: 1.4;
}

.card-actions {
  display: flex;
  gap: 8px;
  margin-top: 10px;
}

.audition-btn,
.commit-btn {
  flex: 1;
  font-size: 12px;
  padding: 6px 12px;
}

.committed-text {
  color: #666;
  font-size: 11px;
  font-style: italic;
}
</style>

