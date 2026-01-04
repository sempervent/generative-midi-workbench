/**
 * Unified playback plan builder.
 *
 * This module creates a single, unified event list for Tone.js playback
 * that includes all notes (drums, bass, melody) and rendered chord events.
 *
 * Timing basis:
 * - PPQ = 480 ticks per quarter note (1 beat)
 * - 1 bar = (time_signature_num * 4) / time_signature_den * PPQ ticks
 * - All events use the same tick basis for consistency
 */

import type { Arrangement, PlaybackRange } from "../types";
import { renderChordEventToNotes } from "./chordRender";

const PPQ = 480; // Pulses per quarter note - matches backend and MIDI standard

export interface PlaybackNoteEvent {
  startTick: number; // Absolute tick from project start (0)
  durationTick: number;
  midi: number;
  velocity: number;
  trackKind: "drums" | "chords" | "bass" | "melody";
  sourceId: string; // note.id or chord_event.id
  channel?: number;
}

export interface PlaybackPlan {
  bpm: number;
  ppq: number;
  startBar: number;
  endBar: number;
  events: PlaybackNoteEvent[];
}

import { debugLog as debugLogUtil } from "../utils/debug";

function debugLog(...args: any[]) {
  debugLogUtil("playback", ...args);
}

/**
 * Build a unified playback plan from arrangement data.
 *
 * This function:
 * 1. Loads all clips/notes/chord events for the selected range
 * 2. Renders chord events into note events
 * 3. Merges all note events
 * 4. Sorts deterministically
 * 5. Returns the array ready for Tone.Part
 */
export function buildPlaybackPlan(
  arrangement: Arrangement,
  bpm: number,
  range: PlaybackRange
): PlaybackPlan {
  // Determine loop range
  let startBar: number;
  let endBar: number;

  if (range.kind === "project") {
    // Calculate project length from all clips
    let maxBar = arrangement.bars;
    for (const track of arrangement.tracks) {
      for (const clip of track.clips) {
        const clipEndBar = clip.start_bar + clip.length_bars;
        if (clipEndBar > maxBar) {
          maxBar = clipEndBar;
        }
      }
    }
    startBar = 0;
    endBar = maxBar;
  } else {
    startBar = range.startBar;
    endBar = range.endBar;
  }

  // Validate range
  if (endBar <= startBar) {
    debugLog("Invalid range:", { startBar, endBar });
    return {
      bpm,
      ppq: PPQ,
      startBar,
      endBar,
      events: [],
    };
  }

  // Calculate ticks per bar
  const quarterNotesPerBar = (arrangement.time_signature_num * 4) / arrangement.time_signature_den;
  const ticksPerBar = quarterNotesPerBar * PPQ;

  debugLog("Building playback plan", {
    startBar,
    endBar,
    ticksPerBar,
    bpm,
    trackCount: arrangement.tracks.length,
  });

  // Filter tracks based on mute/solo logic
  const hasAnyTrackSolo = arrangement.tracks.some((t) => t.is_soloed);
  const filteredTracks = arrangement.tracks.filter((track) => {
    if (track.is_muted) {
      debugLog("Track filtered (muted):", track.id, track.name);
      return false;
    }
    if (hasAnyTrackSolo && !track.is_soloed) {
      debugLog("Track filtered (solo active, not soloed):", track.id, track.name);
      return false;
    }
    return true;
  });

  debugLog("Track filtering:", {
    totalTracks: arrangement.tracks.length,
    filteredTracks: filteredTracks.length,
    hasAnySolo: hasAnyTrackSolo,
    mutedTracks: arrangement.tracks.filter((t) => t.is_muted).length,
    soloedTracks: arrangement.tracks.filter((t) => t.is_soloed).length,
  });

  const allEvents: PlaybackNoteEvent[] = [];
  let chordEventCount = 0;
  let chordNoteCount = 0;

  // Process each track
  for (const track of filteredTracks) {
    // Filter clips based on mute/solo
    const hasAnyClipSolo = track.clips.some((c) => c.is_soloed);
    const filteredClips = track.clips.filter((clip) => {
      if (clip.is_muted) {
        debugLog("Clip filtered (muted):", clip.id, clip.start_bar);
        return false;
      }
      if (hasAnyClipSolo && !clip.is_soloed) {
        debugLog("Clip filtered (solo active, not soloed):", clip.id, clip.start_bar);
        return false;
      }
      return true;
    });

    debugLog(`Track ${track.name} clip filtering:`, {
      totalClips: track.clips.length,
      filteredClips: filteredClips.length,
      hasAnySolo: hasAnyClipSolo,
    });

    for (const clip of filteredClips) {
      const clipStartBar = clip.start_bar;
      const clipEndBar = clip.start_bar + clip.length_bars;

      // Skip if clip is completely outside range
      if (clipEndBar <= startBar || clipStartBar >= endBar) {
        continue;
      }

      // Get offsets
      const clipOffset = clip.start_offset_ticks || 0;
      const trackOffset = track.start_offset_ticks || 0;

      // Process regular notes
      for (const note of clip.notes) {
        // Calculate absolute tick position
        const baseTick = clipStartBar * ticksPerBar + note.start_tick;
        const absoluteTick = baseTick + clipOffset + trackOffset;

        // Check if note is within range
        const noteStartBar = absoluteTick / ticksPerBar;
        const noteEndBar = noteStartBar + note.duration_tick / ticksPerBar;

        if (noteEndBar <= startBar || noteStartBar >= endBar) {
          continue;
        }

        // Clamp to range
        const rangeStartTick = startBar * ticksPerBar;
        const rangeEndTick = endBar * ticksPerBar;
        const clampedStartTick = Math.max(absoluteTick, rangeStartTick);
        let clampedDurationTick = note.duration_tick;

        // Adjust duration if note extends beyond range
        if (absoluteTick + note.duration_tick > rangeEndTick) {
          clampedDurationTick = rangeEndTick - clampedStartTick;
        }
        if (clampedDurationTick <= 0) continue;

        allEvents.push({
          startTick: clampedStartTick,
          durationTick: clampedDurationTick,
          midi: note.pitch,
          velocity: note.velocity,
          trackKind: track.role as "drums" | "chords" | "bass" | "melody",
          sourceId: note.id,
          channel: track.midi_channel,
        });
      }

      // Process chord events
      if (clip.chord_events && clip.chord_events.length > 0) {
        const chordEventsInRange = clip.chord_events.filter((ce) => {
          if (!ce.is_enabled) return false;
          const chordStartBar = clipStartBar + ce.start_tick / ticksPerBar;
          const chordEndBar = chordStartBar + ce.duration_tick / ticksPerBar;
          return chordEndBar > startBar && chordStartBar < endBar;
        });

        chordEventCount += chordEventsInRange.length;

        // Render chord events to notes
        for (const chordEvent of chordEventsInRange) {
          const renderedNotes = renderChordEventToNotes(
            chordEvent,
            clipStartBar,
            clipOffset,
            trackOffset,
            ticksPerBar,
            arrangement.key_tonic,
            arrangement.mode,
            arrangement.seed,
            bpm
          );

          chordNoteCount += renderedNotes.length;

          // Convert rendered notes to playback events
          for (const note of renderedNotes) {
            // note.start_tick is already absolute (from renderChordEventToNotes)
            const absoluteTick = note.start_tick;

            // Check if note is within range
            const noteStartBar = absoluteTick / ticksPerBar;
            const noteEndBar = noteStartBar + note.duration_tick / ticksPerBar;

            if (noteEndBar <= startBar || noteStartBar >= endBar) {
              continue;
            }

            // Clamp to range
            const rangeStartTick = startBar * ticksPerBar;
            const rangeEndTick = endBar * ticksPerBar;
            const clampedStartTick = Math.max(absoluteTick, rangeStartTick);
            let clampedDurationTick = note.duration_tick;

            // Adjust duration if note extends beyond range
            if (absoluteTick + note.duration_tick > rangeEndTick) {
              clampedDurationTick = rangeEndTick - clampedStartTick;
            }
            if (clampedDurationTick <= 0) continue;

            allEvents.push({
              startTick: clampedStartTick,
              durationTick: clampedDurationTick,
              midi: note.pitch,
              velocity: note.velocity,
              trackKind: "chords",
              sourceId: chordEvent.id,
              channel: track.midi_channel,
            });
          }
        }
      }
    }
  }

  // Sort events by start tick (deterministic)
  allEvents.sort((a, b) => {
    if (a.startTick !== b.startTick) {
      return a.startTick - b.startTick;
    }
    // If same start tick, sort by midi (lower notes first)
    return a.midi - b.midi;
  });

  // Debug logging
  const debugEnabled =
    import.meta.env.DEV || localStorage.getItem("midinecromancer:debug:playback") === "true";
  if (debugEnabled) {
    const minTick = allEvents.length > 0 ? Math.min(...allEvents.map((e) => e.startTick)) : 0;
    const maxTick =
      allEvents.length > 0 ? Math.max(...allEvents.map((e) => e.startTick + e.durationTick)) : 0;
    const chordEvents = allEvents.filter((e) => e.trackKind === "chords");
    const firstChordNotes = chordEvents.slice(0, 10).map((e) => ({
      startTick: e.startTick,
      durationTick: e.durationTick,
      midi: e.midi,
      velocity: e.velocity,
      sourceId: e.sourceId,
    }));

    debugLog("Playback plan built", {
      totalEvents: allEvents.length,
      chordEventCount,
      chordNoteCount,
      chordEventsInPlan: chordEvents.length,
      minTick,
      maxTick,
      firstChordNotes,
    });
  }

  return {
    bpm,
    ppq: PPQ,
    startBar,
    endBar,
    events: allEvents,
  };
}
