"""Isolated, timeout-bounded parse/static-check/test validation."""

from __future__ import annotations

import ast
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from canarygraph.domain import MigrationPatch, MigrationStatus, ValidationResult


class ValidationPipeline:
    def __init__(self, *, timeout_seconds: int = 120) -> None:
        self.timeout_seconds = timeout_seconds

    def validate(
        self,
        repository: str | Path,
        patches: tuple[MigrationPatch, ...],
        *,
        run_mypy: bool = False,
        run_tests: bool = False,
    ) -> ValidationResult:
        root = Path(repository).resolve()
        for patch in patches:
            try:
                ast.parse(patch.after, filename=patch.path)
            except SyntaxError as exc:
                return ValidationResult(MigrationStatus.PARSE_FAILED, False, output=str(exc))

        with tempfile.TemporaryDirectory(prefix="canarygraph-") as directory:
            isolated = Path(directory) / "repository"
            shutil.copytree(root, isolated, symlinks=True)
            for patch in patches:
                source_path = Path(patch.path).resolve()
                try:
                    relative = source_path.relative_to(root)
                except ValueError:
                    return ValidationResult(
                        MigrationStatus.PARSE_FAILED,
                        False,
                        output=f"Patch path escapes repository: {source_path}",
                    )
                target = isolated / relative
                target.write_text(patch.after, encoding="utf-8")
            compile_result = self._run([sys.executable, "-m", "compileall", "-q", "."], isolated)
            if compile_result.returncode:
                return ValidationResult(
                    MigrationStatus.PARSE_FAILED, False, output=compile_result.stdout
                )
            mypy_success: bool | None = None
            if run_mypy:
                result = self._run([sys.executable, "-m", "mypy", "."], isolated)
                mypy_success = result.returncode == 0
                if not mypy_success:
                    return ValidationResult(
                        MigrationStatus.TYPE_CHECK_FAILED,
                        True,
                        False,
                        output=result.stdout,
                    )
            test_success: bool | None = None
            if run_tests:
                result = self._run([sys.executable, "-m", "pytest", "-q"], isolated)
                test_success = result.returncode == 0
                if not test_success:
                    return ValidationResult(
                        MigrationStatus.TEST_FAILED,
                        True,
                        mypy_success,
                        False,
                        result.stdout,
                    )
        return ValidationResult(
            MigrationStatus.VALIDATED,
            True,
            mypy_success,
            test_success,
            "Validation completed successfully",
        )

    def _run(self, command: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                command,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds,
                check=False,
                env={
                    "PATH": os.pathsep.join(
                        [str(Path(sys.executable).parent), "/usr/local/bin", "/usr/bin", "/bin"]
                    )
                },
            )
        except subprocess.TimeoutExpired as exc:
            return subprocess.CompletedProcess(command, 124, stdout=f"Timed out: {exc}", stderr="")
