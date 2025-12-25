/** Transport loop management utilities for Tone.js */

import * as Tone from "tone";

/**
 * Set Transport loop points and enable/disable looping.
 *
 * @param loopEnabled - Whether looping is enabled
 * @param startBar - Start bar (0-indexed, inclusive)
 * @param endBar - End bar (0-indexed, exclusive)
 * @param timeSigNum - Time signature numerator
 */
export function setTransportLoop(
  loopEnabled: boolean,
  startBar: number,
  endBar: number,
  timeSigNum: number
): void {
  // Validate range
  if (endBar <= startBar) {
    console.warn(`Invalid loop range: endBar (${endBar}) must be > startBar (${startBar})`);
    return;
  }

  // Convert bars to Tone musical time format: "bars:beats:sixteenths"
  // Tone uses 0-indexed bars, so startBar:0:0 means bar 0, beat 0, sixteenth 0
  const loopStart = `${startBar}:0:0`;
  const loopEnd = `${endBar}:0:0`;

  // Set loop points
  Tone.Transport.loopStart = loopStart;
  Tone.Transport.loopEnd = loopEnd;
  Tone.Transport.loop = loopEnabled;

  // If currently playing and position is outside loop, snap to start
  if (Tone.Transport.state === "started") {
    const currentPos = Tone.Transport.position as string;
    const currentBar = parseBarFromPosition(currentPos);
    if (currentBar < startBar || currentBar >= endBar) {
      Tone.Transport.position = loopStart;
    }
  }
}

/**
 * Parse bar number from Tone position string.
 * Handles formats like "1:0:0", "2.5:0:0", etc.
 */
function parseBarFromPosition(position: string): number {
  const parts = position.split(":");
  if (parts.length === 0) return 0;
  const barPart = parts[0];
  const bar = Number.parseFloat(barPart);
  return Math.floor(bar);
}

/**
 * Compute project length in bars from arrangement.
 *
 * @param arrangement - The arrangement to compute length for
 * @returns Project length in bars (minimum 1)
 */
export function computeProjectLengthBars(arrangement: {
  bars: number;
  tracks: Array<{
    clips: Array<{
      start_bar: number;
      length_bars: number;
    }>;
  }>;
}): number {
  // Start with project.bars as baseline
  let maxBar = arrangement.bars;

  // Find the maximum end bar across all clips
  for (const track of arrangement.tracks) {
    for (const clip of track.clips) {
      const clipEndBar = clip.start_bar + clip.length_bars;
      if (clipEndBar > maxBar) {
        maxBar = clipEndBar;
      }
    }
  }

  // Ensure minimum of 1 bar
  return Math.max(1, maxBar);
}
