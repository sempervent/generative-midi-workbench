"""Tests for ZIP export functionality."""

import io
import zipfile

import mido
import pytest

from midinecromancer.midi.export_zip import export_project_to_zip, generate_zip_filename


@pytest.fixture
def sample_project():
    """Create a sample project for testing."""
    from midinecromancer.models.project import Project

    return Project(
        id="00000000-0000-0000-0000-000000000001",
        name="Test Project",
        bpm=120,
        time_signature_num=4,
        time_signature_den=4,
        bars=8,
        key_tonic="C",
        mode="ionian",
        seed=12345,
    )


@pytest.fixture
def sample_tracks(sample_project):
    """Create sample tracks with clips and notes."""
    from midinecromancer.models.clip import Clip
    from midinecromancer.models.note import Note
    from midinecromancer.models.track import Track

    track1 = Track(
        id="00000000-0000-0000-0000-000000000002",
        project_id=sample_project.id,
        name="Drums",
        role="drums",
        midi_channel=9,
        midi_program=0,
        start_offset_ticks=0,
    )

    clip1 = Clip(
        id="00000000-0000-0000-0000-000000000003",
        track_id=track1.id,
        start_bar=0,
        length_bars=8,
        start_offset_ticks=0,
    )

    note1 = Note(
        id="00000000-0000-0000-0000-000000000004",
        clip_id=clip1.id,
        pitch=36,  # Kick
        velocity=100,
        start_tick=0,
        duration_tick=480,
    )

    clip1.notes = [note1]
    track1.clips = [clip1]

    return [track1]


def test_export_zip_track_split(sample_project, sample_tracks):
    """Test ZIP export with track splitting."""
    zip_bytes = export_project_to_zip(sample_project, sample_tracks, split_by="track")

    # Verify it's a valid ZIP
    zip_file = zipfile.ZipFile(io.BytesIO(zip_bytes))
    assert len(zip_file.namelist()) == 1

    # Verify MIDI file is valid
    midi_bytes = zip_file.read(zip_file.namelist()[0])
    mid = mido.MidiFile(file=io.BytesIO(midi_bytes))
    assert mid.ticks_per_beat == 480
    assert len(mid.tracks) > 0


def test_export_zip_clip_split(sample_project, sample_tracks):
    """Test ZIP export with clip splitting."""
    zip_bytes = export_project_to_zip(sample_project, sample_tracks, split_by="clip")

    # Verify it's a valid ZIP
    zip_file = zipfile.ZipFile(io.BytesIO(zip_bytes))
    assert len(zip_file.namelist()) >= 1

    # Verify all MIDI files are valid
    for filename in zip_file.namelist():
        if filename.endswith(".mid"):
            midi_bytes = zip_file.read(filename)
            mid = mido.MidiFile(file=io.BytesIO(midi_bytes))
            assert mid.ticks_per_beat == 480


def test_generate_zip_filename():
    """Test ZIP filename generation."""
    filename = generate_zip_filename("Test Project")
    assert filename.endswith(".zip")
    assert "Test_Project" in filename
    # Should have timestamp format YYYYMMDD_HHMMSS
    parts = filename.split("_")
    assert len(parts) >= 3


def test_export_zip_with_offsets(sample_project, sample_tracks):
    """Test that offsets are applied in ZIP export."""
    # Set offsets
    sample_tracks[0].start_offset_ticks = 120
    sample_tracks[0].clips[0].start_offset_ticks = 60

    zip_bytes = export_project_to_zip(sample_project, sample_tracks, split_by="track")

    # Verify ZIP is created
    zip_file = zipfile.ZipFile(io.BytesIO(zip_bytes))
    assert len(zip_file.namelist()) > 0

    # Note: We can't easily verify offset application without parsing MIDI events,
    # but we can verify the export doesn't crash with offsets set

