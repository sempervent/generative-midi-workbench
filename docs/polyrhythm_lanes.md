# Polyrhythm Lanes (Multi-Cycle)

MIDINecromancer supports **multi-lane polyrhythms**, allowing a single clip to run multiple independent rhythmic cycles simultaneously. This enables complex, layered rhythms where different instruments (kick, snare, hi-hat, etc.) each follow their own polyrhythmic pattern, all aligned to a shared LCM grid.

## What are Polyrhythm Lanes?

A **polyrhythm lane** is an independent rhythmic cycle within a clip. Each lane has:
- A **polyrhythm profile** (steps, pulses, cycle beats, rotation, swing)
- A **MIDI pitch** (which note to play)
- A **velocity** (how hard to hit)
- **Mute/Solo** controls
- A **seed offset** (for deterministic variation)

Multiple lanes in the same clip run simultaneously, creating complex polyrhythmic textures.

### Example: 3-Lane Polyrhythm

```
Lane 1 (Kick):  3:2 pattern (3 steps, 2 pulses, 2 beats)
Lane 2 (Snare): 4:3 pattern (4 steps, 3 pulses, 4 beats)
Lane 3 (Hat):   7:4 pattern (7 steps, 4 pulses, 4 beats)
```

All three lanes play at once, creating a rich, shifting rhythm.

## LCM Alignment

When multiple lanes coexist, MIDINecromancer calculates the **Least Common Multiple (LCM)** of all lane step counts to create a unified grid for:

1. **Visualization**: The piano roll shows a grid aligned to the LCM
2. **Playback**: Events are scheduled on the LCM grid
3. **Export**: MIDI events are aligned to ensure stable tick positions

### Example LCM Calculation

If you have lanes with:
- Lane 1: 3 steps
- Lane 2: 4 steps
- Lane 3: 5 steps

The LCM is 60 (3 × 4 × 5), so the visualization grid will show 60 subdivisions per cycle.

## Creating Multi-Lane Polyrhythms

### In the UI

1. **Create or select a clip**
2. **Set grid mode to `polyrhythm_multi`** (or use legacy `polyrhythm` mode)
3. **Add lanes**:
   - Click "+ Add Lane"
   - Select a polyrhythm profile
   - Configure pitch, velocity, role
   - Adjust seed offset for variation
4. **Arrange lanes**:
   - Use ↑/↓ buttons to reorder
   - Set mute/solo as needed
5. **Preview**:
   - The stacked lane grid shows all lanes aligned to the LCM
   - Each lane's ratio is displayed
   - Active steps are highlighted

### Lane Properties

- **Profile**: The polyrhythm pattern (steps, pulses, cycle beats)
- **Pitch**: MIDI note (0-127)
- **Velocity**: Note velocity (1-127)
- **Role**: Optional label (kick, snare, hat, etc.)
- **Seed Offset**: Additional seed value for deterministic variation
- **Mute**: Silence this lane
- **Solo**: Play only this lane (and other soloed lanes)

## Determinism Guarantees

Multi-lane polyrhythms are **fully deterministic**. Given the same:
- Project seed
- Clip ID
- Lane IDs and order
- Lane configurations (profiles, pitches, velocities, seed offsets)
- BPM, time signature, bars

...you will get **identical events** every time.

### Seed Generation

Each lane uses a deterministic seed derived from:
```
lane_seed = base_seed XOR hash(clip_id) XOR hash(lane_id) XOR seed_offset
```

This ensures:
- Same inputs = same outputs
- Different lanes = different patterns (even with same profile)
- Seed offsets allow controlled variation

## Mute and Solo Logic

- **Mute**: A muted lane produces no events
- **Solo**: If any lane is soloed, only soloed lanes play
- **Normal**: If no lanes are soloed, all non-muted lanes play

## API Usage

### List Lanes

```bash
GET /api/v1/clips/{clip_id}/polyrhythm-lanes
```

### Create Lane

```bash
POST /api/v1/clips/{clip_id}/polyrhythm-lanes
{
  "polyrhythm_profile_id": "...",
  "lane_name": "Kick",
  "pitch": 36,
  "velocity": 100,
  "instrument_role": "kick",
  "order_index": 0,
  "seed_offset": 0
}
```

### Preview Lanes

```bash
POST /api/v1/polyrhythms/preview-lanes?project_id=...&clip_id=...
```

Returns:
- `lanes`: Lane metadata with ratios
- `events`: Merged event list (sorted by tick, order, pitch)
- `grid_spec`: LCM grid specification

## Legacy Mode Support

Clips created with the old single-profile polyrhythm mode are automatically migrated:
- Existing `polyrhythm_profile_id` → creates a default lane
- Grid mode `polyrhythm` → works with legacy profile
- Grid mode `polyrhythm_multi` → uses lanes

## Practical Examples

### Techno Pattern

```
Lane 1 (Kick):  4:4 (steady quarter notes)
Lane 2 (Hat):   5:4 (5 steps, 4 pulses, 4 beats)
Lane 3 (Perc):  7:4 (7 steps, 4 pulses, 4 beats)
```

Creates a driving techno feel with shifting hi-hat and percussion patterns over a steady kick.

### Latin Clave

```
Lane 1 (Clave): 3:2 (classic clave pattern)
Lane 2 (Bass):  4:3 (bass line)
Lane 3 (Perc):  5:4 (shaker)
```

Traditional Latin rhythm with multiple interlocking patterns.

### Complex Polyrhythm

```
Lane 1: 3:2 (2 beats)
Lane 2: 4:3 (3 beats)
Lane 3: 5:4 (4 beats)
Lane 4: 7:5 (5 beats)
```

Creates a complex, shifting polyrhythm where patterns phase in and out of alignment.

## MIDI Export

When exporting, lanes are rendered to notes using the same deterministic algorithm. The exported MIDI file contains all lane events aligned to the LCM grid, ensuring:
- Stable tick positions
- Correct playback in external software
- No timing drift

## Technical Details

- **Event Sorting**: Events are sorted by `(start_tick, order_index, pitch)` for stable ordering
- **Humanization**: Per-lane humanization (if enabled) is applied deterministically
- **Swing**: Per-profile swing is applied to off-beat steps
- **Bounds Checking**: Events are clamped to clip boundaries

## Best Practices

1. **Start Simple**: Begin with 2-3 lanes to understand the interaction
2. **Use Seed Offsets**: Different seed offsets create variation while maintaining determinism
3. **Leverage Roles**: Use instrument roles to organize lanes (kick, snare, hat, etc.)
4. **Test Export**: Always verify MIDI export sounds correct in external software
5. **LCM Awareness**: Very high LCM values (e.g., 60+) may create dense grids; consider simplifying

