# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **Debug Instrumentation**: Added comprehensive debug logging system
  - Debug flags via localStorage: `midinecromancer:debug:gen`, `midinecromancer:debug:playback`, `midinecromancer:debug:polyrhythm`, `midinecromancer:debug:muteSolo`
  - Debug utilities in `frontend/src/utils/debug.ts` for consistent logging across components
  - Enhanced playback plan logging with track/clip filtering details
- **Polyrhythm Preview Audio**: Fixed polyrhythm preview to actually play audio
  - Preview now uses Tone.js to create and play `Tone.Part` with correct timing
  - AudioContext properly resumed on user gesture
  - Auto-stops after cycle completes or 8 seconds max
  - Debug logging for preview events
- **Drum Generation Enhancements**: Added producer-grade parameters
  - New parameters: `fill_probability`, `syncopation`, `ghost_note_probability`, `hat_subdivision`
  - Fill pattern generation for last bar/half-bar
  - Syncopation support (shifts off-beat hits)
  - Per-clip seeding with deterministic variation
  - Enhanced `generate_drum_pattern_v2` with additional controls
- **Chord Modal Upgrade**: Diatonic chord picker and quick insert
  - Diatonic chord picker in ChordEditor showing in-key chords
  - Borrowed chords tab for parallel/relative key chords
  - Chord chips with function tags (T/PD/D) and tension indicators
  - Quick insert in ChordGenerationModal for empty spaces
  - Backend endpoint `/theory/chords` for diatonic chord suggestions
  - Backend endpoint `/chords/insert` for inserting chords into empty arrangement spaces
- **Chord Modal v2**: Comprehensive chord generation and editing interface
  - **Two-tab interface**: Generate tab for creating/replacing progressions, Edit/Insert tab for manual selection
  - **Shared header controls**: Key, Mode, Style, Bars Range, Seed (with lock), Snap to Grid
  - **Generate tab features**:
    - Progression controls: Harmonic rhythm, Chord pool, Cadence bias, Tension, Repetition, Voicing, Inversion variance
    - Strum + Humanization: Beat-based controls with quick buttons and presets
    - **NEW Chord Hit Patterns**: Sustain, Piano Stabs, Guitar Strum, Syncopated Pump
    - Hit pattern controls: Hits per bar, Subdivision, Accent, Decay curve, Swing, Offset
    - Output options: Replace Range, Insert Empty Only, Layer (new clip)
  - **Edit/Insert tab features**:
    - Chord Palette: Diatonic and Borrowed chord chips with function/tension indicators
    - Suggested Chords: 8 contextual suggestions with preview and insert buttons
    - Timeline: Visual chord slots with inline editing, quantize, humanize actions
  - Backend endpoint `/api/v1/chords/suggest` for contextual chord suggestions
  - Full integration with arrangement panel for empty space insertion
- **Chord Modal Overhaul**: Redesigned chord editor with beat-based timing controls
  - Strum and humanize now use beats instead of milliseconds for BPM-independent behavior
  - Duration quick buttons (1, 2, 4, 8 beats)
  - Strum presets (None, 1/16, 1/8, 1/4, 1/2, 1 beat)
  - Timing preview showing strum and humanize effects
  - Audition button for non-destructive chord playback
  - Improved inversion stepper controls
  - New pattern controls: Hit mode (Hold, Stabs, Comp, Arp, Strum), Strum curve, Offset beats, Hit params
- **Segment Regeneration System**: Producer-grade regenerate/mutate workflow
  - Regenerate modal with segment-specific controls (Beats, Chords, Bass, Melody)
  - Preview mode for non-destructive preview before applying
  - Variation slider (0-1) for controlling mutation amount
  - Deterministic regeneration (same seed + params = same result)
  - Per-segment knobs:
    - **Beats**: Kit, density, swing, ghost notes, pause probability, hats pattern
    - **Chords**: Progression style, chord rhythm, strum preset, voicing, tension
    - **Bass**: Follow roots, rhythm lock, octave range, syncopation
    - **Melody**: Range, stepwise vs leapy, motif repeat, rhythmic density
  - Integration with TrackPopover for contextual regeneration
- **Backend Regenerate Service**: New service for clip regeneration with preview support
  - `POST /api/v1/clips/{clip_id}/regenerate` - Apply regeneration
  - `POST /api/v1/clips/{clip_id}/preview-regenerate` - Preview regeneration
  - Deterministic seed generation based on project ID, clip ID, kind, seed, and variation

### Changed
- **Chord Timing**: Migrated from milliseconds to beats for strum and humanize
  - New database fields: `strum_beats`, `humanize_beats` (migration 012)
  - Legacy `strum_ms` and `humanize_ms` fields retained for backward compatibility
  - Chord rendering now uses beat-based calculations for consistent behavior across BPM
  - Frontend chord editor UI updated to use beats exclusively
- **Chord Editor UI**: Complete redesign with producer-focused controls
  - Beat-based sliders and inputs with clear unit labels
  - Quick duration buttons for common values
  - Strum preset dropdown for musical values
  - Timing preview text explaining strum/humanize effects
  - Improved layout and visual hierarchy

### Fixed
- **Frontend Boot Issues**: Fixed critical runtime errors preventing app from loading
  - Fixed `DEBUG is not defined` error in `playbackPlan.ts` by using proper debug flag checks (`import.meta.env.DEV` and localStorage)
  - Added missing `Tone` import in `PolyrhythmEditor.vue`
  - Fixed `ChordGenerationModal` component resolution by ensuring proper import in `ArrangementPanel.vue`
  - Fixed `TrackPopover` props warnings by explicitly declaring all props (`projectId`, `bpm`, `timeSignatureNum`, `timeSignatureDen`)
  - All components now load without runtime errors or Vue warnings
- **Playback Robustness**: Improved playback error handling
  - Playback no longer crashes if debug flags are absent
  - Safe debug logging using environment checks and localStorage flags
  - AudioContext warnings handled gracefully (expected browser behavior, doesn't block functionality)
- **Mute/Solo Semantics**: Fixed mute/solo behavior across UI, playback, and export
  - ArrangementPanel now correctly uses `is_muted` and `is_soloed` fields consistently
  - Backend arrangement service correctly computes `mute` from clip/track `is_muted` state
  - Mute/solo toggles properly persist to backend and affect playback
  - Playback plan correctly implements: "if any track/clip soloed → only soloed play, else exclude muted"
  - Export respects mute/solo flags (already implemented, verified working)
- **Polyrhythm Preview**: Verified and documented preview audio functionality
  - Preview creates `Tone.Part` and schedules events correctly
  - AudioContext properly started on user gesture via `ensureAudioStarted()`
  - Preview stops automatically after cycle completes (or 8 seconds max)
  - Debug logging available via `localStorage.setItem('midinecromancer:debug:polyrhythm', 'true')`
- Chord editor now properly refreshes arrangement after save
- Chord lane clicking opens editor modal correctly
- Chord events update immediately in UI after edits

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- **Segment Creation Modal**: Comprehensive modal for creating and configuring musical segments
  - Click empty space in arrangement lanes to open modal
  - Select which segments to generate (beats, chords, bass, melody)
  - Configure segment-specific parameters via structured models
  - Preview mode: generate without saving to database
  - Apply mode: generate and persist clips to database
  - Producer-friendly defaults for rap/hip-hop style loops
  - Deterministic generation: same seed + parameters = same output
  - Backend endpoint: `POST /api/v1/segments/generate`
  - Segment models: `BeatsModel`, `ChordsModel`, `BassModel`, `MelodyModel`
  - Segment generation service with preview support
  - Frontend `SegmentCreationModal.vue` component with tabbed interface
  - Frontend API client for segment generation
  - Backend tests for deterministic output and preview/apply modes
  - Documentation: `docs/segments.md` explaining segment generation workflow

### Fixed
- **Arrangement Card Hover and Click**: Fixed hover behavior and click detection in arrangement cards
  - Replaced JavaScript-based hover detection with pure CSS hover for better performance
  - Fixed click detection by tracking initial mouse position to distinguish clicks from drags
  - Quick toggle buttons (mute, solo, duplicate) now appear on hover using CSS transitions
  - Fixed missing `dragStartPos` ref that was causing click detection to fail
  - Removed unused `onMounted`/`onUnmounted` imports and lifecycle hooks
- **Mute/Solo Functionality**: Fixed and enhanced mute/solo support for clips
  - Added `is_soloed` field to `ClipUpdate` interface
  - Added solo toggle button to arrangement cards (appears on hover)
  - Added `handleSoloToggle` function in `ArrangementPanel` to persist solo state
  - Fixed `handlePopoverApply` to correctly map `is_soloed` from segment to clip update
  - Solo state now properly persists when applying changes from `TrackPopover`
  - Playback already correctly filters clips based on solo state (no changes needed)
- **Toggle Solo Function**: Added missing `toggleSolo` method to `tracksApi` and backend endpoint
  - Frontend now has `tracksApi.toggleSolo(trackId, soloed)` method
  - Backend endpoint: `PATCH /api/v1/tracks/{track_id}/solo`
  - Solo state now persists and affects playback correctly
- **Chord Editor**: Implemented chord editing functionality
  - Created `ChordEditor.vue` component for editing chord properties
  - Clicking chords in `ChordLane` now opens editor modal
  - Editor allows editing intensity, voicing, inversion, strum, humanize, duration, enabled, and locked states
  - Changes persist immediately to backend
- **Arrangement Hover**: Fixed hover interactions in arrangement panel
  - Cards now have proper z-index to appear above grid lines
  - Empty space hint shows on hover with proper pointer-events handling
  - Grid lines have `pointer-events: none` to not block card interactions
- **Playback Mute/Solo**: Fixed playback to respect track-level solo
  - Playback now filters tracks based on mute/solo logic (matches backend logic)
  - If any track is soloed, only soloed tracks play
  - Muted tracks are excluded from playback
- **Chord Update Lock Logic**: Fixed chord update endpoint to allow unlocking locked chords
  - Previously, locked chords could not be updated at all, even to unlock them
  - Now allows updates when: chord is unlocked, or update is trying to unlock, or only updating lock status
  - Prevents updates to other fields when chord is locked (with clear error message)
- **Arrangement Panel Fixes**: Fixed critical regressions preventing arrangement panel from working
  - Fixed 404 error: corrected API endpoint URL from `/api/v1/projects/{id}/arrangement/panel` to `/projects/{id}/arrangement/panel` (baseURL already includes `/api/v1`)
  - Removed stale `ClipEditorModal` references from `ComposerView.vue` that were causing Vue warnings
  - Removed undefined `selectedClipSegment` and `clipEditorOpen` properties
  - Fixed click handler signature mismatch: `ArrangementCard` now correctly emits `(segment, shift)` instead of `(event, segment)`
  - Improved popover click handling: added `requestAnimationFrame` for DOM readiness and better overlay click detection
  - Fixed empty space click handling: added `stopPropagation` to prevent event bubbling
  - Fixed card ref collection: properly extracts element from Vue component ref
  - All Vue warnings resolved: no more "Failed to resolve component" or "property not defined" errors
  - Arrangement panel now loads successfully and displays cards correctly
  - Click-to-edit popover now opens reliably on card click

### Added
- **Arrangement UX Overhaul: Contextual Track Popovers**
  - Click any arrangement card to open a smart, contextual popover
  - Click empty space to create new clips
  - Four collapsible sections: Overview, Generate/Regenerate, Transform, Advanced
  - Live preview system: preview changes without committing
  - Non-destructive editing: all changes preview first, commit only on Apply
  - Kind-specific advanced controls (Beats, Chords, Bass, Melody)
  - Visual affordances: active card glow, hover states, empty space indicators
  - Keyboard shortcuts: Enter to apply, Escape to cancel, Cmd+D to duplicate
  - Popover positioning: automatically stays within viewport bounds
  - Preview session management: snapshot original state, revert on cancel
  - Regenerate with preview: variation, scope selection, keep structure option
  - Transform controls: time scaling, offset, swing, density
  - Quick actions: duplicate, half/double time, delete
  - Empty space creation: click empty lane area to create new clips
  - TrackPopover component with kind-specific advanced panels
  - usePreviewSession composable for managing preview state
- **Arrangement UX Polish**: DAW-like interaction model for arranging clips
  - Drag-to-move cards with grid snap (1 bar, 1/2, 1/4, 1 beat, or off)
  - Resize handles on card edges (left adjusts start+length, right adjusts length)
  - Multi-select with Shift-click (same lane only)
  - Visual grid lines with strong lines every bar
  - Zoom controls (mouse wheel + Cmd/Ctrl, trackpad pinch)
  - Duplicate gestures: context menu, Cmd/Ctrl+D, Alt-drag
  - Half/Double time scaling with animation
  - Intensity visual feedback (opacity, saturation, border thickness)
  - Quick expression toggles on hover (mute, duplicate)
  - Context menu for clip actions
  - Keyboard shortcuts: Cmd/Ctrl+D (duplicate), Escape (close/deselect), arrow keys in editor
  - ClipEditorModal with live preview and keyboard navigation
  - Smooth animations for all state changes (150-220ms)
  - Ghost outline during drag showing snapped position
  - Tooltips showing current values during drag/resize
  - Error feedback with shake animation for invalid moves
  - Composables: `useGrid`, `useDragSnap`, `useZoom` for reusable interaction logic
  - Fixed arrangement endpoint bug (tracks were being duplicated)
  - Added `intensity` and `params` fields to clips (migration `010_arrangement_cards`)
  - New arrangement panel endpoint: `GET /api/v1/projects/{id}/arrangement/panel`
  - Clip action endpoints: update, duplicate, time-scale, offset, regenerate
- **Chord Timeline 2.0**: Comprehensive expressive chord editing and visualization
  - Chord cards with duration, intensity, voicing, strum, and humanize controls
  - Chord cards are resizable (drag handles) and draggable (snap to grid)
  - Enable/disable and lock/unlock per chord
  - Grid quantization (default 1 beat, configurable)
  - Chord Timeline panel shows all chords with full expressive controls
  - Chord Lane in main arrangement view displays chords as blocks with visual feedback
  - Migration `008_chords_expressive` adds expressive fields to `chord_events` table
  - New API endpoints: `GET/POST/PUT/DELETE /api/v1/chords` and `/projects/{id}/chords`
  - Chord rendering service with deterministic strum, humanize, and voicing
  - Intensity controls velocity scaling (0-1, default 0.85)
  - Voicing presets: root, open, drop2, smooth
  - Strum timing: deterministic spread across chord tones (ms)
  - Humanization: deterministic timing and velocity jitter (ms)
  - Chord cards update backend immediately on change
  - Chord generation now sets default expressive parameters
- **ZIP Export**: MIDI export now supports ZIP format with per-part MIDI files
  - Default export is ZIP with one .mid file per track
  - Optional split by clip mode
  - Filename format: `ProjectName_YYYYMMDD_HHMMSS.zip`
  - Each part named: `part_01_TrackName.mid`
- **Arrangement Offsets**: Added per-clip and per-track timing offsets for arrangement synchronization
  - `Clip.start_offset_ticks` and `Track.start_offset_ticks` fields (migration 006)
  - Offsets applied consistently in playback, export, and preview
  - Deterministic offset generation helper using blake2b hashing
  - Offsets ensure polyrhythm lanes, drums, chords, bass, and melody align to song grid
- **Chord Visibility Fix**: Chord generation now properly persists and displays in UI
  - Chords are stored in database with proper clip relationships
  - ChordTimeline component displays generated chords
  - Arrangement automatically refreshes after chord generation
- **Looped Playback**: Implemented looped playback with toggleable looping (enabled by default).
  - Project-wide looping: Loops over entire computed project length
  - Region looping: Loop over a selected bar range (startBar to endBar, exclusive)
  - Loop toggle: UI button and keyboard shortcut (L) to enable/disable looping
  - Range selector: Choose between "Project" or "Bars" playback range
  - Bar range inputs: Set custom start and end bars for region playback
  - Uses Tone.Transport.loop with musical time (bars:beats:sixteenths) for sample-accurate looping
  - Loop state persisted in localStorage
  - Works with all event types: notes, chords, bass, and polyrhythm lanes
- **Playback Architecture Documentation**: Added `docs/playback.md` documenting current and new playback architecture
- **Mute/Solo Functionality**: Implemented comprehensive mute and solo support across tracks, clips, and polyrhythm lanes.
  - Added `Clip.is_muted` and `Clip.is_soloed` fields (migration 005)
  - Created `services/playback_filter.py` with centralized mute/solo resolution logic
  - Added API endpoints for toggling track and clip mute/solo states
  - Frontend mute toggle now persists to backend and affects playback
  - Export now respects mute/solo flags
- **Tick Conversion Utilities**: Created `music/ticks.py` with canonical timing conversion functions for consistent tick calculations across the application.

### Fixed
- **Middle Pane Rendering Regression**: Fixed broken middle track displays (Drums/Chords/Bass/Melody)
  - PianoRoll now uses proper timing calculations (no hardcoded 1920 ticks/bar)
  - ChordLane correctly displays chord events with proper positioning
  - Both components now account for clip and track offsets
  - Added ResizeObserver for dynamic container sizing
  - Added dev diagnostics overlay (Ctrl+Shift+D) for debugging
  - Centralized timing utilities in `frontend/src/music/timing.ts`
  - Added visual event adapters for unified rendering
  - Fixed container sizing issues (explicit heights, overflow handling)
  - Added runtime validation for tick values (prevents NaN/undefined)
- **Chord Generation Visibility**: Fixed chord generation to properly display in UI after generation
- **Polyrhythm Offset Alignment**: Fixed polyrhythm lane rendering to respect clip and track offsets
- **Tone.js Scheduling**: Fixed "Start time must be strictly greater" error by using proper musical time format and sorting events
- **Mute Toggle**: Fixed mute toggle in frontend to actually persist state and affect playback
- **Playback Filtering**: Playback now correctly filters muted tracks and clips
- **Export Filtering**: MIDI export now excludes muted tracks and clips

### Changed
- Updated `ClipInArrangement` schema to include `is_muted` and `is_soloed` fields
- Updated frontend types to include clip mute/solo state

### In Progress
- Polyrhythm timing alignment fixes
- Chord rendering and UI
- Bass generation and UI

### Added
- **Docker Compose Dev/Prod Profiles**: Complete Docker setup with development and production configurations
  - Dev profile: Hot reload backend (uvicorn --reload) and frontend (Vite HMR) with bind mounts
  - Prod profile: Immutable images, Gunicorn + Uvicorn workers, static frontend served via nginx
  - Migration gating: Backend starts only after migrations complete successfully (dev and prod)
  - Multi-stage Dockerfiles: Separate dev/prod targets for backend and frontend
  - Health checks: Database and backend services with proper health monitoring
  - Service dependencies: Uses Compose v2 `service_completed_successfully` for migration gating
- **Backend Dockerfile**: Multi-stage with dev (hot reload) and prod (Gunicorn) targets
  - Dev: uv sync with dev deps, bind-mount friendly, uvicorn --reload
  - Prod: Non-editable install, Gunicorn + 4 Uvicorn workers, non-root user, health check
- **Frontend Dockerfile**: Multi-stage with dev (Vite), build, and prod (nginx) targets
  - Dev: Node 20 Alpine, npm ci, Vite dev server
  - Build: npm run build for static assets
  - Prod: Nginx Alpine serving dist/ with SPA routing and API proxy
- **Environment Configuration**: `.env.example` with all required variables
- **Docker Makefile Targets**: `make docker-dev`, `make docker-prod`, `make docker-down`, `make docker-logs`, `make docker-clean`
- **Docker Documentation**: Comprehensive guide in `docs/docker.md` with dev/prod workflows, troubleshooting, and best practices
- **Theory Overlay + Suggestion Engine**: Interactive musical cheat sheet with theory-aware suggestions
  - Harmony suggestions: next chord, cadence endings, borrowed chords
  - Rhythm suggestions: ghost notes, lane rotations, density variations
  - Melody suggestions: chord tone arpeggios, approach notes, motif mutations
  - Audition system: preview suggestions via Tone.js without saving
  - Commit system: permanently add suggestions to composition
  - Deterministic generation: same seed + params = same suggestions
  - Project analysis: automatic key/mode detection, harmonic rhythm analysis
- **Suggestion Persistence**: Track suggestion runs and commits in database
  - `suggestion_runs` table: stores generation sessions with context and parameters
  - `suggestions` table: individual suggestions with preview events and commit plans
  - `suggestion_commits` table: tracks what was created from each commit
- **Analysis Module**: `music/analysis.py` for project state analysis
- **Suggestion Generation**: `music/suggest.py` for deterministic suggestion creation
- **Suggestion API**: Full CRUD for suggestion runs, preview, and commit endpoints
- **Theory Overlay UI**: Panel component with tabs, parameter controls, and suggestion cards
- **Documentation**: Comprehensive suggestions guide with examples and API usage

### Added (Previous)
- **Polyrhythm Profiles**: Create and manage polyrhythm patterns with configurable steps, pulses, cycle beats, and rotation
- **Polyrhythm Generation Engine**: Deterministic polyrhythm event generation using Euclidean rhythm algorithm
- **LCM Alignment**: Automatic alignment of multiple polyrhythm cycles using least common multiple for visualization and export
- **Polyrhythm API**: Full CRUD endpoints for polyrhythm profiles (`/api/v1/polyrhythms`)
- **Polyrhythm Preview**: Preview polyrhythm events before assigning to clips (`/api/v1/polyrhythms/preview/{project_id}`)
- **Clip Rhythm Modes**: Clips now support `standard`, `euclidean`, `polyrhythm`, and `polyrhythm_multi` grid modes
- **MIDI Export Enhancement**: Improved fractional beat handling with deterministic rounding for polyrhythm events
- **Polyrhythm UI**: Editor component for creating and managing polyrhythm profiles in the composer view
- **Polyrhythm Lanes (Multi-Cycle)**: Support for multiple independent polyrhythm cycles per clip
  - Each lane has its own profile, pitch, velocity, mute/solo, and seed offset
  - Lanes are aligned to a shared LCM grid for visualization and export
  - Full CRUD API for lane management (`/api/v1/clips/{clip_id}/polyrhythm-lanes`)
  - Preview endpoint returns merged events and grid specification
- **Deterministic Lane Rendering**: Stable seed generation per lane using blake2b hashing
- **Lane Visualization**: Stacked lane grid showing all cycles aligned to LCM
- **Biome Formatting**: Added Biome for TypeScript/JavaScript formatting and linting (frontend)
- **Ruff Configuration**: Enhanced ruff config for Python formatting and linting (backend)
- **Documentation**: Comprehensive polyrhythms and polyrhythm lanes guides with examples

### Changed
- Clip model now includes `grid_mode` and `polyrhythm_profile_id` fields (legacy support maintained)
- MIDI export now explicitly handles fractional beat positions with deterministic rounding
- MIDI export now renders polyrhythm lanes to notes before export
- Backend Makefile: Added `fmt` and `lint-fix` targets
- Frontend package.json: Added `format`, `lint`, and `check` scripts using Biome

### Technical
- Database migration `002_polyrhythms` adds `polyrhythm_profiles` table and extends `clips` table
- Database migration `003_polyrhythm_lanes` adds `clip_polyrhythm_lanes` join table with data migration for legacy clips
- Database migration `004_theory_overlay` adds `suggestion_runs`, `suggestions`, and `suggestion_commits` tables
- New modules: `music/analysis.py` (project analysis), `music/suggest.py` (suggestion generation)
- Deterministic suggestion generation using blake2b hashing for stable seeds
- Suggestion scoring algorithm combining theoretical correctness and context fit
- Commit plan system for describing what will be created (clips, notes, chord events)
- Tests for suggestion determinism, scoring stability, and commit behavior
- New module `music/polyrhythm.py` with `CycleSpec`, `LaneSpec`, `render_to_events`, `render_lanes_to_events`, `lcm_resolution`, and `lcm_grid_for_lanes` utilities
- New module `services/polyrhythm.py` for rendering lanes to notes for export
- Deterministic seed generation using `hashlib.blake2b` for stable hashing across Python sessions
- Tests for polyrhythm determinism, LCM calculation, multi-lane rendering, and mute/solo behavior

## [0.1.0] - YYYY-MM-DD

### Added
- MkDocs documentation setup with Material theme
- GitHub Pages automatic deployment
- Pre-commit hooks configuration
- Issue templates for bugs and features

[Unreleased]: https://github.com/sempervent/generative-midi-workbench/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/sempervent/generative-midi-workbench/releases/tag/v0.1.0

