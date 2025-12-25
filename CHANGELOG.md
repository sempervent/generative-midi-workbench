# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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

[Unreleased]: https://github.com/your-org/your-repo/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/your-org/your-repo/releases/tag/v0.1.0

