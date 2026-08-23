"""Classify which compatibility changes can be migrated safely."""

from __future__ import annotations

from typing import ClassVar

from canarygraph.domain import BreakingChange, ChangeKind, MigrationPlan, MigrationStatus


class MigrationPlanner:
    SAFE_RENAMES: ClassVar[set[ChangeKind]] = {
        ChangeKind.FUNCTION_RENAMED,
        ChangeKind.METHOD_RENAMED,
        ChangeKind.CLASS_RENAMED,
        ChangeKind.PARAMETER_RENAMED,
    }

    def plan(self, change: BreakingChange) -> MigrationPlan:
        if change.kind in self.SAFE_RENAMES and change.replacement:
            return MigrationPlan(
                MigrationStatus.AVAILABLE,
                "A configured rename has deterministic source semantics",
                (f"rename {change.symbol} to {change.replacement}",),
            )
        if change.kind == ChangeKind.PARAMETER_BECAME_KEYWORD_ONLY:
            return MigrationPlan(
                MigrationStatus.AVAILABLE,
                "Positional arguments can be labeled using the extracted signature",
                (f"pass {change.parameter} by keyword",),
            )
        if change.kind == ChangeKind.REQUIRED_PARAMETER_ADDED:
            return MigrationPlan(
                MigrationStatus.REVIEW_REQUIRED,
                f"Required argument {change.parameter!r} cannot be inferred safely",
            )
        if change.kind in {
            ChangeKind.PARAMETER_TYPE_CHANGED,
            ChangeKind.BEHAVIORAL_CHANGE,
            ChangeKind.DEFAULT_REMOVED,
        }:
            return MigrationPlan(
                MigrationStatus.REVIEW_REQUIRED,
                "The correct replacement value or behavior requires application semantics",
            )
        return MigrationPlan(
            MigrationStatus.UNSUPPORTED,
            "No semantics-preserving deterministic transformation is available",
        )
