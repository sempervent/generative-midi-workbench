import * as Tone from "tone";
import type { Arrangement, PlaybackRange } from "../types";
import { computeProjectLengthBars, setTransportLoop } from "./transportLoop";

let synth: Tone.PolySynth | null = null;
let drumSynth: Tone.MembraneSynth | null = null;
let scheduledParts: Tone.Part[] = [];
let isPlaying = false;
let currentScheduleId: number | null = null;

export function usePlayback() {
  async function start(
    arrangement: Arrangement,
    bpm: number,
    loopEnabled = true,
    range: PlaybackRange = { kind: "project" }
  ) {
    // Stop any existing playback first
    if (isPlaying) {
      stop();
    }

    // Clean up existing synths and parts
    cleanup();

    await Tone.start();
    Tone.Transport.stop();
    Tone.Transport.cancel();
    Tone.Transport.bpm.value = bpm;
    isPlaying = true;

    // Initialize synths
    synth = new Tone.PolySynth(Tone.Synth).toDestination();
    drumSynth = new Tone.MembraneSynth().toDestination();

    // Determine loop range
    let startBar: number;
    let endBar: number;

    if (range.kind === "project") {
      const projectLength = computeProjectLengthBars(arrangement);
      startBar = 0;
      endBar = projectLength;
    } else {
      startBar = range.startBar;
      endBar = range.endBar;
    }

    // Validate range
    if (endBar <= startBar) {
      console.error(`Invalid playback range: endBar (${endBar}) must be > startBar (${startBar})`);
      isPlaying = false;
      return;
    }

    // Set transport loop
    setTransportLoop(loopEnabled, startBar, endBar, arrangement.time_signature_num);

    // Set transport position to loop start
    Tone.Transport.position = `${startBar}:0:0`;

    // Build schedule for the range
    const PPQ = 480;
    const quarterNotesPerBar =
      (arrangement.time_signature_num * 4) / arrangement.time_signature_den;
    const ticksPerBar = quarterNotesPerBar * PPQ;

    // Filter tracks and clips
    const filteredTracks = arrangement.tracks.filter((track) => !track.is_muted);

    let hasNotes = false;

    // Schedule events using Tone.Part for loop-safe playback
    for (const track of filteredTracks) {
      // Filter clips based on mute/solo
      const hasAnyClipSolo = track.clips.some((c) => c.is_soloed);
      const filteredClips = track.clips.filter((clip) => {
        if (clip.is_muted) return false;
        if (hasAnyClipSolo && !clip.is_soloed) return false;
        return true;
      });

      for (const clip of filteredClips) {
        // Check if clip overlaps with playback range
        const clipStartBar = clip.start_bar;
        const clipEndBar = clip.start_bar + clip.length_bars;

        // Skip if clip is completely outside range
        if (clipEndBar <= startBar || clipStartBar >= endBar) {
          continue;
        }

        // Filter notes that are within the playback range
        // Note: start_tick is relative to clip start, so we need to calculate absolute position
        const notesInRange = clip.notes.filter((note) => {
          const noteStartBar = clipStartBar + note.start_tick / ticksPerBar;
          const noteEndBar = noteStartBar + note.duration_tick / ticksPerBar;
          // Include note if any part overlaps with range
          return noteEndBar > startBar && noteStartBar < endBar;
        });

        if (notesInRange.length === 0) {
          continue;
        }

        hasNotes = true;

        // Create events for this clip in musical time
        const events: Array<{ time: string; note: any }> = [];

        for (const note of notesInRange) {
          // Calculate absolute tick position
          const absoluteTick = clipStartBar * ticksPerBar + note.start_tick;

          // Calculate relative tick from loop start
          const loopStartTick = startBar * ticksPerBar;
          const relativeTick = absoluteTick - loopStartTick;

          // Skip if outside range (shouldn't happen due to filter, but double-check)
          if (relativeTick < 0 || relativeTick >= (endBar - startBar) * ticksPerBar) {
            continue;
          }

          // Convert ticks to Tone.js musical time format: "bars:beats:sixteenths"
          // PPQ = 480 ticks per quarter note
          // 1 sixteenth = 480 / 4 = 120 ticks
          // For Tone.js: beats are quarter notes (for 4/4), sixteenths are within the beat
          const relativeBar = Math.floor(relativeTick / ticksPerBar);
          const ticksInBar = relativeTick % ticksPerBar;
          
          // Convert ticks to sixteenths (120 ticks per sixteenth)
          const totalSixteenths = Math.floor(ticksInBar / 120);
          // In Tone.js format, beats are quarter notes, so 4 sixteenths per beat
          const beats = Math.floor(totalSixteenths / 4);
          const remainingSixteenths = totalSixteenths % 4;

          // Format as "bars:beats:sixteenths" (Tone.js format)
          const time = `${relativeBar}:${beats}:${remainingSixteenths}`;

          const durationTicks = note.duration_tick;
          const durationBars = durationTicks / ticksPerBar;

          if (track.role === "drums") {
            events.push({
              time,
              note: {
                type: "drum",
                pitch: note.pitch,
                velocity: note.velocity / 127,
                duration: Math.max(durationBars, 0.01), // Minimum duration
              },
            });
          } else {
            const freq = Tone.Frequency(note.pitch, "midi").toFrequency();
            events.push({
              time,
              note: {
                type: "note",
                freq,
                velocity: note.velocity / 127,
                duration: Math.max(durationBars, 0.01), // Minimum duration
              },
            });
          }
        }

        // Create Tone.Part for this clip
        // Sort events by time to ensure strictly increasing times
        if (events.length > 0) {
          // Sort by time string (lexicographic sort works for "bars:beats:sixteenths")
          events.sort((a, b) => {
            const aParts = a.time.split(":").map(Number);
            const bParts = b.time.split(":").map(Number);
            // Compare bars, then beats, then sixteenths
            if (aParts[0] !== bParts[0]) return aParts[0] - bParts[0];
            if (aParts[1] !== bParts[1]) return aParts[1] - bParts[1];
            return aParts[2] - bParts[2];
          });

          // Ensure no duplicate times by adding tiny offsets if needed
          // This handles cases where multiple notes start at the exact same tick (e.g., chords)
          for (let i = 1; i < events.length; i++) {
            if (events[i].time === events[i - 1].time) {
              // Add 1 sixteenth note offset
              const parts = events[i].time.split(":").map(Number);
              parts[2] += 1; // Add one sixteenth
              if (parts[2] >= 4) {
                // If we exceed 4 sixteenths per beat, move to next beat
                parts[2] = 0;
                parts[1] += 1;
                // Check if we exceed beats per bar (depends on time sig, but 4 is safe for most)
                if (parts[1] >= 4) {
                  parts[1] = 0;
                  parts[0] += 1;
                }
              }
              events[i].time = `${parts[0]}:${parts[1]}:${parts[2]}`;
            }
          }

          const part = new Tone.Part((time, event) => {
            // Convert duration from bars to Tone time string
            const durationStr = `${event.note.duration}m`;
            if (event.note.type === "drum") {
              drumSynth?.triggerAttackRelease(
                event.note.pitch,
                durationStr,
                time,
                event.note.velocity
              );
            } else {
              synth?.triggerAttackRelease(event.note.freq, durationStr, time, event.note.velocity);
            }
          }, events);

          // Start part at 0 - events are scheduled at absolute times
          // Transport loop will handle repetition
          part.start(0);
          scheduledParts.push(part);
        }

        // Schedule chord events if present
        if (clip.chord_events && clip.chord_events.length > 0) {
          const chordEventsInRange = clip.chord_events.filter((ce) => {
            const chordStartBar = clipStartBar + ce.start_tick / ticksPerBar;
            return chordStartBar >= startBar && chordStartBar < endBar;
          });

          // Chord events are currently represented as notes in the arrangement
          // If chords need special rendering/voicing, add it here
          // For now, they're handled via the notes array
        }
      }
    }

    if (!hasNotes) {
      console.warn("No notes to play in range");
      cleanup();
      isPlaying = false;
      return;
    }

    // Start transport
    const scheduleId = Tone.now();
    currentScheduleId = scheduleId;
    Tone.Transport.start();

    // If loop is disabled, stop after range ends
    if (!loopEnabled) {
      const rangeBars = endBar - startBar;
      const rangeSeconds =
        rangeBars *
        (60 / bpm) *
        (arrangement.time_signature_num / arrangement.time_signature_den) *
        4;
      setTimeout(() => {
        if (currentScheduleId === scheduleId) {
          stop();
        }
      }, rangeSeconds * 1000);
    }
  }

  function stop() {
    if (!isPlaying) return;

    Tone.Transport.stop();
    cleanup();
    isPlaying = false;
    currentScheduleId = null;
  }

  function cleanup() {
    Tone.Transport.cancel();

    // Dispose all scheduled parts
    for (const part of scheduledParts) {
      try {
        part.stop();
        part.dispose();
      } catch (e) {
        // Ignore errors
      }
    }
    scheduledParts = [];

    if (synth) {
      try {
        synth.releaseAll();
      } catch (e) {
        // Ignore errors
      }
      synth.dispose();
      synth = null;
    }
    if (drumSynth) {
      drumSynth.dispose();
      drumSynth = null;
    }
  }

  function getIsPlaying() {
    return isPlaying;
  }

  return {
    start,
    stop,
    getIsPlaying,
  };
}
