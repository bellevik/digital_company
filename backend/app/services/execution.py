from __future__ import annotations

import subprocess
from dataclasses import dataclass
from typing import Protocol

from app.config import Settings


@dataclass(slots=True)
class ExecutionResult:
    stdout: str
    stderr: str
    exit_code: int
    command: list[str]


class ExecutionAdapter(Protocol):
    def run(self, *, prompt: str) -> ExecutionResult:
        ...


class CodexCLIExecutionAdapter:
    def __init__(self, settings: Settings):
        self._settings = settings

    def run(self, *, prompt: str) -> ExecutionResult:
        command = [
            self._settings.codex_cli_command,
            self._settings.codex_cli_subcommand,
            self._settings.codex_cli_full_auto_flag,
            "-C",
            str(self._settings.resolved_codex_workdir),
            prompt,
        ]
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
        return ExecutionResult(
            stdout=completed.stdout,
            stderr=completed.stderr,
            exit_code=completed.returncode,
            command=command,
        )


class MockExecutionAdapter:
    def run(self, *, prompt: str) -> ExecutionResult:
        return ExecutionResult(
            stdout=(
                '{"summary":"Mock execution completed.","memory_summary":"Mock run",'
                '"memory_content":"Mock backend configured without Codex CLI.",'
                '"follow_up_tasks":[]}'
            ),
            stderr="",
            exit_code=0,
            command=["mock-executor", prompt],
        )
