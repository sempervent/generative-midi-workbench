import { onMounted, onUnmounted, ref } from "vue";
import type { useGrid } from "./useGrid";

export interface DragState {
  isDragging: boolean;
  startX: number;
  currentX: number;
  snappedX: number;
  startValue: number;
  currentValue: number;
  snappedValue: number;
}

export function useDragSnap(
  snapToGrid: ReturnType<typeof useGrid>["snapToGrid"],
  pixelsPerBar: number,
  onDragStart?: (value: number) => void,
  onDrag?: (value: number, snapped: number) => void,
  onDragEnd?: (value: number) => void
) {
  const dragState = ref<DragState | null>(null);
  const isDragging = computed(() => dragState.value !== null);

  function startDrag(event: MouseEvent | TouchEvent, initialValue: number, fine = false) {
    const clientX = "touches" in event ? event.touches[0].clientX : event.clientX;
    const startX = clientX;
    const startValue = initialValue;

    dragState.value = {
      isDragging: true,
      startX,
      currentX: startX,
      snappedX: startX,
      startValue,
      currentValue: startValue,
      snappedValue: startValue,
    };

    onDragStart?.(startValue);

    const handleMove = (e: MouseEvent | TouchEvent) => {
      if (!dragState.value) return;
      const clientX = "touches" in e ? e.touches[0].clientX : e.clientX;
      const deltaX = clientX - dragState.value.startX;
      const deltaBars = deltaX / pixelsPerBar;
      const newValue = dragState.value.startValue + deltaBars;
      const snapped = snapToGrid(newValue, fine);

      dragState.value.currentX = clientX;
      dragState.value.currentValue = newValue;
      dragState.value.snappedValue = snapped;
      dragState.value.snappedX =
        dragState.value.startX + (snapped - dragState.value.startValue) * pixelsPerBar;

      onDrag?.(newValue, snapped);
    };

    const handleEnd = () => {
      if (!dragState.value) return;
      const finalValue = dragState.value.snappedValue;
      onDragEnd?.(finalValue);
      dragState.value = null;
    };

    document.addEventListener("mousemove", handleMove);
    document.addEventListener("touchmove", handleMove);
    document.addEventListener("mouseup", handleEnd, { once: true });
    document.addEventListener("touchend", handleEnd, { once: true });
  }

  return {
    dragState,
    isDragging,
    startDrag,
  };
}
