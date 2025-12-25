# Playback Architecture

## Current Playback Architecture

### Event Scheduling

The current playback system uses **one-shot absolute time scheduling** via `triggerAttackRelease()`:

1. **Time Conversion**: Events are converted from ticks to absolute seconds:
   - `clipStartSeconds = (clip.start_bar * ticksPerBar * secondsPerTick) + scheduleId`
   - `startTime = clipStartSeconds + note.start_tick * secondsPerTick`
   - Where `scheduleId = Tone.now()` and `secondsPerTick = 60 / (bpm * PPQ)`

2. **Scheduling Method**: Each note is scheduled using:
   ```typescript
   synth.triggerAttackRelease(freq, duration, startTime, velocity)
   ```
   This creates a one-time event at an absolute time.

3. **Stop Mechanism**: Playback stops via `setTimeout` after calculating total duration:
   ```typescript
   const totalSeconds = totalBars * (60 / bpm) * (timeSigNum / timeSigDen) * 4
   setTimeout(() => stop(), totalSeconds * 1000)
   ```

### BPM and Time Signature Handling

- BPM is set via `Tone.Transport.bpm.value = bpm`
- Time signature is used only for tick calculations (not set in Transport)
- PPQ (Pulses Per Quarter Note) = 480 ticks per quarter note

### Canonical Time Unit

The canonical unit is **ticks**:
- All events have `start_tick` and `duration_tick` in ticks
- Ticks are converted to seconds for Tone.js scheduling
- One quarter note = 480 ticks (PPQ)

### Current Stop Behavior

Playback stops when:
1. User clicks stop button → calls `stop()` which:
   - Stops Transport
   - Cancels scheduled events
   - Disposes synths
2. Automatic stop after project duration (via setTimeout)
3. No looping currently implemented

### Limitations for Looping

The current architecture has limitations for looping:
- Absolute time scheduling doesn't loop automatically
- `setTimeout`-based stop doesn't work with loops
- No region filtering (plays entire project)
- Events scheduled beyond loop end will still trigger

## Looped Playback Architecture (New)

### Event Scheduling with Looping

The new architecture uses **Tone.Part** for loop-safe scheduling:

1. **Musical Time**: Events are scheduled in musical time (bars:beats:sixteenths)
2. **Tone.Part**: Each track/clip uses a `Tone.Part` that loops automatically
3. **Transport Loop**: `Tone.Transport.loop` controls looping at the transport level
4. **Region Filtering**: Events are filtered by range before scheduling

### Loop Management

- **Loop Points**: Set via `Tone.Transport.loopStart` and `Tone.Transport.loopEnd` in musical time
- **Loop Toggle**: `Tone.Transport.loop = true/false`
- **Position Reset**: When starting region playback, position is set to `loopStart`

### Range Types

- **Project**: Loops over entire computed project length
- **Bars**: Loops over a specific bar range (startBar to endBar, exclusive)

### Keyboard Shortcuts

- **L**: Toggle loop on/off

## Looped Playback (New)

### Overview

The playback system now supports looping with two modes:
1. **Project Loop**: Loops over the entire computed project length
2. **Region Loop**: Loops over a selected bar range

### Loop Controls

- **Loop Toggle Button**: Click to enable/disable looping (default: enabled)
- **Keyboard Shortcut**: Press `L` to toggle loop on/off
- **Range Selector**: Choose between "Project" or "Bars" playback
- **Bar Range Inputs**: When "Bars" is selected, set start and end bars

### Implementation Details

**Scheduling Strategy**: Uses `Tone.Part` for loop-safe event scheduling
- Events are scheduled in musical time (bars:beats:sixteenths)
- Each clip gets its own `Tone.Part` that loops automatically
- Transport loop points are set via `Tone.Transport.loopStart` and `Tone.Transport.loopEnd`

**Range Filtering**: Events are filtered by range before scheduling
- Only notes/chords within the selected range are scheduled
- Clips that don't overlap with the range are skipped entirely

**Loop Behavior**:
- When loop is enabled: Transport loops continuously at loop points
- When loop is disabled: Plays once and stops at range end
- Loop points are aligned to bar boundaries
- Position resets to `loopStart` when starting region playback

### State Persistence

Loop preferences are saved to `localStorage`:
- `loopEnabled`: Whether looping is enabled
- `range`: The selected range (project or bars with start/end)

### Compatibility

- Works with all event types: notes, chords, bass, polyrhythm lanes
- Does not affect preview/audition playback (uses separate scheduling)
- Maintains determinism: same events produce same playback

