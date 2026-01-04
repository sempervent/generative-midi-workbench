"""Music theory endpoints for chord suggestions and diatonic chords."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from midinecromancer.db.base import get_session
from midinecromancer.models.project import Project
from midinecromancer.music.theory import Mode, roman_to_degree

router = APIRouter()


class DiatonicChord(BaseModel):
    """Diatonic chord info."""

    roman_numeral: str
    chord_name: str
    degree: int
    function: str  # T, PD, D, etc.
    tension: float  # 0-1, how much tension this chord creates


def _roman_to_chord_name(roman: str, tonic: str, mode: Mode) -> str:
    """Convert roman numeral to chord name."""
    degree = roman_to_degree(roman)
    tonic_pc_map = {
        "C": 0,
        "C#": 1,
        "D": 2,
        "D#": 3,
        "E": 4,
        "F": 5,
        "F#": 6,
        "G": 7,
        "G#": 8,
        "A": 9,
        "A#": 10,
        "B": 11,
        "Bb": 10,
        "Eb": 3,
        "Ab": 8,
        "Db": 1,
        "Gb": 6,
    }
    tonic_pc = tonic_pc_map.get(tonic, 0)
    intervals = {
        "ionian": [0, 2, 4, 5, 7, 9, 11],
        "dorian": [0, 2, 3, 5, 7, 9, 10],
        "phrygian": [0, 1, 3, 5, 7, 8, 10],
        "lydian": [0, 2, 4, 6, 7, 9, 11],
        "mixolydian": [0, 2, 4, 5, 7, 9, 10],
        "aeolian": [0, 2, 3, 5, 7, 8, 10],
        "locrian": [0, 1, 3, 5, 6, 8, 10],
    }
    mode_intervals = intervals.get(mode, intervals["ionian"])
    root_pc = (tonic_pc + mode_intervals[degree - 1]) % 12

    pc_names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    root_name = pc_names[root_pc]

    # Determine quality based on mode
    if mode == "ionian":
        qualities = {1: "", 2: "m", 3: "m", 4: "", 5: "", 6: "m", 7: "dim"}
    elif mode == "aeolian":
        qualities = {1: "m", 2: "dim", 3: "", 4: "m", 5: "m", 6: "", 7: ""}
    else:
        # Default for other modes
        qualities = {1: "", 2: "m", 3: "m", 4: "", 5: "", 6: "m", 7: "dim"}

    quality = qualities.get(degree, "")
    if "7" in roman:
        quality += "7"

    return root_name + quality


@router.get("/theory/chords", response_model=list[DiatonicChord])
async def get_diatonic_chords(
    project_id: UUID = Query(...),
    include_borrowed: bool = Query(False),
    session: AsyncSession = Depends(get_session),
) -> list[DiatonicChord]:
    """Get diatonic chords for a project's key/mode.

    Args:
        project_id: Project ID
        include_borrowed: Include borrowed chords from parallel/relative keys

    Returns:
        List of diatonic chords with roman numerals, names, functions, tension
    """
    project = await session.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    tonic = project.key_tonic
    mode: Mode = project.mode  # type: ignore

    # Define diatonic chords by mode
    if mode == "ionian":
        # Major key: I, ii, iii, IV, V, vi, vii°
        romans = ["I", "ii", "iii", "IV", "V", "vi", "vii°"]
        functions = ["T", "PD", "T", "PD", "D", "T", "D"]
        tensions = [0.0, 0.3, 0.2, 0.4, 0.7, 0.1, 0.9]
    elif mode == "aeolian":
        # Minor key: i, ii°, III, iv, v, VI, VII
        romans = ["i", "ii°", "III", "iv", "v", "VI", "VII"]
        functions = ["T", "PD", "T", "PD", "D", "T", "D"]
        tensions = [0.0, 0.4, 0.2, 0.3, 0.6, 0.1, 0.8]
    else:
        # Default for other modes (simplified)
        romans = ["I", "ii", "iii", "IV", "V", "vi", "vii"]
        functions = ["T", "PD", "T", "PD", "D", "T", "D"]
        tensions = [0.0, 0.3, 0.2, 0.4, 0.7, 0.1, 0.8]

    chords = []
    for i, roman in enumerate(romans):
        chord_name = _roman_to_chord_name(roman, tonic, mode)
        chords.append(
            DiatonicChord(
                roman_numeral=roman,
                chord_name=chord_name,
                degree=i + 1,
                function=functions[i],
                tension=tensions[i],
            )
        )

    # Add borrowed chords if requested
    if include_borrowed:
        # Common borrowed chords
        if mode == "ionian":
            # Borrow from parallel minor: bVII, bVI, iv
            borrowed = [
                ("bVII", "T", 0.5),
                ("bVI", "T", 0.4),
                ("iv", "PD", 0.3),
            ]
        elif mode == "aeolian":
            # Borrow from parallel major: V, IV
            borrowed = [
                ("V", "D", 0.7),
                ("IV", "PD", 0.4),
            ]
        else:
            borrowed = []

        for roman, func, tension in borrowed:
            chord_name = _roman_to_chord_name(roman, tonic, mode)
            chords.append(
                DiatonicChord(
                    roman_numeral=roman,
                    chord_name=chord_name,
                    degree=0,  # Borrowed, no degree
                    function=func,
                    tension=tension,
                )
            )

    return chords
