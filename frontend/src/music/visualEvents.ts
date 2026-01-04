/**
 * Visual event adapter: converts notes and chord events to a unified visual representation.
 */

import type { ChordEvent, Note } from "../types";
import { clipLocalToProjectTicks, validateTick } from "./timing";

export type VisualEventKind = "note" | "chord";

export interface VisualEvent {
  id: string;
  kind: VisualEventKind;
  startTick: number;
  durationTick: number;
  pitch?: number;
  velocity?: number;
  label?: string;
  intensity?: number;
  // Additional metadata
  metadata?: {
    romanNumeral?: string;
    chordName?: string;
    isEnabled?: boolean;
    isLocked?: boolean;
  };
}

/**
 * Convert notes to visual events.
 */
export function notesToVisualEvents(
  notes: Note[],
  clipStartBar: number,
  clipOffsetTicks: number,
  trackOffsetTicks: number,
  timeSignatureNum: number,
  timeSignatureDen: number
): VisualEvent[] {
  return notes.map((note) => {
    const startTick = clipLocalToProjectTicks(
      note.start_tick,
      clipStartBar,
      clipOffsetTicks,
      trackOffsetTicks,
      timeSignatureNum,
      timeSignatureDen
    );

    return {
      id: note.id,
      kind: "note" as const,
      startTick: validateTick(startTick, `note ${note.id} start`),
      durationTick: validateTick(note.duration_tick, `note ${note.id} duration`),
      pitch: note.pitch,
      velocity: note.velocity,
    };
  });
}

/**
 * Convert chord events to visual events.
 */
export function chordEventsToVisualEvents(
  chords: ChordEvent[],
  clipStartBar: number,
  clipOffsetTicks: number,
  trackOffsetTicks: number,
  timeSignatureNum: number,
  timeSignatureDen: number
): VisualEvent[] {
  return chords
    .filter((chord) => chord.is_enabled !== false) // Only enabled chords
    .map((chord) => {
      const startTick = clipLocalToProjectTicks(
        chord.start_tick,
        clipStartBar,
        clipOffsetTicks,
        trackOffsetTicks,
        timeSignatureNum,
        timeSignatureDen
      );

      return {
        id: chord.id,
        kind: "chord" as const,
        startTick: validateTick(startTick, `chord ${chord.id} start`),
        durationTick: validateTick(chord.duration_tick, `chord ${chord.id} duration`),
        intensity: chord.intensity,
        label: chord.chord_name,
        metadata: {
          romanNumeral: chord.roman_numeral,
          chordName: chord.chord_name,
          isEnabled: chord.is_enabled,
          isLocked: chord.is_locked,
        },
      };
    });
}
