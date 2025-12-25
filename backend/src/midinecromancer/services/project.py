"""Project service."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from midinecromancer.models.project import Project
from midinecromancer.models.track import Track
from midinecromancer.schemas.project import ProjectCreate, ProjectUpdate


class ProjectService:
    """Service for project operations."""

    def __init__(self, session: AsyncSession):
        """Initialize service with database session."""
        self.session = session

    async def create(self, data: ProjectCreate) -> Project:
        """Create a new project."""
        project = Project(**data.model_dump())
        self.session.add(project)
        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def get(self, project_id: UUID) -> Project | None:
        """Get project by ID."""
        result = await self.session.execute(select(Project).where(Project.id == project_id))
        return result.scalar_one_or_none()

    async def list(self) -> list[Project]:
        """List all projects."""
        result = await self.session.execute(select(Project).order_by(Project.created_at.desc()))
        return list(result.scalars().all())

    async def update(self, project_id: UUID, data: ProjectUpdate) -> Project | None:
        """Update project."""
        project = await self.get(project_id)
        if not project:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(project, key, value)

        await self.session.commit()
        await self.session.refresh(project)
        return project

    async def get_with_tracks(self, project_id: UUID) -> tuple[Project | None, list[Track]]:
        """Get project with all tracks."""
        project = await self.get(project_id)
        if not project:
            return None, []

        result = await self.session.execute(
            select(Track).where(Track.project_id == project_id).order_by(Track.created_at)
        )
        tracks = list(result.scalars().all())
        return project, tracks
