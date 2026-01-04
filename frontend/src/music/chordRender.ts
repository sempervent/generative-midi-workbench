/**
 * Chord rendering utilities for converting chord events to playable notes.
 *
 * NOTE: This frontend renderer should match the backend chord_patterns.py renderer
 * for consistency. For production, consider using the backend renderer via API
 * or sharing the algorithm via tests.
 */

import type { ChordEvent } from "../types";

const PPQ = 480; // Pulses per quarter note

const DEBUG =
  typeof window !== "undefined" &&
  (localStorage.getItem("midinecromancer:debug:chordRender") === "true" || import.meta.env.DEV);

function debugLog(...args: any[]) {
  if (DEBUG) {
    console.log("[chordRender]", ...args);
  }
}

/**
 * Convert a chord symbol to MIDI note numbers.
 * Improved parser that handles sharps, flats, and various chord qualities.
 * @param chordName - Chord name (e.g., "C", "Am", "G7", "F#m", "Bbmaj7")
 * @param romanNumeral - Optional roman numeral (e.g., "I", "vi", "V7") - more reliable
 * @param tonic - Key tonic (e.g., "C", "G#")
 * @param mode - Mode (e.g., "ionian", "aeolian")
 * @param octave - Base octave (default 4)
 * @returns Array of MIDI note numbers
 */
function chordNameToNotes(
  chordName: string,
  tonic: string,
  mode: string,
  octave = 4,
  romanNumeral?: string
): number[] {
  // Map note names to semitones from C
  const noteMap: Record<string, number> = {
    C: 0,
    "C#": 1,
    Db: 1,
    D: 2,
    "D#": 3,
    Eb: 3,
    E: 4,
    F: 5,
    "F#": 6,
    Gb: 6,
    G: 7,
    "G#": 8,
    Ab: 8,
    A: 9,
    "A#": 10,
    Bb: 10,
    B: 11,
  };

  // If we have a roman numeral, use it for more reliable pitch calculation
  if (romanNumeral) {
    return chordNameToNotesFromRoman(romanNumeral, tonic, mode, octave);
  }

  // Parse chord name - handle sharps/flats in root note
  // Examples: "C", "C#", "F#m", "Bbm", "G#maj7", "Ab7"
  const chordNameUpper = chordName.trim();

  // Extract root note (may include # or b)
  let rootNote = "";
  let i = 0;

  // Handle single letter or letter + sharp/flat
  if (chordNameUpper[i] && /[A-G]/.test(chordNameUpper[i])) {
    rootNote += chordNameUpper[i];
    i++;
    // Check for # or b
    if (chordNameUpper[i] === "#" || chordNameUpper[i] === "b") {
      rootNote += chordNameUpper[i];
      i++;
    }
  }

  if (!rootNote) {
    console.warn(`Could not parse root note from chord: ${chordName}`);
    return [];
  }

  // Parse quality
  const remainder = chordNameUpper.slice(i);
  const isMinor = remainder.includes("m") || remainder.includes("min");
  const is7th = remainder.includes("7");
  const isMajor7 = remainder.includes("maj7") || remainder.includes("M7");
  const isDim = remainder.includes("dim");
  const isAug = remainder.includes("aug");

  const rootSemitone = noteMap[rootNote];
  if (rootSemitone === undefined) {
    console.warn(`Unknown root note: ${rootNote} in chord ${chordName}`);
    return [];
  }

  const rootMidi = (octave + 1) * 12 + rootSemitone;

  // Build chord intervals
  const intervals: number[] = [0]; // Root

  if (isDim) {
    intervals.push(3); // Minor third
    intervals.push(6); // Diminished fifth
  } else if (isAug) {
    intervals.push(4); // Major third
    intervals.push(8); // Augmented fifth
  } else if (isMinor) {
    intervals.push(3); // Minor third
    intervals.push(7); // Perfect fifth
  } else {
    intervals.push(4); // Major third
    intervals.push(7); // Perfect fifth
  }

  if (is7th) {
    if (isMajor7) {
      intervals.push(11); // Major 7th
    } else {
      intervals.push(10); // Minor 7th (dominant 7th)
    }
  }

  return intervals.map((interval) => rootMidi + interval);
}

/**
 * Convert roman numeral to MIDI notes using scale degrees.
 * This is more reliable than parsing chord names.
 */
function chordNameToNotesFromRoman(
  roman: string,
  tonic: string,
  mode: string,
  octave = 4
): number[] {
  // Map roman numerals to scale degrees
  const romanToDegree: Record<string, number> = {
    I: 1,
    II: 2,
    III: 3,
    IV: 4,
    V: 5,
    VI: 6,
    VII: 7,
    i: 1,
    ii: 2,
    iii: 3,
    iv: 4,
    v: 5,
    vi: 6,
    vii: 7,
  };

  // Extract base roman (remove 7, sus, etc.)
  const baseRoman = roman.replace(/7|sus|dim|aug/g, "").trim();
  const degree = romanToDegree[baseRoman] || 1;
  const is7th = roman.includes("7");
  const isMinor = baseRoman === baseRoman.toLowerCase() || baseRoman.includes("m");

  // Map tonic to semitone
  const noteMap: Record<string, number> = {
    C: 0,
    "C#": 1,
    Db: 1,
    D: 2,
    "D#": 3,
    Eb: 3,
    E: 4,
    F: 5,
    "F#": 6,
    Gb: 6,
    G: 7,
    "G#": 8,
    Ab: 8,
    A: 9,
    "A#": 10,
    Bb: 10,
    B: 11,
  };

  const tonicSemitone = noteMap[tonic] || 0;

  // Mode intervals (semitones from tonic)
  const modeIntervals: Record<string, number[]> = {
    ionian: [0, 2, 4, 5, 7, 9, 11],
    aeolian: [0, 2, 3, 5, 7, 8, 10],
    dorian: [0, 2, 3, 5, 7, 9, 10],
    phrygian: [0, 1, 3, 5, 7, 8, 10],
    lydian: [0, 2, 4, 6, 7, 9, 11],
    mixolydian: [0, 2, 4, 5, 7, 9, 10],
    locrian: [0, 1, 3, 5, 6, 8, 10],
  };

  const intervals = modeIntervals[mode] || modeIntervals.ionian;
  const degreeIdx = (degree - 1) % 7;
  const rootSemitone = (tonicSemitone + intervals[degreeIdx]) % 12;
  const rootMidi = (octave + 1) * 12 + rootSemitone;

  // Build chord notes directly from scale degrees
  const notes: number[] = [];

  // Root
  const rootNote = (octave + 1) * 12 + rootSemitone;
  notes.push(rootNote);

  // Third (degree + 2)
  const thirdIdx = (degreeIdx + 2) % 7;
  const thirdSemitone = (tonicSemitone + intervals[thirdIdx]) % 12;
  notes.push((octave + 1) * 12 + thirdSemitone);

  // Fifth (degree + 4)
  const fifthIdx = (degreeIdx + 4) % 7;
  const fifthSemitone = (tonicSemitone + intervals[fifthIdx]) % 12;
  notes.push((octave + 1) * 12 + fifthSemitone);

  // Seventh (degree + 6) if needed
  if (is7th) {
    const seventhIdx = (degreeIdx + 6) % 7;
    const seventhSemitone = (tonicSemitone + intervals[seventhIdx]) % 12;
    notes.push((octave + 1) * 12 + seventhSemitone);
  }

  return notes.sort((a, b) => a - b);
}

/**
 * Apply voicing to chord notes.
 * @param notes - Base chord notes
 * @param voicing - Voicing style ("root", "open", "drop2", "smooth")
 * @param inversion - Inversion number (0-3)
 * @param lowMidi - Lowest MIDI note (default 48 = C3)
 * @param highMidi - Highest MIDI note (default 72 = C5)
 * @returns Voiced chord notes
 */
function applyVoicing(
  notes: number[],
  voicing: string,
  inversion: number,
  lowMidi = 48,
  highMidi = 72
): number[] {
  if (notes.length === 0) return [];

  // Apply inversion
  let voiced = [...notes];
  for (let i = 0; i < inversion && i < notes.length; i++) {
    const root = voiced[0];
    voiced = voiced.slice(1);
    voiced.push(root + 12); // Move root up an octave
  }

  // Apply voicing style
  if (voicing === "open") {
    // Spread notes across wider range
    const spread = voiced.map((note, idx) => {
      const octaveOffset = Math.floor(idx / 3) * 12;
      return note + octaveOffset;
    });
    voiced = spread;
  } else if (voicing === "drop2") {
    // Drop second note an octave
    if (voiced.length >= 2) {
      voiced[1] -= 12;
    }
  } else if (voicing === "smooth") {
    // Keep notes close together (within one octave)
    // Already handled by inversion
  }
  // "root" voicing: keep as-is

  // Clamp to range
  return voiced
    .map((note) => {
      // Move to target range if needed
      while (note < lowMidi) note += 12;
      while (note > highMidi) note -= 12;
      return note;
    })
    .filter((note) => note >= lowMidi && note <= highMidi)
    .sort((a, b) => a - b);
}

/**
 * Render a chord event to note events for playback.
 * @param chordEvent - Chord event to render
 * @param clipStartBar - Starting bar of the clip
 * @param clipOffsetTicks - Clip offset in ticks
 * @param trackOffsetTicks - Track offset in ticks
 * @param ticksPerBar - Ticks per bar
 * @param tonic - Key tonic
 * @param mode - Mode
 * @param seed - Random seed for determinism
 * @param bpm - BPM for beat-to-tick conversion (optional, defaults to 120)
 * @returns Array of note events ready for Tone.js
 */
export function renderChordEventToNotes(
  chordEvent: ChordEvent,
  clipStartBar: number,
  clipOffsetTicks: number,
  trackOffsetTicks: number,
  ticksPerBar: number,
  tonic: string,
  mode: string,
  seed: number,
  bpm = 120
): Array<{
  pitch: number;
  start_tick: number;
  duration_tick: number;
  velocity: number;
}> {
  if (!chordEvent.is_enabled) {
    return [];
  }

  // Get base chord notes - prefer roman numeral if available (more reliable)
  const baseNotes = chordNameToNotes(
    chordEvent.chord_name,
    tonic,
    mode,
    4,
    chordEvent.roman_numeral
  );

  if (baseNotes.length === 0) {
    if (DEBUG) {
      console.warn(`[chordRender] No notes generated for chord:`, {
        chord_name: chordEvent.chord_name,
        roman: chordEvent.roman_numeral,
        tonic,
        mode,
      });
    }
    return [];
  }

  // Apply voicing
  const voicedNotes = applyVoicing(
    baseNotes,
    chordEvent.voicing || "root",
    chordEvent.inversion || 0,
    48, // C3
    72 // C5
  );

  if (voicedNotes.length === 0) {
    debugLog("No voiced notes after voicing/inversion", {
      baseNotes,
      voicing: chordEvent.voicing,
      inversion: chordEvent.inversion,
    });
    return [];
  }

  debugLog("Rendering chord", {
    chord_name: chordEvent.chord_name,
    roman: chordEvent.roman_numeral,
    baseNotes,
    voicedNotes,
    strum_beats: chordEvent.strum_beats,
    humanize_beats: chordEvent.humanize_beats,
  });

  // Calculate timing
  const baseStartTick =
    clipStartBar * ticksPerBar + chordEvent.start_tick + clipOffsetTicks + trackOffsetTicks;
  const durationTicks = chordEvent.duration_tick;
  const intensity = chordEvent.intensity || 0.85;

  // Convert strum/humanize from beats to ticks
  // Use beats fields if available, otherwise fall back to ms (for backward compatibility)
  let strumBeats = chordEvent.strum_beats ?? 0.0;
  let humanizeBeats = chordEvent.humanize_beats ?? 0.0;

  // Fallback: convert ms to beats if beats fields are not available
  if (strumBeats === 0 && chordEvent.strum_ms && chordEvent.strum_ms > 0) {
    strumBeats = (chordEvent.strum_ms / 1000.0) * (bpm / 60.0);
  }
  if (humanizeBeats === 0 && chordEvent.humanize_ms && chordEvent.humanize_ms > 0) {
    humanizeBeats = (chordEvent.humanize_ms / 1000.0) * (bpm / 60.0);
  }

  // Convert beats to ticks (1 beat = 1 quarter note = PPQ ticks)
  const ticksPerBeat = PPQ;
  const strumTicks = Math.round(strumBeats * ticksPerBeat);
  const humanizeTicks = Math.round(humanizeBeats * ticksPerBeat);

  // Deterministic random for strum order and humanization
  // Simple seeded random function
  function seededRandom(s: number): number {
    s = Math.sin(s) * 10000;
    return s - Math.floor(s);
  }

  const strumSeed = seed + chordEvent.id.charCodeAt(0);
  const humanizeSeed = seed + chordEvent.id.charCodeAt(chordEvent.id.length - 1);

  // Determine strum order
  const strumOrder = [...Array(voicedNotes.length).keys()];
  if (strumTicks > 0) {
    // Shuffle deterministically
    for (let i = strumOrder.length - 1; i > 0; i--) {
      const j = Math.floor(seededRandom(strumSeed + i) * (i + 1));
      [strumOrder[i], strumOrder[j]] = [strumOrder[j], strumOrder[i]];
    }
  }

  // Generate note events
  const noteEvents: Array<{
    pitch: number;
    start_tick: number;
    duration_tick: number;
    velocity: number;
  }> = [];

  for (let i = 0; i < strumOrder.length; i++) {
    const noteIdx = strumOrder[i];
    const pitch = voicedNotes[noteIdx];

    // Calculate start time with strum
    // Distribute notes evenly across strum duration
    let noteStart: number;
    if (strumBeats > 0 && strumOrder.length > 1) {
      const strumPosition = i / (strumOrder.length - 1);
      noteStart = baseStartTick + Math.round(strumPosition * strumTicks);
    } else {
      noteStart = baseStartTick;
    }

    // Apply humanization (clamp to chord bounds)
    if (humanizeBeats > 0) {
      const humanizeOffset = Math.round((seededRandom(humanizeSeed + i) - 0.5) * 2 * humanizeTicks);
      noteStart += humanizeOffset;
      // Clamp to chord bounds
      noteStart = Math.max(baseStartTick, Math.min(baseStartTick + durationTicks, noteStart));
    }

    // Calculate velocity with intensity
    let velocity = Math.round(100 * intensity);
    if (chordEvent.velocity_jitter > 0) {
      const jitter = Math.round(
        (seededRandom(humanizeSeed + i + 100) - 0.5) * 2 * chordEvent.velocity_jitter
      );
      velocity += jitter;
    }
    velocity = Math.max(1, Math.min(127, velocity));

    noteEvents.push({
      pitch,
      start_tick: noteStart,
      duration_tick: durationTicks,
      velocity,
    });
  }

  return noteEvents;
}
