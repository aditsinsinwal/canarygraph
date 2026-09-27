"""Structured, deterministic compatibility rules for Python APIs."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field

from canarygraph.domain import (
    ApiFunction,
    ApiVersion,
    BreakingChange,
    ChangeKind,
    ParameterKind,
)


@dataclass(frozen=True, slots=True)
class RenameMap:
    symbols: dict[str, str] = field(default_factory=dict)
    parameters: dict[str, dict[str, str]] = field(default_factory=dict)


def _id(kind: ChangeKind, symbol: str, parameter: str | None = None) -> str:
    raw = f"{kind.value}:{symbol}:{parameter or ''}".encode()
    return hashlib.sha256(raw).hexdigest()[:16]


class ApiDiffEngine:
    """Compare normalized API models; source formatting never affects results."""

    def compare(
        self,
        old: ApiVersion,
        new: ApiVersion,
        *,
        renames: RenameMap | None = None,
        behavioral_changes: list[dict[str, str]] | None = None,
    ) -> tuple[BreakingChange, ...]:
        renames = renames or RenameMap()
        changes: list[BreakingChange] = []
        old_classes = {item.qualified_name: item for item in old.classes}
        new_classes = {item.qualified_name: item for item in new.classes}
        new_class_names = set(new_classes)
        renamed_old_classes = {
            source for source, target in renames.symbols.items() if target in new_class_names
        }
        for name, old_class in old_classes.items():
            if name in new_classes:
                removed_members = set(old_class.enum_members) - set(new_classes[name].enum_members)
                for member in sorted(removed_members):
                    changes.append(
                        self._change(
                            ChangeKind.ENUM_MEMBER_REMOVED,
                            f"{name}.{member}",
                            f"Enum member {member!r} was removed",
                            70,
                        )
                    )
            elif name in renamed_old_classes:
                changes.append(
                    self._change(
                        ChangeKind.CLASS_RENAMED,
                        name,
                        f"Class renamed to {renames.symbols[name]}",
                        85,
                        replacement=renames.symbols[name],
                    )
                )
            else:
                changes.append(
                    self._change(ChangeKind.CLASS_REMOVED, name, "Public class was removed", 100)
                )

        old_functions = old.function_index
        new_functions = new.function_index
        for name, old_function in old_functions.items():
            mapped = renames.symbols.get(name)
            new_function = new_functions.get(name)
            mapped_owner = (
                renames.symbols.get(old_function.owner_class) if old_function.owner_class else None
            )
            if new_function is None and mapped_owner:
                new_function = new_functions.get(f"{mapped_owner}.{old_function.signature.name}")
            if new_function is None and mapped:
                new_function = new_functions.get(mapped)
                if new_function:
                    kind = (
                        ChangeKind.METHOD_RENAMED
                        if old_function.owner_class
                        else ChangeKind.FUNCTION_RENAMED
                    )
                    changes.append(
                        self._change(
                            kind,
                            name,
                            f"Callable renamed to {mapped}",
                            90,
                            old=old_function,
                            new=new_function,
                            replacement=mapped,
                        )
                    )
            if new_function is None:
                owner_removed = bool(
                    old_function.owner_class in old_classes
                    and old_function.owner_class not in new_classes
                    and not (mapped_owner and mapped_owner in new_classes)
                )
                if not owner_removed:
                    kind = (
                        ChangeKind.METHOD_REMOVED
                        if old_function.owner_class
                        else ChangeKind.FUNCTION_REMOVED
                    )
                    changes.append(
                        self._change(
                            kind, name, "Public callable was removed", 100, old=old_function
                        )
                    )
                continue
            changes.extend(self._signature_changes(name, old_function, new_function, renames))

        for item in behavioral_changes or []:
            symbol = item.get("symbol", "").strip()
            if not symbol:
                raise ValueError("Every behavioral change requires a non-empty symbol")
            try:
                severity = int(item.get("severity", "80"))
            except ValueError as exc:
                raise ValueError("Behavioral change severity must be an integer") from exc
            if not 0 <= severity <= 100:
                raise ValueError("Behavioral change severity must be between 0 and 100")
            changes.append(
                self._change(
                    ChangeKind.BEHAVIORAL_CHANGE,
                    symbol,
                    item.get("description", "Configured behavioral contract changed"),
                    severity,
                    metadata=tuple(sorted((str(k), str(v)) for k, v in item.items())),
                )
            )
        return tuple(
            sorted(changes, key=lambda item: (item.symbol, item.kind.value, item.parameter or ""))
        )

    def load_behavioral_fixture(self, path: str) -> list[dict[str, str]]:
        with open(path, encoding="utf-8") as stream:
            data = json.load(stream)
        if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            raise ValueError("Behavioral fixture must be a JSON array of objects")
        return [{str(key): str(value) for key, value in item.items()} for item in data]

    def _signature_changes(
        self,
        symbol: str,
        old: ApiFunction,
        new: ApiFunction,
        renames: RenameMap,
    ) -> list[BreakingChange]:
        changes: list[BreakingChange] = []
        old_parameters = {item.name: item for item in old.signature.parameters}
        new_parameters = {item.name: item for item in new.signature.parameters}
        parameter_renames = renames.parameters.get(symbol, {})

        for old_name, old_parameter in old_parameters.items():
            mapped_name = parameter_renames.get(old_name)
            new_parameter = new_parameters.get(mapped_name or old_name)
            if new_parameter is None:
                changes.append(
                    self._change(
                        ChangeKind.PARAMETER_REMOVED,
                        symbol,
                        f"Parameter {old_name!r} was removed",
                        85,
                        old=old,
                        new=new,
                        parameter=old_name,
                    )
                )
                continue
            if mapped_name and mapped_name != old_name:
                changes.append(
                    self._change(
                        ChangeKind.PARAMETER_RENAMED,
                        symbol,
                        f"Parameter {old_name!r} renamed to {mapped_name!r}",
                        75,
                        old=old,
                        new=new,
                        parameter=old_name,
                        replacement=mapped_name,
                    )
                )
            if old_parameter.annotation != new_parameter.annotation:
                changes.append(
                    self._change(
                        ChangeKind.PARAMETER_TYPE_CHANGED,
                        symbol,
                        f"Parameter {old_name!r} annotation changed from "
                        f"{old_parameter.annotation!r} to {new_parameter.annotation!r}",
                        55,
                        old=old,
                        new=new,
                        parameter=old_name,
                    )
                )
            if (
                old_parameter.kind
                in {ParameterKind.POSITIONAL_ONLY, ParameterKind.POSITIONAL_OR_KEYWORD}
                and new_parameter.kind == ParameterKind.KEYWORD_ONLY
            ):
                changes.append(
                    self._change(
                        ChangeKind.PARAMETER_BECAME_KEYWORD_ONLY,
                        symbol,
                        f"Parameter {old_name!r} became keyword-only",
                        90,
                        old=old,
                        new=new,
                        parameter=old_name,
                    )
                )
            if old_parameter.default is not None and new_parameter.default is None:
                changes.append(
                    self._change(
                        ChangeKind.DEFAULT_REMOVED,
                        symbol,
                        f"Default value for {old_name!r} was removed",
                        95,
                        old=old,
                        new=new,
                        parameter=old_name,
                    )
                )

        renamed_targets = set(parameter_renames.values())
        for name, parameter in new_parameters.items():
            if name not in old_parameters and name not in renamed_targets and parameter.required:
                changes.append(
                    self._change(
                        ChangeKind.REQUIRED_PARAMETER_ADDED,
                        symbol,
                        f"Required parameter {name!r} was added",
                        100,
                        old=old,
                        new=new,
                        parameter=name,
                    )
                )
        return changes

    def _change(
        self,
        kind: ChangeKind,
        symbol: str,
        message: str,
        severity: int,
        *,
        old: ApiFunction | None = None,
        new: ApiFunction | None = None,
        replacement: str | None = None,
        parameter: str | None = None,
        metadata: tuple[tuple[str, str], ...] = (),
    ) -> BreakingChange:
        return BreakingChange(
            _id(kind, symbol, parameter),
            kind,
            symbol,
            message,
            severity,
            old.signature if old else None,
            new.signature if new else None,
            replacement,
            parameter,
            metadata,
        )
