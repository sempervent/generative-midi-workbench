/**
 * Centralized timing conversion utilities.
 * All tick/bar/time conversions should go through this module.
 */

export const PPQ = 480; // Pulses Per Quarter Note (standard MIDI resolution)

/**
 * Calculate ticks per bar based on time signature.
 */
export function ticksPerBar(timeSignatureNum: number, timeSignatureDen: number): number {
  const quarterNotesPerBar = (timeSignatureNum * 4) / timeSignatureDen;
  return quarterNotesPerBar * PPQ;
}

/**
 * Convert bars to ticks.
 */
export function barsToTicks(
  bars: number,
  timeSignatureNum: number,
  timeSignatureDen: number
): number {
  return bars * ticksPerBar(timeSignatureNum, timeSignatureDen);
}

/**
 * Convert ticks to bars.
 */
export function ticksToBars(
  ticks: number,
  timeSignatureNum: number,
  timeSignatureDen: number
): number {
  const tpb = ticksPerBar(timeSignatureNum, timeSignatureDen);
  return ticks / tpb;
}

/**
 * Convert a note's position from clip-local ticks to project-absolute ticks.
 * Accounts for clip start bar and offsets.
 */
export function clipLocalToProjectTicks(
  clipLocalTick: number,
  clipStartBar: number,
  clipOffsetTicks: number,
  trackOffsetTicks: number,
  timeSignatureNum: number,
  timeSignatureDen: number
): number {
  const tpb = ticksPerBar(timeSignatureNum, timeSignatureDen);
  const clipStartTicks = clipStartBar * tpb;
  return clipLocalTick + clipStartTicks + clipOffsetTicks + trackOffsetTicks;
}

/**
 * Validate that a tick value is valid (not NaN, not Infinity, is a number).
 */
export function validateTick(tick: number, context: string): number {
  if (typeof tick !== "number" || Number.isNaN(tick) || !Number.isFinite(tick)) {
    if (import.meta.env.DEV) {
      console.error(`Invalid tick value in ${context}:`, tick);
      throw new Error(`Invalid tick value in ${context}: ${tick}`);
    }
    return 0;
  }
  return tick;
}
