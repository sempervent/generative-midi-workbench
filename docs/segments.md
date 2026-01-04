# Segment Generation

The Segment Creation Modal allows you to create and configure musical segments (clips with content) for your arrangement. You can generate beats, chords, bass, and melody with producer-grade controls.

## Opening the Modal

- **Click empty space** in any arrangement lane to open the modal with the clicked position as the start bar
- The modal opens with sensible defaults for a rap/hip-hop style loop

## Segment Types

### Beats
Generate drum patterns with:
- **Kit**: Hip-Hop, Trap, Boom Bap, or Minimal
- **Pattern**: Straight, Syncopated, Euclidean, or Polyrhythm
- **Density**: Overall hit density (0-1)
- **Swing**: Swing amount (0-0.75)
- **Ghost Notes**: Enable/disable ghost notes
- **Fills**: None, Ends, Every 4 bars, or Random

### Chords
Generate chord progressions with:
- **Key & Mode**: Select key and mode (Ionian, Dorian, etc.)
- **Progression Style**: Pop, Rap Minor, Jazzy, Modal, or Circle of Fifths
- **Voicing**: Root, Drop 2, Spread, or Tight
- **Intensity**: Velocity and note density (0-1)
- **Strum**: Strum timing in milliseconds (0-80ms)

### Bass
Generate basslines with:
- **Style**: Root, Walking, 808, or Syncopated
- **Octave**: Bass octave (1-4)
- **Follow Kicks**: How closely bass follows kick pattern (0-1)
- **Rhythmic Density**: Note density (0-1)
- **Intensity**: Velocity scaling (0-1)

### Melody
Generate melodies with:
- **Range**: Narrow, Medium, or Wide
- **Motif Repetition**: How much motifs repeat (0-1)
- **Leapiness**: Probability of leaps vs. stepwise motion (0-1)
- **Call & Response**: Enable/disable call-response patterns
- **Syncopation**: Syncopation amount (0-1)
- **Intensity**: Velocity scaling (0-1)

## Preview vs. Apply

- **Preview**: Generates segments without saving to database. Use this to test different configurations.
- **Apply/Create**: Generates segments and saves them to the database. The arrangement panel refreshes automatically.

## Determinism

Segment generation is deterministic:
- Same seed + same parameters = same output
- Seeds are computed deterministically from project ID, start bar, and segment kind
- This ensures reproducible results for debugging and iteration

## Model Defaults

The modal uses producer-friendly defaults:
- **Beats**: Hip-Hop kit, straight pattern, medium density, accent on 2 and 4
- **Chords**: Minor mode, rap-style progression, root voicing
- **Bass**: 808 style, follows kicks, medium density
- **Melody**: Medium range, moderate repetition, stepwise bias

These defaults yield a coherent rap/hip-hop loop that works well together.

