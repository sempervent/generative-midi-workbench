import * as Tone from "tone";
import type { Arrangement, PlaybackRange } from "../types";
import { type PlaybackNoteEvent, buildPlaybackPlan } from "./playbackPlan";
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

    // Ensure AudioContext is started (only on user gesture)
    const { ensureAudioStarted } = await import("../audio/ensureAudio");
    await ensureAudioStarted();
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

    // Build unified playback plan (includes all notes + rendered chords)
    const plan = buildPlaybackPlan(arrangement, bpm, range);

    if (plan.events.length === 0) {
      console.warn("No events in playback plan");
      cleanup();
      isPlaying = false;
      return;
    }

    // Convert playback plan events to Tone.js format
    const PPQ = plan.ppq;
    const quarterNotesPerBar =
      (arrangement.time_signature_num * 4) / arrangement.time_signature_den;
    const ticksPerBar = quarterNotesPerBar * PPQ;

    const toneEvents: Array<{ time: string; note: any }> = [];

    for (const event of plan.events) {
      // Calculate relative tick from loop start
      const loopStartTick = plan.startBar * ticksPerBar;
      const relativeTick = event.startTick - loopStartTick;

      // Skip if outside range (shouldn't happen, but double-check)
      if (relativeTick < 0 || relativeTick >= (plan.endBar - plan.startBar) * ticksPerBar) {
        continue;
      }

      // Convert ticks to Tone.js musical time format: "bars:beats:sixteenths"
      const relativeBar = Math.floor(relativeTick / ticksPerBar);
      const ticksInBar = relativeTick % ticksPerBar;
      const totalSixteenths = Math.floor(ticksInBar / 120);
      const beats = Math.floor(totalSixteenths / 4);
      const remainingSixteenths = totalSixteenths % 4;
      const time = `${relativeBar}:${beats}:${remainingSixteenths}`;

      const durationBars = event.durationTick / ticksPerBar;

      if (event.trackKind === "drums") {
        toneEvents.push({
          time,
          note: {
            type: "drum",
            pitch: event.midi,
            velocity: event.velocity / 127,
            duration: Math.max(durationBars, 0.01),
          },
        });
      } else {
        const freq = Tone.Frequency(event.midi, "midi").toFrequency();
        toneEvents.push({
          time,
          note: {
            type: "note",
            freq,
            velocity: event.velocity / 127,
            duration: Math.max(durationBars, 0.01),
          },
        });
      }
    }

    // Sort events by time
    toneEvents.sort((a, b) => {
      const aParts = a.time.split(":").map(Number);
      const bParts = b.time.split(":").map(Number);
      if (aParts[0] !== bParts[0]) return aParts[0] - bParts[0];
      if (aParts[1] !== bParts[1]) return aParts[1] - bParts[1];
      return aParts[2] - bParts[2];
    });

    // Ensure no duplicate times
    for (let i = 1; i < toneEvents.length; i++) {
      if (toneEvents[i].time === toneEvents[i - 1].time) {
        const parts = toneEvents[i].time.split(":").map(Number);
        parts[2] += 1;
        if (parts[2] >= 4) {
          parts[2] = 0;
          parts[1] += 1;
          if (parts[1] >= 4) {
            parts[1] = 0;
            parts[0] += 1;
          }
        }
        toneEvents[i].time = `${parts[0]}:${parts[1]}:${parts[2]}`;
      }
    }

    // Create single Tone.Part for all events
    const part = new Tone.Part((time, event) => {
      const durationStr = `${event.note.duration}m`;
      if (event.note.type === "drum") {
        drumSynth?.triggerAttackRelease(event.note.pitch, durationStr, time, event.note.velocity);
      } else {
        synth?.triggerAttackRelease(event.note.freq, durationStr, time, event.note.velocity);
      }
    }, toneEvents);

    part.start(0);
    scheduledParts.push(part);

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
