"""Call-shape-aware filtering for symbol-level compatibility changes."""

from __future__ import annotations

from canarygraph.domain import (
    ApiUsage,
    BreakingChange,
    ChangeKind,
    FunctionSignature,
    ParameterKind,
)


def _positional_index(signature: FunctionSignature | None, parameter: str | None) -> int | None:
    if not signature or not parameter:
        return None
    positional = [
        item.name
        for item in signature.parameters
        if item.kind in {ParameterKind.POSITIONAL_ONLY, ParameterKind.POSITIONAL_OR_KEYWORD}
    ]
    try:
        return positional.index(parameter)
    except ValueError:
        return None


def usage_is_affected(change: BreakingChange, usage: ApiUsage) -> bool:
    """Return whether this concrete call shape is affected by *change*.

    Starred arguments remain affected because their runtime contents are unknown.
    """

    call = usage.call_site
    if call.has_star_arguments or call.has_star_keywords:
        return True
    if change.kind == ChangeKind.PARAMETER_RENAMED:
        return bool(change.parameter and change.parameter in call.keyword_arguments)
    if change.kind == ChangeKind.PARAMETER_BECAME_KEYWORD_ONLY:
        index = _positional_index(change.old_signature, change.parameter)
        return index is None or call.positional_arguments > index
    if change.kind == ChangeKind.DEFAULT_REMOVED:
        if change.parameter in call.keyword_arguments:
            return False
        index = _positional_index(change.old_signature, change.parameter)
        return index is None or call.positional_arguments <= index
    if change.kind == ChangeKind.PARAMETER_REMOVED:
        if change.parameter in call.keyword_arguments:
            return True
        index = _positional_index(change.old_signature, change.parameter)
        return index is not None and call.positional_arguments > index
    if change.kind == ChangeKind.REQUIRED_PARAMETER_ADDED:
        if change.parameter in call.keyword_arguments:
            return False
        index = _positional_index(change.new_signature, change.parameter)
        return index is None or call.positional_arguments <= index
    return True
