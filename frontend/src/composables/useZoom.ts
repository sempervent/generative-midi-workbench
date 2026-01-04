import { computed, ref } from "vue";

export function useZoom(initialPixelsPerBar = 60) {
  const zoomLevel = ref(1.0);
  const minZoom = 0.25;
  const maxZoom = 4.0;

  const pixelsPerBar = computed(() => initialPixelsPerBar * zoomLevel.value);

  function setZoom(level: number) {
    zoomLevel.value = Math.max(minZoom, Math.min(maxZoom, level));
  }

  function zoomIn(factor = 1.2) {
    setZoom(zoomLevel.value * factor);
  }

  function zoomOut(factor = 1.2) {
    setZoom(zoomLevel.value / factor);
  }

  function resetZoom() {
    zoomLevel.value = 1.0;
  }

  function handleWheel(event: WheelEvent, centerX: number, containerWidth: number) {
    if (!event.ctrlKey && !event.metaKey) return;

    event.preventDefault();
    const delta = -event.deltaY * 0.001;
    const oldZoom = zoomLevel.value;
    const newZoom = Math.max(minZoom, Math.min(maxZoom, oldZoom * (1 + delta)));

    // Zoom centered on cursor
    const zoomFactor = newZoom / oldZoom;
    setZoom(newZoom);

    return { zoomFactor, centerX, containerWidth };
  }

  return {
    zoomLevel,
    pixelsPerBar,
    setZoom,
    zoomIn,
    zoomOut,
    resetZoom,
    handleWheel,
  };
}
