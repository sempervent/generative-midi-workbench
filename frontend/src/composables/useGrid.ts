import { computed, ref } from "vue";

export type GridResolution = "1bar" | "1/2" | "1/4" | "1beat" | "off";

export function useGrid(timeSignatureNum = 4) {
  const gridResolution = ref<GridResolution>("1bar");

  const gridValue = computed(() => {
    switch (gridResolution.value) {
      case "1bar":
        return 1.0;
      case "1/2":
        return 0.5;
      case "1/4":
        return 0.25;
      case "1beat":
        return 1.0 / timeSignatureNum;
      case "off":
        return 0;
      default:
        return 1.0;
    }
  });

  function snapToGrid(value: number, fine = false): number {
    if (gridResolution.value === "off" && !fine) {
      // Free move, but quantize on drop to nearest beat
      return Math.round(value * timeSignatureNum) / timeSignatureNum;
    }
    if (fine && gridResolution.value !== "off") {
      // Shift key: snap to 1 beat
      return Math.round(value * timeSignatureNum) / timeSignatureNum;
    }
    const grid = gridValue.value;
    if (grid === 0) return value;
    return Math.round(value / grid) * grid;
  }

  function setGrid(resolution: GridResolution) {
    gridResolution.value = resolution;
  }

  return {
    gridResolution,
    gridValue,
    snapToGrid,
    setGrid,
  };
}
