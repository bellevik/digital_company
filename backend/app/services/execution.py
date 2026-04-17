from __future__ import annotations

import logging
import selectors
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Protocol

from app.config import Settings

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ExecutionResult:
    stdout: str
    stderr: str
    exit_code: int
    command: list[str]


OutputCallback = Callable[[str, str], None]


class ExecutionAdapter(Protocol):
    def run(
        self,
        *,
        prompt: str,
        workdir: Path | None = None,
        on_output: OutputCallback | None = None,
    ) -> ExecutionResult:
        ...


class CodexCLIExecutionAdapter:
    def __init__(self, settings: Settings):
        self._settings = settings

    def run(
        self,
        *,
        prompt: str,
        workdir: Path | None = None,
        on_output: OutputCallback | None = None,
    ) -> ExecutionResult:
        command_workdir = workdir or self._settings.resolved_codex_workdir
        command = [
            self._settings.codex_cli_command,
            "-a",
            self._settings.codex_cli_approval_policy,
            self._settings.codex_cli_subcommand,
            "-s",
            self._settings.codex_cli_sandbox_mode,
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
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                stdin=subprocess.DEVNULL,
                bufsize=1,
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

        stdout_parts: list[str] = []
        stderr_parts: list[str] = []
        selector = selectors.DefaultSelector()
        if process.stdout is not None:
            selector.register(process.stdout, selectors.EVENT_READ, ("stdout", stdout_parts))
        if process.stderr is not None:
            selector.register(process.stderr, selectors.EVENT_READ, ("stderr", stderr_parts))

        while selector.get_map():
            for key, _ in selector.select():
                stream_name, sink = key.data
                chunk = key.fileobj.readline()
                if chunk == "":
                    selector.unregister(key.fileobj)
                    key.fileobj.close()
                    continue
                sink.append(chunk)
                if on_output is not None:
                    on_output(stream_name, chunk)

        return_code = process.wait()
        stdout = "".join(stdout_parts)
        stderr = "".join(stderr_parts)
        logger.info(
            "Codex CLI finished",
            extra={
                "workdir": str(command_workdir),
                "exit_code": return_code,
                "stdout_length": len(stdout),
                "stderr_length": len(stderr),
            },
        )
        return ExecutionResult(
            stdout=stdout,
            stderr=stderr,
            exit_code=return_code,
            command=command,
        )


class MockExecutionAdapter:
    def run(
        self,
        *,
        prompt: str,
        workdir: Path | None = None,
        on_output: OutputCallback | None = None,
    ) -> ExecutionResult:
        stdout = (
            '{"summary":"Mock execution completed.","memory_summary":"Mock run",'
            '"memory_content":"Mock backend configured without Codex CLI.",'
            '"artifact_paths":["mock-output.txt"],'
            '"follow_up_tasks":[]}'
        )
        stderr = ""
        if on_output is not None:
            on_output("stderr", "Mock executor starting...\n")
            on_output("stdout", stdout)
        return ExecutionResult(
            stdout=stdout,
            stderr=stderr,
            exit_code=0,
            command=["mock-executor", str(workdir) if workdir is not None else "", prompt],
        )
