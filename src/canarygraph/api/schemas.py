"""Validated HTTP contracts."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from pydantic import BaseModel, Field, field_validator


class AnalysisCreate(BaseModel):
    repository: str = Field(min_length=1)
    old_api: str = Field(min_length=1)
    new_api: str = Field(min_length=1)
    library: str = Field(min_length=1, pattern=r"^[A-Za-z_][A-Za-z0-9_.-]*$")
    old_version: str = "old"
    new_version: str = "new"
    symbol_renames: dict[str, str] = Field(default_factory=dict)
    parameter_renames: dict[str, dict[str, str]] = Field(default_factory=dict)
    behavioral_fixture: str | None = None
    include_private: bool = False

    @field_validator("repository", "old_api", "new_api", "behavioral_fixture")
    @classmethod
    def normalize_path(cls, value: str | None) -> str | None:
        return str(Path(value).expanduser().resolve()) if value else value


class AnalysisCreated(BaseModel):
    id: str
    status: str


class ValidationRequest(BaseModel):
    run_ruff: bool = False
    run_mypy: bool = False
    run_tests: bool = False


class ErrorBody(BaseModel):
    error: dict[str, Any]
