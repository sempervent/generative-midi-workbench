# MIDINecromancer

A full-stack generative MIDI composition workbench that lets you create, edit, and play back MIDI compositions in the browser. The system uses music theory constraints (circle-of-fifths, diatonic harmony) to generate intelligent drum patterns, chord progressions, basslines, and melodies.

## Features

- 🎹 **Project Management**: Create and manage multiple composition projects
- 🎵 **Music Theory-Driven Generation**:
  - Drum patterns with Euclidean rhythms and variation
  - Chord progressions using circle-of-fifths motion
  - Basslines that follow chord roots with syncopation
  - Melodies constrained to scales with stepwise motion
- 🎛️ **Interactive UI**:
  - Circle-of-fifths key selector
  - Piano roll visualization
  - Chord timeline display
  - Real-time playback (Web MIDI + Tone.js fallback)
- 💾 **PostgreSQL Storage**: All compositions stored in database
- 🎼 **MIDI Export**: Export compositions as Standard MIDI Files (.mid)
- 🔄 **Reproducible**: Deterministic generation with seed-based RNG

## Tech Stack

### Backend
- **Python 3.12+** with `uv` for package management
- **FastAPI** for REST API
- **SQLAlchemy 2.0** (async) for database ORM
- **Alembic** for schema migrations
- **PostgreSQL** for data storage
- **mido** for MIDI file generation

### Frontend
- **Vue 3** with TypeScript
- **Vite** for build tooling
- **Pinia** for state management
- **Tone.js** for audio playback
- **Web MIDI API** support (when available)

## Prerequisites

- Python 3.12+
- Node.js 18+
- Docker and Docker Compose (for PostgreSQL)
- `uv` (Python package manager) - install from [https://github.com/astral-sh/uv](https://github.com/astral-sh/uv)

## Setup

### Option A: Docker Compose (Recommended)

The easiest way to run MIDINecromancer is using Docker Compose with dev or prod profiles.

#### Development

```bash
# Copy environment file
cp .env.example .env

# Start all services with hot reload
make docker-dev
# or
docker compose --profile dev up --build
```

This starts:
- PostgreSQL database
- Backend with hot reload (http://localhost:8000)
- Frontend with Vite HMR (http://localhost:5173)
- Automatic migrations before backend starts

#### Production

```bash
# Copy and configure .env
cp .env.example .env
# Edit .env with production values

# Start production services
make docker-prod
# or
docker compose --profile prod up --build -d
```

See [Docker Setup Guide](docs/docker.md) for detailed information.

### Option B: Local Development

#### 1. Start PostgreSQL

```bash
docker compose up -d db
```

This starts a PostgreSQL container on port 5432.

### 3. Backend Setup

```bash
cd backend

# Install dependencies with uv
uv sync

# Set up environment (create .env file)
cat > .env << EOF
DATABASE_URL=postgresql+asyncpg://midinecromancer:midinecromancer@localhost:5432/midinecromancer
ENVIRONMENT=development
DEBUG=true
CORS_ORIGINS=http://localhost:5173,http://localhost:3000
EOF

# Run database migrations
uv run alembic upgrade head

# Start the backend server
uv run uvicorn midinecromancer.main:app --reload --port 8000
```

The API will be available at `http://localhost:8000`. API documentation at `http://localhost:8000/docs`.

### 4. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`.

## Usage

### Creating a Project

1. Open the application in your browser
2. Click "New Project"
3. Enter a project name
4. Configure key, mode, BPM, time signature, and number of bars

### Generating Content

1. Open a project in the composer view
2. Use the generation buttons:
   - **Full**: Generates all parts (drums, chords, bass, melody)
   - **Drums**: Generates drum pattern only
   - **Chords**: Generates chord progression only
   - **Bass**: Generates bassline (requires chords first)
   - **Melody**: Generates melody only

### Playing Back

1. Click the play button (▶) in the transport controls
2. The composition will play using Tone.js (WebAudio) or Web MIDI if available

### Exporting

1. Click "Export MIDI" in the header
2. The composition will be downloaded as a `.mid` file

## Project Structure

```
midinecromancer/
├── backend/
│   ├── src/midinecromancer/
│   │   ├── api/          # FastAPI routes
│   │   ├── db/           # Database configuration
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Business logic
│   │   ├── music/        # Music theory & generation
│   │   └── midi/         # MIDI export
│   ├── alembic/          # Database migrations
│   └── tests/            # Unit tests
├── frontend/
│   ├── src/
│   │   ├── api/          # API client
│   │   ├── components/   # Vue components
│   │   ├── views/        # Page views
│   │   ├── stores/       # Pinia stores
│   │   └── music/        # Playback engine
│   └── package.json
├── docker-compose.yml
└── README.md
```

## API Endpoints

### Projects
- `POST /api/v1/projects` - Create project
- `GET /api/v1/projects` - List projects
- `GET /api/v1/projects/{id}` - Get project
- `PATCH /api/v1/projects/{id}` - Update project
- `GET /api/v1/projects/{id}/arrangement` - Get full arrangement

### Generation
- `POST /api/v1/projects/{id}/generate/full` - Generate full arrangement
- `POST /api/v1/projects/{id}/generate/drums` - Generate drums
- `POST /api/v1/projects/{id}/generate/chords` - Generate chords
- `POST /api/v1/projects/{id}/generate/bass` - Generate bass
- `POST /api/v1/projects/{id}/generate/melody` - Generate melody

### Export
- `GET /api/v1/projects/{id}/export/midi` - Export as MIDI file
- `GET /api/v1/projects/{id}/export/json` - Export as JSON

## Testing

```bash
cd backend
uv run pytest
```

Tests include:
- Music theory utilities
- Deterministic generation (same seed = same output)
- MIDI export validation

## Development

### Running Migrations

```bash
cd backend
uv run alembic upgrade head        # Apply migrations
uv run alembic revision --autogenerate -m "description"  # Create new migration
```

### Code Quality

The backend uses `ruff` for linting (optional):

```bash
cd backend
uv run ruff check src/
uv run ruff format src/
```

## License

MIT License - see LICENSE file for details.

## Contributing

This is an MVP implementation. Future enhancements could include:
- More sophisticated music theory (borrowed chords, modal interchange)
- Advanced rhythm patterns
- MIDI editing in the UI
- Multiple clips per track
- Effects and processing
- Collaboration features
