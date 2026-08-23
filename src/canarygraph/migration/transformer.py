"""LibCST transformations constrained to statically identified call sites."""

from __future__ import annotations

import difflib
from collections import defaultdict
from pathlib import Path

import libcst as cst
from libcst.metadata import MetadataWrapper, PositionProvider

from canarygraph.domain import ApiUsage, BreakingChange, ChangeKind, MigrationPatch


class _CallSiteTransformer(cst.CSTTransformer):
    METADATA_DEPENDENCIES = (PositionProvider,)

    def __init__(self, change: BreakingChange, lines: set[int]) -> None:
        self.change = change
        self.lines = lines

    def _targeted(self, node: cst.CSTNode) -> bool:
        return self.get_metadata(PositionProvider, node).start.line in self.lines

    def leave_ImportAlias(
        self, original_node: cst.ImportAlias, updated_node: cst.ImportAlias
    ) -> cst.ImportAlias:
        if self.change.kind != ChangeKind.CLASS_RENAMED or not self.change.replacement:
            return updated_node
        old_name = self.change.symbol.rsplit(".", 1)[-1]
        new_name = self.change.replacement.rsplit(".", 1)[-1]
        if isinstance(updated_node.name, cst.Name) and updated_node.name.value == old_name:
            return updated_node.with_changes(name=cst.Name(new_name))
        return updated_node

    def leave_Call(self, original_node: cst.Call, updated_node: cst.Call) -> cst.Call:
        if not self._targeted(original_node):
            return updated_node
        if self.change.kind in {ChangeKind.FUNCTION_RENAMED, ChangeKind.METHOD_RENAMED}:
            replacement = (self.change.replacement or "").rsplit(".", 1)[-1]
            if isinstance(updated_node.func, cst.Attribute):
                return updated_node.with_changes(
                    func=updated_node.func.with_changes(attr=cst.Name(replacement))
                )
            if isinstance(updated_node.func, cst.Name):
                return updated_node.with_changes(func=cst.Name(replacement))
        if self.change.kind == ChangeKind.CLASS_RENAMED and self.change.replacement:
            old_name = self.change.symbol.rsplit(".", 1)[-1]
            new_name = self.change.replacement.rsplit(".", 1)[-1]
            if isinstance(updated_node.func, cst.Name) and updated_node.func.value == old_name:
                return updated_node.with_changes(func=cst.Name(new_name))
        if self.change.kind == ChangeKind.PARAMETER_RENAMED:
            old_parameter = self.change.parameter
            new_parameter = self.change.replacement
            renamed_args = [
                argument.with_changes(keyword=cst.Name(new_parameter))
                if argument.keyword and argument.keyword.value == old_parameter and new_parameter
                else argument
                for argument in updated_node.args
            ]
            return updated_node.with_changes(args=renamed_args)
        if self.change.kind == ChangeKind.PARAMETER_BECAME_KEYWORD_ONLY:
            old_signature = self.change.old_signature
            if not old_signature or not self.change.parameter:
                return updated_node
            positional_names = [
                parameter.name
                for parameter in old_signature.parameters
                if parameter.kind.value in {"POSITIONAL_ONLY", "POSITIONAL_OR_KEYWORD"}
            ]
            try:
                index = positional_names.index(self.change.parameter)
            except ValueError:
                return updated_node
            positional_seen = 0
            args: list[cst.Arg] = []
            for argument in updated_node.args:
                if argument.keyword is None and argument.star == "":
                    if positional_seen == index:
                        argument = argument.with_changes(keyword=cst.Name(self.change.parameter))
                    positional_seen += 1
                args.append(argument)
            return updated_node.with_changes(args=args)
        return updated_node


class SourceTransformer:
    """Generate patches; never writes application source implicitly."""

    def transform(
        self, change: BreakingChange, usages: tuple[ApiUsage, ...]
    ) -> tuple[MigrationPatch, ...]:
        grouped: dict[str, set[int]] = defaultdict(set)
        for usage in usages:
            grouped[usage.call_site.location.path].add(usage.call_site.location.line)
        patches: list[MigrationPatch] = []
        for path_text, lines in sorted(grouped.items()):
            path = Path(path_text)
            before = path.read_text(encoding="utf-8")
            wrapper = MetadataWrapper(cst.parse_module(before))
            after = wrapper.visit(_CallSiteTransformer(change, lines)).code
            if before == after:
                continue
            diff = "".join(
                difflib.unified_diff(
                    before.splitlines(keepends=True),
                    after.splitlines(keepends=True),
                    fromfile=str(path),
                    tofile=str(path),
                )
            )
            patches.append(MigrationPatch(str(path), before, after, diff))
        return tuple(patches)
