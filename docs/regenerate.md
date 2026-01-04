# Segment Regeneration

The regeneration system allows you to re-roll or mutate segments (drums, chords, bass, melody) without affecting other parts of your arrangement.

## Opening the Regenerate Modal

- **From Track Popover**: Click any arrangement card to open the popover, then expand "Generate / Regenerate" and click "Open Regenerate Modal"
- The modal opens with the current clip's kind pre-selected

## Regeneration Workflow

### Preview Mode
- Click "Preview" to generate new content without saving
- Preview shows what will be generated (ghost cards or playable preview)
- No database writes occur in preview mode

### Apply Mode
- Click "Apply" to regenerate and persist changes
- Only regenerates segments that are enabled
- Arrangement panel refreshes automatically after apply

### Cancel
- Click "Cancel" or press Escape to close without changes
- Preview state is discarded

## Global Settings

- **Seed**: Base seed for generation (randomize button available)
- **Variation**: Amount of variation (0-1)
  - 0.0 = minimal variation (very similar to original)
  - 1.0 = maximum variation (completely different)

## Segment-Specific Controls

### Beats
- **Kit**: Hip-Hop, Trap, Boom Bap, or Minimal
- **Density**: Overall hit density (0-1)
- **Swing**: Swing amount (0-1)
- **Ghost Notes**: Enable/disable ghost notes
- **Pause Probability**: Probability of pauses/breaks (0-0.5)
- **Hats Pattern**: Straight, Syncopated, Euclidean, or Polyrhythm

### Chords
- **Progression Style**: Pop, Rap Minor, Jazzy, Modal, or Circle of Fifths
- **Chord Rhythm**: Block, Syncopated, or Arp-lite
- **Strum Preset**: None, 1/16, 1/8, 1/4, or 1/2 beats
- **Voicing**: Root, Open, Drop-2, or Tight
- **Tension**: Borrowed chords probability (0-1)

### Bass
- **Follow Roots**: How closely bass follows kick pattern (0-1)
- **Rhythm Lock**: Lock to Drums, Lock to Chords, or Free
- **Octave Range**: Bass octave (1-4)
- **Syncopation**: Syncopation amount (0-1)

### Melody
- **Range**: Narrow, Medium, or Wide
- **Stepwise vs Leapy**: Probability of leaps vs. stepwise motion (0-1)
- **Motif Repeat**: How much motifs repeat (0-1)
- **Rhythmic Density**: Note density (0-1)

## Determinism

Regeneration is deterministic:
- Same seed + same variation + same params = same output
- Seeds are computed deterministically from project ID, clip ID, kind, base seed, and variation
- This ensures reproducible results for debugging and iteration

## Best Practices

1. **Start with Preview**: Always preview before applying to see what will change
2. **Adjust Variation**: Use lower variation (0.1-0.3) for subtle changes, higher (0.7-1.0) for dramatic re-rolls
3. **Enable Selectively**: Only enable segments you want to regenerate
4. **Lock Seeds**: Use the same seed with different variation to explore variations of the same idea

