# Drum Generation

MIDINecromancer provides producer-grade drum generation with extensive customization options.

## Generation Parameters

### Style
- **boom_bap**: Classic hip-hop feel (kick on 1 and 3, snare on 2 and 4)
- **trap**: Modern trap patterns (more syncopated, heavier 808s)
- **drill**: UK drill style (aggressive, dense patterns)
- **lofi**: Lo-fi hip-hop (sparse, relaxed)
- **minimal**: Minimal patterns (very sparse)

### Core Parameters

- **Density** (0-1): Overall hit density
  - 0.3 = sparse
  - 0.7 = medium (default)
  - 1.0 = dense
- **Swing** (0-1): Swing amount
  - 0.0 = straight
  - 0.5 = triplet feel
  - 1.0 = heavy swing
- **Variation Intensity** (0-1): Bar-to-bar variation
  - 0.0 = identical every bar
  - 0.3 = subtle variation (default)
  - 1.0 = high variation

### Advanced Parameters

- **Fill Probability** (0-1): Probability of fill in last bar
  - Adds rapid snare/kick hits in last half-bar
  - Creates dynamic endings
- **Syncopation** (0-1): Syncopation amount
  - Shifts off-beat hits forward
  - Creates more groove and feel
- **Ghost Note Probability** (0-1): Probability of ghost notes
  - Quiet snares between main snares
  - Adds texture and groove
- **Hat Subdivision**: Hi-hat subdivision (1/8, 1/16, 1/32)
  - Controls hi-hat grid resolution
- **Pause Probability** (0-1): Probability of pausing per bar
  - Creates dropouts for dynamics
  - Can target kick, snare, or all

### Hi-Hat Modes

- **straight_8**: Straight 8th notes
- **straight_16**: Straight 16th notes (default)
- **skip_step**: Syncopated, skips some steps
- **roll**: Roll pattern with density control

## Determinism

Drum generation is fully deterministic:

- Same project seed + same parameters = same pattern
- Per-clip seeding uses `(project_seed, clip_id, seed_offset)`
- Variation is deterministic but creates diversity across bars
- Fill patterns use separate seed for consistency

## MIDI Mapping

Drums use General MIDI (GM) drum mapping:

- **Kick**: 36 (C2)
- **Snare**: 38 (D2)
- **Clap**: 39 (Eb2)
- **Closed Hat**: 42 (F#2)
- **Open Hat**: 46 (Bb2)
- **Rim**: 37 (C#2)
- **Toms**: 45, 47 (A2, B2)

This ensures compatibility with Ableton Live and other DAWs.

## Regeneration

You can regenerate drums with different parameters:

1. Open TrackPopover on a drum clip
2. Adjust parameters (density, swing, variation, etc.)
3. Preview to hear changes
4. Apply to commit to database

Regeneration uses deterministic seeding, so:
- Same seed + same params = same result
- Different seed or variation = different but coherent pattern

