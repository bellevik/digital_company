from __future__ import annotations

import re
from pathlib import Path

from app.config import Settings

_VALID_PROJECT_ID = re.compile(r"^[A-Za-z0-9._-]+$")


class ProjectWorkspaceService:
    def __init__(self, *, settings: Settings):
        self._settings = settings

    def ensure_root(self) -> Path:
        root = self._settings.resolved_projects_root
        root.mkdir(parents=True, exist_ok=True)
        gitkeep = root / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
        return root

    def ensure_project_directory(self, project_id: str | None) -> Path | None:
        normalized_project_id = self.normalize_project_id(project_id)
        if normalized_project_id is None:
            self.ensure_root()
            return None

        project_directory = self.ensure_root() / normalized_project_id
        project_directory.mkdir(parents=True, exist_ok=True)
        gitkeep = project_directory / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
        return project_directory

    @staticmethod
    def normalize_project_id(project_id: str | None) -> str | None:
        if project_id is None:
            return None

        normalized = project_id.strip()
        if not normalized:
            return None

        if not _VALID_PROJECT_ID.fullmatch(normalized):
            raise ValueError(
                "project_id must use only letters, numbers, dots, underscores, or hyphens"
            )

        return normalized
