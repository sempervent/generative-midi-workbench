# Theory Overlay + Suggestion Engine

MIDINecromancer includes a **Theory Overlay** that provides music-theory-aware suggestions for harmony, rhythm, and melody. You can audition suggestions before committing them to your composition.

## What is the Theory Overlay?

The Theory Overlay analyzes your current composition and suggests musical ideas that:
- Follow music theory principles (circle-of-fifths, diatonic harmony, etc.)
- Fit the current harmonic context
- Can be previewed (auditioned) without saving
- Can be committed to permanently add to your composition

## How It Works

### 1. Analysis

The system analyzes your project to detect:
- **Key and Mode**: Current harmonic center
- **Harmonic Rhythm**: How often chords change
- **Rhythmic Density**: Note density per track/lane
- **Chord Functions**: Roman numeral analysis

### 2. Suggestion Generation

Based on the analysis, the engine generates ranked suggestions in three categories:

#### Harmony Suggestions
- **Next Chord**: Circle-of-fifths motion (V, IV)
- **Cadence Ending**: Strong resolution (V→I, ii→V→I)
- **Borrowed Chords**: Modal interchange (e.g., iv in major key)

#### Rhythm Suggestions
- **Ghost Notes**: Subtle off-beat accents
- **Lane Rotation**: Shift polyrhythm patterns
- **Density Variations**: Add or remove rhythmic events

#### Melody Suggestions
- **Arpeggiate Chord Tones**: Highlight harmonic structure
- **Approach Notes**: Smooth melodic motion
- **Motif Mutation**: Variations on existing patterns

### 3. Audition

Click **Audition** to hear a suggestion without saving:
- Plays via Tone.js overlay
- Does not modify your composition
- Can be stopped/cleared
- Perfect for trying multiple suggestions

### 4. Commit

Click **Commit** to permanently add a suggestion:
- Creates new clips, notes, or chord events
- Updates your composition
- Marks suggestion as committed
- Can be undone by manually deleting created elements

## Using the Theory Overlay

### In the Composer View

1. **Open Theory Overlay Panel** (right side)
2. **View Analysis**: See detected key, mode, harmonic rhythm
3. **Adjust Parameters**:
   - **Seed**: Control suggestion variation
   - **Complexity**: How complex suggestions should be (0.0-1.0)
   - **Tension**: Harmonic tension level (0.0-1.0)
   - **Density**: Rhythmic density (0.0-1.0)
4. **Generate Suggestions**: Click "Generate Suggestions"
5. **Browse by Category**: Switch between Harmony / Rhythm / Melody tabs
6. **Audition**: Click 🎵 to preview
7. **Commit**: Click ✓ to add to composition

## Determinism

Suggestions are **fully deterministic**. Given the same:
- Project ID
- Seed
- Parameters (complexity, tension, density)
- Project state (chords, notes, lanes)

...you will get **identical suggestions** every time.

### Seed Generation

Each suggestion uses a deterministic seed derived from:
```
suggestion_seed = hash(base_seed, project_id, kind, index)
```

This ensures:
- Same inputs = same outputs
- Different suggestion types = different patterns
- Stable ranking and ordering

## Suggestion Scoring

Suggestions are ranked by a **score** (0.0-1.0) that considers:
- **Theoretical correctness**: Does it follow music theory?
- **Context fit**: Does it match the current harmonic/rhythmic context?
- **Complexity match**: Does it match the requested complexity level?

Higher scores appear first. Suggestions are sorted by score, then by title.

## Commit Plans

Each suggestion includes a **commit plan** that describes what will be created:

### Harmony Commit Plans
- `create_chord_event`: Creates a single chord event in a clip
- `create_chord_events`: Creates multiple chord events (e.g., cadence)

### Rhythm Commit Plans
- `append_notes`: Adds notes to an existing clip
- `update_lane_rotation`: Modifies a polyrhythm lane

### Melody Commit Plans
- `create_notes`: Creates notes in a new or existing clip

## Examples

### Example 1: Adding a Cadence

1. Generate suggestions for a project in C major
2. See "Cadence Ending" suggestion (score: 0.9)
3. Audition: Hear V→I resolution
4. Commit: Adds V and I chords to end of progression

### Example 2: Adding Ghost Notes

1. Generate rhythm suggestions
2. See "Add Ghost Notes" suggestion
3. Audition: Hear subtle off-beat accents
4. Commit: Adds quiet hi-hat notes to drum track

### Example 3: Arpeggiating a Chord

1. Generate melody suggestions
2. See "Arpeggiate Chord Tones" for current chord
3. Audition: Hear chord tones played sequentially
4. Commit: Adds arpeggio notes to melody track

## API Usage

### Create Suggestion Run

```bash
POST /api/v1/suggestions/run
{
  "project_id": "...",
  "seed": 12345,
  "params": {
    "complexity": 0.7,
    "tension": 0.6,
    "density": 0.5
  }
}
```

### Preview Suggestion

```bash
POST /api/v1/suggestions/preview
{
  "project_id": "...",
  "kind": "harmony",
  "seed": 12345,
  "params": {}
}
```

### Commit Suggestion

```bash
POST /api/v1/suggestions/{suggestion_id}/commit
```

## Best Practices

1. **Start Simple**: Use default parameters first
2. **Audition First**: Always audition before committing
3. **Adjust Parameters**: Tweak complexity/tension/density for different feels
4. **Use Seeds**: Same seed = same suggestions (useful for reproducibility)
5. **Check Context**: Review detected key/mode to ensure analysis is correct

## Technical Details

- **Analysis**: Uses chord events and note distributions to infer context
- **Generation**: Deterministic algorithms using music theory rules
- **Scoring**: Combines theoretical correctness with context fit
- **Commit**: Idempotent operations (committing twice is rejected)

## Limitations

- Analysis is heuristic-based (may not always detect key correctly)
- Suggestions are rule-based (not AI-generated)
- Commit operations are one-way (no automatic undo)
- Preview events are ephemeral (not saved until committed)

