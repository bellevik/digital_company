from __future__ import annotations

import json
import os
import subprocess
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from app.config import Settings
from app.models.project import Project
from app.services.project_workspace import ProjectWorkspaceService

ProjectType = Literal["generic", "web"]
RuntimeStatus = Literal["running", "stopped", "not_configured"]

_GITIGNORE_LINES = [
    ".DS_Store",
    "__pycache__/",
    "*.pyc",
    "node_modules/",
    "dist/",
    "build/",
    ".vite/",
    ".cache/",
    "coverage/",
    "playwright-report/",
    "test-results/",
    ".playwright/",
    ".digital-company/runtime/",
]


@dataclass(slots=True)
class ProjectManifest:
    project_id: str
    project_type: ProjectType
    framework: str | None
    default_port: int | None


@dataclass(slots=True)
class ProjectRuntimeInfo:
    project_type: ProjectType
    framework: str | None
    runtime_status: RuntimeStatus
    port: int | None
    pid: int | None
    proxy_path: str | None
    local_url: str | None
    log_path: str | None
    scripts: dict[str, str | None]


class ProjectRuntimeService:
    def __init__(self, *, settings: Settings):
        self._settings = settings
        self._workspace_service = ProjectWorkspaceService(settings=settings)

    def bootstrap_project(
        self,
        *,
        project: Project,
        requested_type: ProjectType | None = None,
    ) -> ProjectRuntimeInfo:
        directory = self._workspace_service.ensure_project_directory(project.id)
        assert directory is not None

        manifest = self._ensure_manifest(
            project=project,
            project_directory=directory,
            requested_type=requested_type,
        )
        self._ensure_gitignore(project_directory=directory)
        self._ensure_readme(project=project, project_directory=directory, manifest=manifest)
        if manifest.project_type == "web":
            self._ensure_web_runtime_scaffold(project_directory=directory, manifest=manifest)

        return self.describe_project(project_id=project.id)

    def describe_project(self, *, project_id: str) -> ProjectRuntimeInfo:
        directory = self._workspace_service.ensure_project_directory(project_id)
        assert directory is not None
        manifest = self._read_manifest(project_directory=directory)
        if manifest is None:
            inferred_type = self._infer_project_type(project_directory=directory)
            manifest = self._write_manifest(
                project_directory=directory,
                manifest=ProjectManifest(
                    project_id=project_id,
                    project_type=inferred_type,
                    framework=self._detect_framework(project_directory=directory),
                    default_port=self._default_port(project_id),
                ),
            )
            self._ensure_gitignore(project_directory=directory)
            if manifest.project_type == "web":
                self._ensure_web_runtime_scaffold(project_directory=directory, manifest=manifest)

        runtime_status, pid = self._process_state(project_directory=directory)
        port = manifest.default_port if manifest.project_type == "web" else None
        log_path = self._runtime_log_path(project_directory=directory)
        has_web_scripts = (directory / "scripts" / "START").exists()
        return ProjectRuntimeInfo(
            project_type=manifest.project_type,
            framework=manifest.framework,
            runtime_status=(
                "not_configured"
                if manifest.project_type == "generic" or not has_web_scripts
                else runtime_status
            ),
            port=port,
            pid=pid,
            proxy_path=f"/project-apps/{project_id}/" if manifest.project_type == "web" else None,
            local_url=(
                f"http://{self._settings.project_runtime_host}:{port}/"
                if manifest.project_type == "web" and port is not None
                else None
            ),
            log_path=str(log_path.relative_to(directory)) if log_path.exists() else None,
            scripts={
                "start": self._script_relative_path(directory / "scripts" / "START", directory),
                "stop": self._script_relative_path(directory / "scripts" / "STOP", directory),
                "restart": self._script_relative_path(directory / "scripts" / "RESTART", directory),
                "status": self._script_relative_path(directory / "scripts" / "STATUS", directory),
            },
        )

    def start(self, *, project: Project) -> ProjectRuntimeInfo:
        info = self.bootstrap_project(project=project)
        directory = self._workspace_service.ensure_project_directory(project.id)
        assert directory is not None
        if info.project_type != "web":
            raise ValueError("project_is_not_web")
        if info.runtime_status == "running":
            return info
        self._run_script(script_path=directory / "scripts" / "START", project_directory=directory)
        return self.describe_project(project_id=project.id)

    def stop(self, *, project: Project) -> ProjectRuntimeInfo:
        info = self.bootstrap_project(project=project)
        directory = self._workspace_service.ensure_project_directory(project.id)
        assert directory is not None
        if info.project_type != "web":
            raise ValueError("project_is_not_web")
        self._run_script(script_path=directory / "scripts" / "STOP", project_directory=directory)
        return self.describe_project(project_id=project.id)

    def restart(self, *, project: Project) -> ProjectRuntimeInfo:
        self.bootstrap_project(project=project)
        directory = self._workspace_service.ensure_project_directory(project.id)
        assert directory is not None
        info = self.describe_project(project_id=project.id)
        if info.project_type != "web":
            raise ValueError("project_is_not_web")
        self._run_script(script_path=directory / "scripts" / "RESTART", project_directory=directory)
        return self.describe_project(project_id=project.id)

    def proxy_target(self, *, project_id: str) -> str:
        info = self.describe_project(project_id=project_id)
        if info.project_type != "web":
            raise ValueError("project_is_not_web")
        if info.runtime_status != "running" or info.local_url is None:
            raise ValueError("project_app_not_running")
        return info.local_url.rstrip("/")

    def _ensure_manifest(
        self,
        *,
        project: Project,
        project_directory: Path,
        requested_type: ProjectType | None,
    ) -> ProjectManifest:
        existing = self._read_manifest(project_directory=project_directory)
        project_type = (
            existing.project_type
            if existing is not None
            else requested_type or self._infer_project_type(project_directory=project_directory)
        )
        framework = self._detect_framework(project_directory=project_directory)
        default_port = existing.default_port if existing is not None else self._default_port(project.id)
        return self._write_manifest(
            project_directory=project_directory,
            manifest=ProjectManifest(
                project_id=project.id,
                project_type=project_type,
                framework=framework,
                default_port=default_port,
            ),
        )

    def _ensure_gitignore(self, *, project_directory: Path) -> None:
        gitignore_path = project_directory / ".gitignore"
        existing_lines = gitignore_path.read_text().splitlines() if gitignore_path.exists() else []
        missing_lines = [line for line in _GITIGNORE_LINES if line not in existing_lines]
        if not gitignore_path.exists():
            content = ["# Managed by Digital Company", *sorted(_GITIGNORE_LINES)]
            gitignore_path.write_text("\n".join(content) + "\n")
            return
        if missing_lines:
            with gitignore_path.open("a", encoding="utf-8") as handle:
                handle.write("\n# Managed by Digital Company\n")
                for line in missing_lines:
                    handle.write(f"{line}\n")

    def _ensure_readme(
        self,
        *,
        project: Project,
        project_directory: Path,
        manifest: ProjectManifest,
    ) -> None:
        readme_path = project_directory / "README.md"
        if readme_path.exists():
            return
        content = [
            f"# {project.name}",
            "",
            project.description or "Project scaffolded by Digital Company.",
            "",
            f"- Project ID: `{project.id}`",
            f"- Type: `{manifest.project_type}`",
        ]
        if manifest.project_type == "web":
            content.extend(
                [
                    f"- Default port: `{manifest.default_port}`",
                    "",
                    "## Local scripts",
                    "",
                    "- `./scripts/START`",
                    "- `./scripts/STOP`",
                    "- `./scripts/RESTART`",
                    "- `./scripts/STATUS`",
                ]
            )
        readme_path.write_text("\n".join(content) + "\n", encoding="utf-8")

    def _ensure_web_runtime_scaffold(
        self,
        *,
        project_directory: Path,
        manifest: ProjectManifest,
    ) -> None:
        scripts_dir = project_directory / "scripts"
        scripts_dir.mkdir(parents=True, exist_ok=True)
        runtime_dir = project_directory / ".digital-company" / "runtime"
        runtime_dir.mkdir(parents=True, exist_ok=True)

        framework = manifest.framework or "web"
        port = manifest.default_port or self._default_port(manifest.project_id)
        start_body = self._start_script_body(framework=framework, port=port)
        for filename, content in {
            "START": start_body,
            "STOP": self._stop_script_body(port=port),
            "RESTART": self._restart_script_body(),
            "STATUS": self._status_script_body(port=port),
        }.items():
            script_path = scripts_dir / filename
            if not script_path.exists():
                script_path.write_text(content, encoding="utf-8")
                script_path.chmod(0o755)

    def _read_manifest(self, *, project_directory: Path) -> ProjectManifest | None:
        manifest_path = project_directory / ".digital-company" / "project.json"
        if not manifest_path.exists():
            return None
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        return ProjectManifest(
            project_id=payload["project_id"],
            project_type=payload["project_type"],
            framework=payload.get("framework"),
            default_port=payload.get("default_port"),
        )

    def _write_manifest(
        self,
        *,
        project_directory: Path,
        manifest: ProjectManifest,
    ) -> ProjectManifest:
        manifest_path = project_directory / ".digital-company" / "project.json"
        manifest_path.parent.mkdir(parents=True, exist_ok=True)
        manifest_path.write_text(
            json.dumps(
                {
                    "project_id": manifest.project_id,
                    "project_type": manifest.project_type,
                    "framework": manifest.framework,
                    "default_port": manifest.default_port,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return manifest

    def _infer_project_type(self, *, project_directory: Path) -> ProjectType:
        if (project_directory / "package.json").exists():
            return "web"
        if (project_directory / "index.html").exists():
            return "web"
        return "generic"

    def _detect_framework(self, *, project_directory: Path) -> str | None:
        package_json_path = project_directory / "package.json"
        if not package_json_path.exists():
            return None
        try:
            payload = json.loads(package_json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return "web"
        dependencies = {
            **payload.get("dependencies", {}),
            **payload.get("devDependencies", {}),
        }
        if "next" in dependencies:
            return "nextjs"
        if "vite" in dependencies:
            return "vite"
        if "react-scripts" in dependencies:
            return "cra"
        return "web"

    def _default_port(self, project_id: str) -> int:
        return self._settings.project_runtime_base_port + (zlib.crc32(project_id.encode("utf-8")) % 500)

    def _run_script(self, *, script_path: Path, project_directory: Path) -> None:
        if not script_path.exists():
            raise ValueError("project_runtime_not_configured")
        subprocess.run(
            ["/bin/bash", str(script_path)],
            cwd=project_directory,
            check=True,
            env={**os.environ},
            capture_output=True,
            text=True,
        )

    def _process_state(self, *, project_directory: Path) -> tuple[RuntimeStatus, int | None]:
        pid_path = self._runtime_pid_path(project_directory=project_directory)
        if not pid_path.exists():
            return "stopped", None
        try:
            pid = int(pid_path.read_text(encoding="utf-8").strip())
        except ValueError:
            pid_path.unlink(missing_ok=True)
            return "stopped", None
        try:
            os.kill(pid, 0)
        except OSError:
            pid_path.unlink(missing_ok=True)
            return "stopped", None
        return "running", pid

    def _runtime_pid_path(self, *, project_directory: Path) -> Path:
        return project_directory / ".digital-company" / "runtime" / "app.pid"

    def _runtime_log_path(self, *, project_directory: Path) -> Path:
        return project_directory / ".digital-company" / "runtime" / "app.log"

    def _script_relative_path(self, script_path: Path, project_directory: Path) -> str | None:
        return str(script_path.relative_to(project_directory)) if script_path.exists() else None

    def _start_script_body(self, *, framework: str, port: int) -> str:
        command = {
            "vite": 'npm run dev -- --host 0.0.0.0 --port "$PORT"',
            "nextjs": 'npm run dev -- --hostname 0.0.0.0 --port "$PORT"',
            "cra": 'HOST=0.0.0.0 PORT="$PORT" npm start',
        }.get(framework, 'npm run dev -- --host 0.0.0.0 --port "$PORT"')
        return f"""#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${{SCRIPT_DIR}}/.." && pwd)"
RUNTIME_DIR="${{PROJECT_ROOT}}/.digital-company/runtime"
PID_FILE="${{RUNTIME_DIR}}/app.pid"
LOG_FILE="${{RUNTIME_DIR}}/app.log"
PORT="${{PORT:-{port}}}"

mkdir -p "${{RUNTIME_DIR}}"

if [[ -f "${{PID_FILE}}" ]] && kill -0 "$(cat "${{PID_FILE}}")" 2>/dev/null; then
  echo "Project app is already running on port $PORT"
  exit 0
fi

if [[ ! -f "${{PROJECT_ROOT}}/package.json" ]]; then
  echo "This web project is missing package.json"
  exit 1
fi

if ! command -v npm >/dev/null 2>&1; then
  echo "npm is required to run this web project."
  exit 1
fi

if [[ ! -d "${{PROJECT_ROOT}}/node_modules" ]]; then
  if [[ -f "${{PROJECT_ROOT}}/package-lock.json" ]]; then
    npm ci
  else
    npm install
  fi
fi

cd "${{PROJECT_ROOT}}"
nohup /bin/bash -lc "{command}" >"${{LOG_FILE}}" 2>&1 &
echo $! > "${{PID_FILE}}"
echo "Started project app on port $PORT"
"""

    def _stop_script_body(self, *, port: int) -> str:
        return f"""#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${{SCRIPT_DIR}}/.." && pwd)"
PID_FILE="${{PROJECT_ROOT}}/.digital-company/runtime/app.pid"
PORT="${{PORT:-{port}}}"

if [[ ! -f "${{PID_FILE}}" ]]; then
  echo "Project app is not running."
  exit 0
fi

PID="$(cat "${{PID_FILE}}")"
if kill -0 "${{PID}}" 2>/dev/null; then
  kill "${{PID}}"
  sleep 1
  if kill -0 "${{PID}}" 2>/dev/null; then
    kill -9 "${{PID}}"
  fi
fi

rm -f "${{PID_FILE}}"
echo "Stopped project app on port $PORT"
"""

    def _restart_script_body(self) -> str:
        return """#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
"${SCRIPT_DIR}/STOP"
"${SCRIPT_DIR}/START"
"""

    def _status_script_body(self, *, port: int) -> str:
        host = self._settings.project_runtime_host
        return f"""#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(cd "${{SCRIPT_DIR}}/.." && pwd)"
PID_FILE="${{PROJECT_ROOT}}/.digital-company/runtime/app.pid"
PORT="${{PORT:-{port}}}"

if [[ -f "${{PID_FILE}}" ]] && kill -0 "$(cat "${{PID_FILE}}")" 2>/dev/null; then
  echo "running"
  echo "pid=$(cat "${{PID_FILE}}")"
  echo "url=http://{host}:$PORT/"
else
  echo "stopped"
fi
"""
