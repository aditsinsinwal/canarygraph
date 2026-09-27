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
        run_ruff: bool = False,
        run_mypy: bool = False,
        run_tests: bool = False,
    ) -> ValidationResult:
        root = Path(repository).resolve()
        if not root.is_dir():
            return ValidationResult(
                MigrationStatus.UNSUPPORTED,
                False,
                output=f"Repository is not a directory: {root}",
            )
        if not patches:
            return ValidationResult(
                MigrationStatus.UNSUPPORTED,
                False,
                output="Migration has no source patches to validate",
            )
        escaped_symlink = self._external_symlink(root)
        if escaped_symlink:
            return ValidationResult(
                MigrationStatus.UNSUPPORTED,
                False,
                output=f"Repository contains a symlink escaping its root: {escaped_symlink}",
            )
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
                    MigrationStatus.PARSE_FAILED,
                    False,
                    output=self._output(compile_result),
                )
            static_success: bool | None = None
            if run_ruff:
                result = self._run([sys.executable, "-m", "ruff", "check", "."], isolated)
                static_success = result.returncode == 0
                if not static_success:
                    return ValidationResult(
                        MigrationStatus.TYPE_CHECK_FAILED,
                        True,
                        output=self._output(result),
                        static_check_succeeded=False,
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
                        output=self._output(result),
                        static_check_succeeded=static_success,
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
                        self._output(result),
                        static_success,
                    )
        return ValidationResult(
            MigrationStatus.VALIDATED,
            True,
            mypy_success,
            test_success,
            "Validation completed successfully",
            static_success,
        )

    @staticmethod
    def _external_symlink(root: Path) -> Path | None:
        for path in root.rglob("*"):
            if not path.is_symlink():
                continue
            try:
                path.resolve().relative_to(root)
            except (OSError, ValueError):
                return path
        return None

    @staticmethod
    def _output(result: subprocess.CompletedProcess[str]) -> str:
        return (result.stdout + result.stderr)[-20_000:]

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
                    ),
                    "PYTHONNOUSERSITE": "1",
                    "PYTHONHASHSEED": "0",
                    "LANG": "C.UTF-8",
                },
            )
        except subprocess.TimeoutExpired as exc:
            return subprocess.CompletedProcess(command, 124, stdout=f"Timed out: {exc}", stderr="")
