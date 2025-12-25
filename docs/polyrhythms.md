# Polyrhythms

MIDINecromancer supports polyrhythms, allowing you to create complex rhythmic patterns where different tracks or clips run different cycle lengths simultaneously.

## What are Polyrhythms?

A polyrhythm occurs when two or more rhythms with different cycle lengths play simultaneously. Common examples include:

- **3:2** - Three beats against two (common in Latin music)
- **5:4** - Five beats against four (used in progressive music)
- **7:4** - Seven beats against four (creates a complex, shifting feel)

In MIDINecromancer, polyrhythms are defined using **Polyrhythm Profiles** that specify:
- **Steps**: The number of grid subdivisions in the cycle
- **Pulses**: The number of active onsets (hits) in the cycle
- **Cycle Beats**: The length of the cycle in beats
- **Rotation**: An offset to shift the pattern

## Creating Polyrhythm Profiles

### In the UI

1. Open a project in the Composer view
2. In the left panel, find the "Polyrhythms" section
3. Click "Create New..." or select an existing profile
4. Configure:
   - **Name**: A descriptive name for the profile
   - **Steps**: Grid subdivisions (e.g., 5 for a 5-step cycle)
   - **Pulses**: Number of hits (e.g., 3 for 3 hits in 5 steps)
   - **Rotation**: Shift the pattern (0 to steps-1)
   - **Cycle Beats**: How many beats the cycle spans (e.g., 4.0 beats)
   - **Swing**: Optional swing amount (0.0-1.0)

5. Click "Preview" to hear the pattern
6. Click "Save Profile" to persist it

### Example: 3:2 Clave Pattern

- Steps: 3
- Pulses: 2
- Cycle Beats: 2.0
- Rotation: 0

This creates a pattern where 2 hits occur over 3 steps, repeating every 2 beats.

### Example: 5:4 Techno Hi-Hat

- Steps: 5
- Pulses: 4
- Cycle Beats: 4.0
- Rotation: 0

This creates a 5-step pattern with 4 hits, fitting into 4 beats.

## How Cycle Beats + Steps/Pulses Map to Sound

The relationship between steps, pulses, and cycle beats determines the feel:

- **Steps** define the grid resolution within the cycle
- **Pulses** define which steps are active (using Euclidean rhythm algorithm)
- **Cycle Beats** define how long the cycle takes in musical time

For example:
- Steps=5, Pulses=3, Cycle Beats=4.0 means: 3 hits distributed over 5 steps, repeating every 4 beats
- Steps=7, Pulses=4, Cycle Beats=3.0 means: 4 hits over 7 steps, repeating every 3 beats (creates a 7:3 feel)

## LCM Alignment

When multiple polyrhythm cycles coexist in different tracks, MIDINecromancer uses **Least Common Multiple (LCM) alignment** for:

1. **Visualization**: The piano roll shows a grid aligned to the LCM of all active cycles
2. **Export**: MIDI events are aligned to the LCM grid to ensure stable tick positions

### Example

If you have:
- Track A: 3-step cycle
- Track B: 4-step cycle

The LCM is 12, so the visualization grid will show 12 subdivisions per cycle, and all events will align to this grid.

## Assigning Polyrhythms to Clips

Currently, polyrhythm generation is available through the API. Future UI updates will allow:

1. Selecting a clip
2. Choosing "Polyrhythm" as the rhythm mode
3. Assigning a polyrhythm profile
4. Generating notes based on the profile

## MIDI Export

Polyrhythm events are exported to MIDI with fractional beat positions converted to ticks using deterministic rounding (round half to even). This ensures:

- Stable tick positions across exports
- Correct playback in external MIDI software
- No drift or timing errors

The export uses a PPQ (ticks per quarter note) of 480, providing sufficient resolution for complex polyrhythms.

## Practical Examples

### 3:2 Clave (Latin feel)

```
Steps: 3
Pulses: 2
Cycle Beats: 2.0
Rotation: 0
```

### 5:4 Techno Pattern

```
Steps: 5
Pulses: 4
Cycle Beats: 4.0
Rotation: 0
```

### 7:4 Complex Pattern

```
Steps: 7
Pulses: 4
Cycle Beats: 4.0
Rotation: 0
```

This creates a shifting, complex feel where 4 hits are distributed over 7 steps within 4 beats.

## API Usage

### Create a Profile

```bash
POST /api/v1/polyrhythms
{
  "name": "3:2 Clave",
  "steps": 3,
  "pulses": 2,
  "cycle_beats": 2.0,
  "rotation": 0
}
```

### Preview Events

```bash
POST /api/v1/polyrhythms/preview/{project_id}
{
  "steps": 5,
  "pulses": 3,
  "cycle_beats": 4.0,
  "rotation": 0
}
```

### Assign to Clip

Set `grid_mode` to `"polyrhythm"` and `polyrhythm_profile_id` to the profile ID when creating or updating a clip.

## Technical Details

- **Euclidean Algorithm**: Polyrhythm patterns use the Bjorklund algorithm to evenly distribute pulses across steps
- **Deterministic**: Same seed + same profile = same pattern
- **Fractional Beats**: Cycle beats can be fractional (e.g., 3.5 beats) for more complex timings
- **Swing Support**: Optional swing can be applied to off-beat steps

