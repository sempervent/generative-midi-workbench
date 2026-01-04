import { computed, ref } from "vue";
import type { ArrangementSegment } from "../types";

export interface PreviewState {
  originalSegment: ArrangementSegment;
  previewSegment: ArrangementSegment;
  isActive: boolean;
}

export function usePreviewSession() {
  const previewState = ref<PreviewState | null>(null);
  const isPreviewing = computed(() => previewState.value !== null);

  function startPreview(segment: ArrangementSegment) {
    // Snapshot original state
    previewState.value = {
      originalSegment: { ...segment },
      previewSegment: { ...segment },
      isActive: true,
    };
  }

  function updatePreview(updates: Partial<ArrangementSegment>) {
    if (!previewState.value) return;
    previewState.value.previewSegment = {
      ...previewState.value.previewSegment,
      ...updates,
    };
  }

  function applyPreview(): ArrangementSegment {
    if (!previewState.value) {
      throw new Error("No active preview session");
    }
    const applied = previewState.value.previewSegment;
    previewState.value = null;
    return applied;
  }

  function cancelPreview(): ArrangementSegment {
    if (!previewState.value) {
      throw new Error("No active preview session");
    }
    const original = previewState.value.originalSegment;
    previewState.value = null;
    return original;
  }

  function clearPreview() {
    previewState.value = null;
  }

  return {
    previewState,
    isPreviewing,
    startPreview,
    updatePreview,
    applyPreview,
    cancelPreview,
    clearPreview,
  };
}
