# MIDI Export

MIDINecromancer supports two export formats: single MIDI file and ZIP archive with per-part MIDI files.

## Export Formats

### Single MIDI File

**Endpoint**: `GET /api/v1/projects/{project_id}/export/midi`

Exports the entire project as a single Standard MIDI File (`.mid`). All tracks are combined into one file with separate MIDI tracks for each instrument.

**Use Case**: Quick export for simple projects or when you need a single file.

### ZIP Archive (Per-Part)

**Endpoint**: `GET /api/v1/projects/{project_id}/export/zip?split_by=track`

Exports the project as a ZIP archive containing one MIDI file per part. This is the default and recommended format.

**Parameters**:
- `split_by` (optional): How to split parts
  - `track` (default): One MIDI file per track
  - `clip`: One MIDI file per clip

**Filename Format**: `ProjectName_YYYYMMDD_HHMMSS.zip`

**Part Naming**: `part_01_TrackName.mid`, `part_02_TrackName.mid`, etc.

**Use Case**: 
- Import into DAWs like Ableton Live, Logic Pro, or FL Studio as separate tracks
- Individual track editing
- Mixing and arrangement in external software

## Export Contents

Both formats include:
- All notes from clips (including polyrhythm lanes rendered to notes)
- Applied timing offsets (clip and track offsets)
- Mute/solo filtering (muted tracks/clips are excluded)
- Proper MIDI channels and program changes
- Time signature and tempo information

## Timing Offsets

Offsets are applied during export:
- `effective_tick = base_tick + clip.start_offset_ticks + track.start_offset_ticks`

This ensures that exported MIDI files reflect the same timing as playback.

## Frontend Usage

The UI provides two export buttons:
- **Export ZIP** (primary): Downloads ZIP archive with per-track MIDI files
- **Export MIDI** (secondary): Downloads single combined MIDI file

## API Examples

```bash
# Export as ZIP (default: split by track)
curl -O -J http://localhost:8000/api/v1/projects/{project_id}/export/zip

# Export as ZIP (split by clip)
curl -O -J "http://localhost:8000/api/v1/projects/{project_id}/export/zip?split_by=clip"

# Export as single MIDI
curl -O -J http://localhost:8000/api/v1/projects/{project_id}/export/midi
```

