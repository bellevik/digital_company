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
            prompt,
        ]
        completed = subprocess.run(
            command,
            capture_output=True,
            text=True,
            check=False,
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
