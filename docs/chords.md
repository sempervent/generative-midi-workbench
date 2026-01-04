# Chord Generation and Display

MIDINecromancer generates chord progressions based on music theory and displays them in the UI with full expressive control.

## Chord Modal v2

The Chord Modal v2 provides comprehensive chord generation and editing with two main tabs:

### Generate Tab

The Generate tab allows you to create or replace chord progressions with full control:

**Shared Header Controls** (available in both tabs):
- **Key**: Select the project key (C, C#, D, etc.)
- **Mode**: Select the scale mode (Ionian/Major, Dorian, Phrygian, Lydian, Mixolydian, Aeolian/Minor, Locrian)
- **Style**: Choose a generation style (Rap Dark, Rap Bright, Neo Soul, Trap Minimal, Boom Bap, Cinematic, Ambient)
- **Bars Range**: Set start bar and length in bars
- **Snap to Grid**: Toggle grid snapping for bar boundaries
- **Seed**: Control generation seed for determinism
- **Lock Seed**: Keep seed constant across regenerations

**Progression Controls**:
- **Harmonic Rhythm**: How often chords change (every 1 bar, every 2 bars, every beat, syncopated)
- **Chord Pool**: Source of chords (Diatonic only, Borrowed chords, Secondary dominants, Chromatic approach)
- **Cadence Bias**: Slider (0-1) controlling cadence strength
- **Tension**: Slider (0-1) controlling harmonic tension
- **Repetition**: Slider (0-1) controlling motif repetition
- **Voicing**: Voicing style (Triads, 7ths, 9ths, Spread, Cluster)
- **Inversion Variance**: Slider (0-1) controlling inversion variety

**Strum + Humanization** (Beat-based):
- **Strum Duration**: Number input with quick buttons (0, 1/16, 1/8, 1/4, 1/2, 1 beat)
- **Strum Direction**: Down, Up, Alternate, Random
- **Humanize**: Range 0-0.25 beats for timing variation
- **Velocity Humanize**: Range 0-0.5 for velocity variation
- **Gate**: Duration fraction (0.1-1.0) controlling note length

**Chord Hit Pattern** (NEW):
- **Pattern Type**: 
  - Sustain (one hit, held)
  - Piano Stabs (repeated hits)
  - Guitar Strum (repeated strums with decay)
  - Syncopated Pump (offbeat)
- **Hits per Bar**: 1, 2, 4, 8, or 16 hits
- **Hit Subdivision**: 1/4, 1/8, 1/16, 1/32, Triplet 1/8, Triplet 1/16
- **Hit Accent**: Slider (0-1) for downbeat accenting
- **Decay Curve**: Slider (0-1) for velocity decay over hits
- **Swing**: Range 0-0.2 beats for swing feel
- **Offset**: Range -0.5 to +0.5 beats for push/pull timing

**Output Options**:
- **Apply Mode**: Replace Range, Insert into Empty Only, or Layer (new clip)
- **Preview**: Audition generation without committing
- **Apply**: Commit generation to project
- **Cancel**: Close modal without changes

### Edit/Insert Tab

The Edit/Insert tab provides manual chord selection and suggestions:

**Chord Palette**:
- **Diatonic Tab**: Shows all in-key chords (I, ii, iii, IV, V, vi, vii°)
- **Borrowed Tab**: Shows parallel/relative key chords
- Each chord chip displays:
  - Roman numeral
  - Chord name
  - Color intensity based on function/tension
- **Show Extensions**: Toggle to show 7ths/9ths or triads only

**Suggested Chords Panel**:
- **Load Suggestions**: Generate 8 contextual chord suggestions
- Each suggestion shows:
  - Reason (Next chord, Cadence, Borrowed color, Tritone spice)
  - Score
  - Explanation
  - Preview button (audition)
  - Insert button (add to timeline)

**Timeline Insert/Edit**:
- List of chord slots across selected bar range
- Each slot shows: start bar, chord, duration
- Click slot to edit inline
- Actions:
  - Insert at cursor
  - Split chord
  - Merge adjacent
  - Quantize starts
  - Humanize starts

## Chord Timeline 2.0

The Chord Timeline is a powerful interface for editing and visualizing chord progressions with expressive parameters.

## Chord Generation

### Generating Chords

Click the **"Generate Chords"** button in the composer view. This will:

1. Create or clear the chords track
2. Generate a chord progression based on:
   - Project key and mode
   - Number of bars
   - Project seed (for determinism)
3. Create clips and chord events in the database with default expressive parameters
4. Automatically refresh the arrangement to display chords

### Chord Progression Algorithm

The generator uses:
- Circle of fifths motion (preferred)
- Common progressions for the selected mode (major/ionian or minor/aeolian)
- Cadence endings (V->I or ii->V->I)
- Deterministic generation based on project seed

### Chord Storage

Chords are stored as `ChordEvent` records with expressive fields:
- `clip_id`: Links to the clip containing the chord
- `start_tick`: Start position within the clip (relative to clip start)
- `duration_tick`: Duration in ticks
- `duration_beats`: Duration in beats (for UI display and editing)
- `roman_numeral`: Roman numeral notation (e.g., "I", "vi", "V7")
- `chord_name`: Chord symbol (e.g., "Am", "G7", "C")
- `intensity`: Velocity scaling factor (0.0-1.0, default 0.85)
- `voicing`: Voicing preset ("root", "open", "drop2", "smooth")
- `inversion`: Inversion number (0=root, 1=first, 2=second)
- `strum_beats`: Strum timing spread in beats (default 0.0)
- `humanize_beats`: Humanization range in beats (default 0.0)
- `strum_ms`: Deprecated - use `strum_beats` instead
- `humanize_ms`: Deprecated - use `humanize_beats` instead
- `velocity_jitter`: Velocity jitter range (default 0)
- `timing_jitter_ms`: Timing jitter range in milliseconds (default 0)
- `is_enabled`: Whether chord is enabled (default true)
- `is_locked`: Whether chord is locked from editing (default false)
- `grid_quantum`: Grid quantization in beats (optional, project-level default)

## Chord Display

### Chord Timeline

The **Chord Timeline** panel (right side of composer view) displays:
- All chord events from the chords track as interactive cards
- Each card shows:
  - Roman numeral notation (e.g., "I", "vi")
  - Chord name (e.g., "Am", "G7")
  - Duration (visual width proportional to beats)
  - Intensity slider (0-100%)
  - Voicing dropdown (root, open, drop2, smooth)
  - Strum control (ms)
  - Humanize control (ms)
  - Enable/disable toggle
  - Lock/unlock toggle
- Cards are resizable (drag right edge) to change duration
- Cards snap to grid quantum (default: 1 beat)
- All changes persist immediately to the database

### Chord Lane

The **Chords** lane in the main arrangement view displays:
- Chord events as colored blocks spanning their duration
- Block color intensity reflects the chord's intensity parameter
- Clicking a block opens the chord editor
- Disabled chords appear faded
- Locked chords have a dashed border

### Chord Events in Arrangement

Chord events are included in the arrangement API response:
- `GET /api/v1/projects/{project_id}/arrangement`
- Chords are nested under `tracks[].clips[].chord_events[]` with all expressive fields

## Chord Editor

The chord editor provides comprehensive controls for editing chord events.

### Diatonic Chord Picker

When editing a chord, you can select from diatonic chords in the current key/mode:
- **Diatonic tab**: Shows all in-key chords (I, ii, iii, IV, V, vi, vii° for major)
- **Borrowed tab**: Shows chords from parallel/relative keys (e.g., bVII, bVI, iv in major)
- Each chord chip shows:
  - Roman numeral (e.g., "I", "vi")
  - Chord name (e.g., "C", "Am")
  - Function tag (T = Tonic, PD = Pre-dominant, D = Dominant)
  - Tension indicator (high tension chords highlighted)

Clicking a chord chip updates the chord event immediately.

### Inserting Chords into Empty Spaces

You can insert chords directly into empty arrangement spaces:

1. Click empty space in the chords lane
2. ChordGenerationModal opens with "Quick Insert" section
3. Select a diatonic chord to insert immediately
4. Chord is created at the clicked position with default settings

Alternatively, use the full generation workflow:
1. Click empty space in chords lane
2. Configure generation parameters (style, complexity, tension, etc.)
3. Click "Generate Options" to see suggestions
4. Preview and apply a suggestion

## Expressive Parameters

### Intensity

Controls the velocity scaling of rendered notes:
- Range: 0.0 (silent) to 1.0 (full velocity)
- Default: 0.85
- Applied as: `velocity = base_velocity * intensity`

### Voicing

Determines how chord tones are arranged:
- **root**: Standard root position in middle octave
- **open**: Spread across wider range (root, 5th, 3rd)
- **drop2**: Drop 2nd voice down an octave
- **smooth**: Voice-leading optimized (default for progressions)

### Strum

Time spread between chord tones (beat-based):
- Range: 0-2.0 beats
- Default: 0.0 (all tones simultaneous)
- Applied deterministically using project seed
- Creates arpeggio-like effect when > 0
- **Beat-based**: Same strum setting behaves consistently across BPM changes
- Presets available: None (0), 1/16, 1/8, 1/4, 1/2, 1 beat

### Humanize

Adds subtle timing and velocity variation (beat-based):
- `humanize_beats`: Timing jitter range (0-0.5 beats, typically 0-1/8 beat)
- `velocity_jitter`: Velocity variation range (0-20)
- Applied deterministically using project seed
- Creates more natural, less mechanical sound
- **Beat-based**: Same humanize setting behaves consistently across BPM changes

### Grid Quantization

Chords snap to a grid quantum when moved or resized:
- Default: 1 beat
- Can be set per chord or project-wide
- Ensures clean alignment with other musical elements

## Using Chords

### Bass Generation

Bass lines can be generated from chord progressions:
- Bass notes follow chord roots
- Timing aligns with chord changes

### Melody Generation

Melody generation can use chord progressions for:
- Chord tone targeting
- Harmonic context
- Scale selection

### Suggestions

The theory overlay suggestion engine uses chord progressions for:
- Harmony suggestions (next chord, cadences)
- Melody suggestions (chord tone arpeggios)

## API

### Generate Chords

```http
POST /api/v1/projects/{project_id}/generate/chords
Content-Type: application/json

{
  "seed": 12345,
  "params": {
    "start_on": "I",
    "prefer_circle_motion": true,
    "cadence_ending": true
  }
}
```

### Get Arrangement (includes chords)

```http
GET /api/v1/projects/{project_id}/arrangement
```

Response includes chord events in `tracks[].clips[].chord_events[]` with all expressive fields.

### List Chord Events

```http
GET /api/v1/projects/{project_id}/chords?start_bar=0&end_bar=8
```

Returns all chord events for the project, optionally filtered by bar range.

### Create Chord Event

```http
POST /api/v1/chords
Content-Type: application/json

{
  "clip_id": "...",
  "start_tick": 0,
  "duration_tick": 1920,
  "duration_beats": 4.0,
  "roman_numeral": "I",
  "chord_name": "Cmaj",
  "intensity": 0.85,
  "voicing": "root",
  "inversion": 0,
  "strum_beats": 0.0,
  "humanize_beats": 0.0
}
```

### Update Chord Event

```http
PUT /api/v1/chords/{chord_id}
Content-Type: application/json

{
  "duration_beats": 2.0,
  "intensity": 0.9,
  "voicing": "open"
}
```

### Delete Chord Event

```http
DELETE /api/v1/chords/{chord_id}
```
