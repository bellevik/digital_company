from __future__ import annotations

import logging
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from app.config import Settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ExecutionResult:
    stdout: str
    stderr: str
    exit_code: int
    command: list[str]


class ExecutionAdapter(Protocol):
    def run(self, *, prompt: str, workdir: Path | None = None) -> ExecutionResult:
        ...


class CodexCLIExecutionAdapter:
    def __init__(self, settings: Settings):
        self._settings = settings

    def run(self, *, prompt: str, workdir: Path | None = None) -> ExecutionResult:
        command_workdir = workdir or self._settings.resolved_codex_workdir
        command = [
            self._settings.codex_cli_command,
            self._settings.codex_cli_subcommand,
            self._settings.codex_cli_full_auto_flag,
            "-C",
            str(command_workdir),
        ]
        if command_workdir != self._settings.resolved_codex_workdir:
            command.extend(["--add-dir", str(self._settings.resolved_codex_workdir)])
        command.append(prompt)
        logger.info(
            "Running Codex CLI",
            extra={
                "command": command[:-1],
                "workdir": str(command_workdir),
                "prompt_length": len(prompt),
            },
        )
        try:
            completed = subprocess.run(
                command,
                capture_output=True,
                input="",
                text=True,
                check=False,
            )
        except FileNotFoundError:
            return ExecutionResult(
                stdout="",
                stderr=(
                    f"Execution backend is codex_cli, but '{self._settings.codex_cli_command}' "
                    "is not installed in this runtime. Set CODEX_EXECUTION_BACKEND=mock for "
                    "local Docker testing, or install/mount the Codex CLI into the backend container."
                ),
                exit_code=127,
                command=command,
            )
        logger.info(
            "Codex CLI finished",
            extra={
                "workdir": str(command_workdir),
                "exit_code": completed.returncode,
                "stdout_length": len(completed.stdout),
                "stderr_length": len(completed.stderr),
            },
        )
        return ExecutionResult(
            stdout=completed.stdout,
            stderr=completed.stderr,
            exit_code=completed.returncode,
            command=command,
        )


class MockExecutionAdapter:
    def run(self, *, prompt: str, workdir: Path | None = None) -> ExecutionResult:
        return ExecutionResult(
            stdout=(
                '{"summary":"Mock execution completed.","memory_summary":"Mock run",'
                '"memory_content":"Mock backend configured without Codex CLI.",'
                '"artifact_paths":["mock-output.txt"],'
                '"follow_up_tasks":[]}'
            ),
            stderr="",
            exit_code=0,
            command=["mock-executor", str(workdir) if workdir is not None else "", prompt],
        )
