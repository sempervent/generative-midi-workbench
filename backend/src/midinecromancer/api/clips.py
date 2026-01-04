"""Clip endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from midinecromancer.db.base import get_session
from midinecromancer.models.clip import Clip
from midinecromancer.schemas.clip import ClipResponse

router = APIRouter()


class ClipUpdate(BaseModel):
    """Update clip fields."""

    start_bar: int | None = None
    length_bars: int | None = None
    is_muted: bool | None = None
    intensity: float | None = None
    params: dict | None = None


class ClipDuplicate(BaseModel):
    """Duplicate clip request."""

    new_start_bar: int | None = None


class ClipTimeScale(BaseModel):
    """Time scale clip request."""

    mode: str  # "half" or "double"


class ClipOffset(BaseModel):
    """Offset clip request."""

    bars: int


class ClipRegenerate(BaseModel):
    """Regenerate clip request."""

    kind: str  # "beats"|"chords"|"bass"|"melody"
    seed: int | None = None
    variation: float = 0.3  # 0-1
    params: dict = {}  # Type-specific parameters
    preview: bool = False


@router.patch("/{clip_id}/mute", response_model=ClipResponse)
async def toggle_clip_mute(
    clip_id: UUID,
    muted: bool,
    session: AsyncSession = Depends(get_session),
) -> ClipResponse:
    """Toggle clip mute state."""
    clip = await session.get(Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    clip.is_muted = muted
    await session.commit()
    await session.refresh(clip)
    return ClipResponse.model_validate(clip)


@router.patch("/{clip_id}/solo", response_model=ClipResponse)
async def toggle_clip_solo(
    clip_id: UUID,
    soloed: bool,
    session: AsyncSession = Depends(get_session),
) -> ClipResponse:
    """Toggle clip solo state."""
    clip = await session.get(Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")
    clip.is_soloed = soloed
    await session.commit()
    await session.refresh(clip)
    return ClipResponse.model_validate(clip)


@router.patch("/{clip_id}", response_model=ClipResponse)
async def update_clip(
    clip_id: UUID,
    data: ClipUpdate,
    session: AsyncSession = Depends(get_session),
) -> ClipResponse:
    """Update clip parameters."""
    clip = await session.get(Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    if data.start_bar is not None:
        clip.start_bar = data.start_bar
    if data.length_bars is not None:
        clip.length_bars = max(1, data.length_bars)  # Minimum 1 bar
    if data.is_muted is not None:
        clip.is_muted = data.is_muted
    if data.intensity is not None:
        clip.intensity = max(0.0, min(2.0, data.intensity))  # Clamp 0-2
    if data.params is not None:
        clip.params = data.params

    await session.commit()
    await session.refresh(clip)
    return ClipResponse.model_validate(clip)


@router.post("/{clip_id}/duplicate", response_model=ClipResponse, status_code=201)
async def duplicate_clip(
    clip_id: UUID,
    data: ClipDuplicate,
    session: AsyncSession = Depends(get_session),
) -> ClipResponse:
    """Duplicate a clip with optional new start bar."""
    clip = await session.get(Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    # Create new clip with same properties
    new_clip = Clip(
        track_id=clip.track_id,
        start_bar=data.new_start_bar if data.new_start_bar is not None else clip.start_bar,
        length_bars=clip.length_bars,
        grid_mode=clip.grid_mode,
        polyrhythm_profile_id=clip.polyrhythm_profile_id,
        is_muted=clip.is_muted,
        is_soloed=clip.is_soloed,
        start_offset_ticks=clip.start_offset_ticks,
        intensity=getattr(clip, "intensity", 1.0),
        params=getattr(clip, "params", {}).copy(),
    )
    session.add(new_clip)
    await session.flush()

    # Copy notes
    from midinecromancer.models.note import Note

    for note in clip.notes:
        new_note = Note(
            clip_id=new_clip.id,
            pitch=note.pitch,
            velocity=note.velocity,
            start_tick=note.start_tick,
            duration_tick=note.duration_tick,
            probability=note.probability,
        )
        session.add(new_note)

    # Copy chord events
    from midinecromancer.models.chord_event import ChordEvent

    for chord_event in clip.chord_events:
        new_chord = ChordEvent(
            clip_id=new_clip.id,
            start_tick=chord_event.start_tick,
            duration_tick=chord_event.duration_tick,
            duration_beats=chord_event.duration_beats,
            roman_numeral=chord_event.roman_numeral,
            chord_name=chord_event.chord_name,
            intensity=chord_event.intensity,
            voicing=chord_event.voicing,
            inversion=chord_event.inversion,
            strum_ms=chord_event.strum_ms,
            humanize_ms=chord_event.humanize_ms,
            velocity_jitter=chord_event.velocity_jitter,
            timing_jitter_ms=chord_event.timing_jitter_ms,
            is_enabled=chord_event.is_enabled,
            is_locked=chord_event.is_locked,
            grid_quantum=chord_event.grid_quantum,
        )
        session.add(new_chord)

    await session.commit()
    await session.refresh(new_clip)
    return ClipResponse.model_validate(new_clip)


@router.post("/{clip_id}/time-scale", response_model=ClipResponse)
async def time_scale_clip(
    clip_id: UUID,
    data: ClipTimeScale,
    session: AsyncSession = Depends(get_session),
) -> ClipResponse:
    """Scale clip timing: half (2x length) or double (0.5x length)."""
    clip = await session.get(Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    if data.mode == "half":
        # Double the length (half speed)
        clip.length_bars = max(1, clip.length_bars * 2)
        # Scale rhythm density params if present
        if clip.params and "density" in clip.params:
            clip.params["density"] = clip.params["density"] * 0.5
    elif data.mode == "double":
        # Halve the length (double speed)
        clip.length_bars = max(1, clip.length_bars // 2)
        # Scale rhythm density params if present
        if clip.params and "density" in clip.params:
            clip.params["density"] = min(1.0, clip.params["density"] * 2.0)
    else:
        raise HTTPException(status_code=400, detail="mode must be 'half' or 'double'")

    await session.commit()
    await session.refresh(clip)
    return ClipResponse.model_validate(clip)


@router.post("/{clip_id}/offset", response_model=ClipResponse)
async def offset_clip(
    clip_id: UUID,
    data: ClipOffset,
    session: AsyncSession = Depends(get_session),
) -> ClipResponse:
    """Shift clip start bar by offset (with bounds checking)."""
    clip = await session.get(Clip, clip_id)
    if not clip:
        raise HTTPException(status_code=404, detail="Clip not found")

    new_start_bar = clip.start_bar + data.bars
    if new_start_bar < 0:
        raise HTTPException(status_code=400, detail="Cannot offset clip to negative bar")

    clip.start_bar = new_start_bar
    await session.commit()
    await session.refresh(clip)
    return ClipResponse.model_validate(clip)


@router.post("/{clip_id}/regenerate")
async def regenerate_clip(
    clip_id: UUID,
    data: ClipRegenerate,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Regenerate clip content with preview support."""
    from midinecromancer.services.regenerate import RegenerateService

    service = RegenerateService(session)
    try:
        result = await service.regenerate_clip(
            clip_id=clip_id,
            kind=data.kind,
            seed=data.seed,
            variation=data.variation,
            params=data.params,
            preview=data.preview,
        )
        if not data.preview:
            await session.commit()
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        await session.rollback()
        raise HTTPException(status_code=500, detail=f"Regeneration failed: {str(e)}")


@router.post("/{clip_id}/preview-regenerate")
async def preview_regenerate_clip(
    clip_id: UUID,
    data: ClipRegenerate,
    session: AsyncSession = Depends(get_session),
) -> dict:
    """Preview regenerate clip content without DB writes."""
    from midinecromancer.services.regenerate import RegenerateService

    service = RegenerateService(session)
    try:
        result = await service.regenerate_clip(
            clip_id=clip_id,
            kind=data.kind,
            seed=data.seed,
            variation=data.variation,
            params=data.params,
            preview=True,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Preview failed: {str(e)}")
