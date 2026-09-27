import pytest

from canarygraph.compatibility import usage_is_affected
from canarygraph.domain import (
    ApiUsage,
    BreakingChange,
    CallSite,
    ChangeKind,
    Confidence,
    FunctionSignature,
    Parameter,
    ParameterKind,
    SourceLocation,
)


def signature(*parameters: Parameter) -> FunctionSignature:
    return FunctionSignature("f", parameters)


def usage(*, positional: int = 0, keywords: tuple[str, ...] = (), star: bool = False) -> ApiUsage:
    return ApiUsage(
        "sdk.f",
        CallSite(
            "app.call",
            "f",
            SourceLocation("app.py", 1),
            positional,
            keywords,
            star,
            star,
        ),
        Confidence.HIGH,
        "test",
    )


@pytest.mark.parametrize(
    ("change", "call", "affected"),
    [
        (
            BreakingChange(
                "1",
                ChangeKind.PARAMETER_RENAMED,
                "sdk.f",
                "",
                1,
                parameter="old",
                replacement="new",
            ),
            usage(positional=1),
            False,
        ),
        (
            BreakingChange(
                "2",
                ChangeKind.PARAMETER_RENAMED,
                "sdk.f",
                "",
                1,
                parameter="old",
                replacement="new",
            ),
            usage(keywords=("old",)),
            True,
        ),
        (
            BreakingChange(
                "3",
                ChangeKind.PARAMETER_BECAME_KEYWORD_ONLY,
                "sdk.f",
                "",
                1,
                old_signature=signature(
                    Parameter("a", ParameterKind.POSITIONAL_OR_KEYWORD),
                    Parameter("b", ParameterKind.POSITIONAL_OR_KEYWORD, default="1"),
                ),
                parameter="b",
            ),
            usage(positional=2),
            True,
        ),
        (
            BreakingChange(
                "4",
                ChangeKind.DEFAULT_REMOVED,
                "sdk.f",
                "",
                1,
                old_signature=signature(
                    Parameter("a", ParameterKind.POSITIONAL_OR_KEYWORD, default="1")
                ),
                parameter="a",
            ),
            usage(),
            True,
        ),
        (
            BreakingChange(
                "5",
                ChangeKind.PARAMETER_REMOVED,
                "sdk.f",
                "",
                1,
                old_signature=signature(
                    Parameter("a", ParameterKind.POSITIONAL_OR_KEYWORD),
                    Parameter("b", ParameterKind.POSITIONAL_OR_KEYWORD, default="1"),
                ),
                parameter="b",
            ),
            usage(positional=1),
            False,
        ),
        (
            BreakingChange(
                "6",
                ChangeKind.REQUIRED_PARAMETER_ADDED,
                "sdk.f",
                "",
                1,
                new_signature=signature(
                    Parameter("a", ParameterKind.POSITIONAL_OR_KEYWORD),
                    Parameter("currency", ParameterKind.KEYWORD_ONLY),
                ),
                parameter="currency",
            ),
            usage(keywords=("currency",)),
            False,
        ),
    ],
)
def test_usage_impact_uses_concrete_call_shape(
    change: BreakingChange, call: ApiUsage, affected: bool
) -> None:
    assert usage_is_affected(change, call) is affected


def test_starred_arguments_remain_conservatively_affected() -> None:
    change = BreakingChange(
        "1",
        ChangeKind.PARAMETER_RENAMED,
        "sdk.f",
        "",
        1,
        parameter="old",
        replacement="new",
    )

    assert usage_is_affected(change, usage(star=True))
