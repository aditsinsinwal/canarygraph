from dataclasses import dataclass, field
from pathlib import Path

import pytest

from canarygraph.compatibility import ApiDiffEngine, RenameMap, SdkSurfaceExtractor
from canarygraph.domain import ChangeKind


@dataclass(frozen=True)
class RuleCase:
    expected: ChangeKind
    old: str
    new: str
    renames: RenameMap = field(default_factory=RenameMap)


def compare(tmp_path: Path, case: RuleCase) -> set[ChangeKind]:
    old_root = tmp_path / "old"
    new_root = tmp_path / "new"
    old_root.mkdir()
    new_root.mkdir()
    (old_root / "sdk.py").write_text(case.old)
    (new_root / "sdk.py").write_text(case.new)
    extractor = SdkSurfaceExtractor()
    old = extractor.extract(old_root, library="sdk", version="1")
    new = extractor.extract(new_root, library="sdk", version="2")
    return {item.kind for item in ApiDiffEngine().compare(old, new, renames=case.renames)}


POSITIVE_CASES = [
    RuleCase(ChangeKind.FUNCTION_REMOVED, "def f():\n    pass\n", ""),
    RuleCase(
        ChangeKind.METHOD_REMOVED,
        "class C:\n    def f(self):\n        pass\n",
        "class C:\n    pass\n",
    ),
    RuleCase(
        ChangeKind.FUNCTION_RENAMED,
        "def old():\n    pass\n",
        "def new():\n    pass\n",
        RenameMap({"sdk.old": "sdk.new"}),
    ),
    RuleCase(
        ChangeKind.METHOD_RENAMED,
        "class C:\n    def old(self):\n        pass\n",
        "class C:\n    def new(self):\n        pass\n",
        RenameMap({"sdk.C.old": "sdk.C.new"}),
    ),
    RuleCase(
        ChangeKind.REQUIRED_PARAMETER_ADDED,
        "def f(a):\n    pass\n",
        "def f(a, b):\n    pass\n",
    ),
    RuleCase(
        ChangeKind.PARAMETER_REMOVED,
        "def f(a, b):\n    pass\n",
        "def f(a):\n    pass\n",
    ),
    RuleCase(
        ChangeKind.PARAMETER_RENAMED,
        "def f(old):\n    pass\n",
        "def f(new):\n    pass\n",
        RenameMap(parameters={"sdk.f": {"old": "new"}}),
    ),
    RuleCase(
        ChangeKind.PARAMETER_TYPE_CHANGED,
        "def f(a: int):\n    pass\n",
        "def f(a: str):\n    pass\n",
    ),
    RuleCase(
        ChangeKind.PARAMETER_BECAME_KEYWORD_ONLY,
        "def f(a, b=1):\n    pass\n",
        "def f(a, *, b=1):\n    pass\n",
    ),
    RuleCase(
        ChangeKind.DEFAULT_REMOVED,
        "def f(a=1):\n    pass\n",
        "def f(a):\n    pass\n",
    ),
    RuleCase(ChangeKind.CLASS_REMOVED, "class C:\n    pass\n", ""),
    RuleCase(
        ChangeKind.CLASS_RENAMED,
        "class Old:\n    pass\n",
        "class New:\n    pass\n",
        RenameMap({"sdk.Old": "sdk.New"}),
    ),
    RuleCase(
        ChangeKind.ENUM_MEMBER_REMOVED,
        "from enum import Enum\nclass E(Enum):\n    A = 1\n    B = 2\n",
        "from enum import Enum\nclass E(Enum):\n    A = 1\n",
    ),
]


@pytest.mark.parametrize("case", POSITIVE_CASES, ids=lambda case: case.expected.value)
def test_breaking_rule_positive(tmp_path: Path, case: RuleCase) -> None:
    assert case.expected in compare(tmp_path, case)


NEGATIVE_CASES = [
    RuleCase(ChangeKind.FUNCTION_REMOVED, "def f():\n    pass\n", "def f():\n    pass\n"),
    RuleCase(
        ChangeKind.METHOD_REMOVED,
        "class C:\n    def f(self):\n        pass\n",
        "class C:\n    def f(self):\n        pass\n",
    ),
    RuleCase(
        ChangeKind.FUNCTION_RENAMED,
        "def old():\n    pass\n",
        "def new():\n    pass\n",
    ),
    RuleCase(
        ChangeKind.METHOD_RENAMED,
        "class C:\n    def old(self):\n        pass\n",
        "class C:\n    def new(self):\n        pass\n",
    ),
    RuleCase(
        ChangeKind.REQUIRED_PARAMETER_ADDED,
        "def f(a):\n    pass\n",
        "def f(a, b=1):\n    pass\n",
    ),
    RuleCase(
        ChangeKind.PARAMETER_REMOVED,
        "def f(a):\n    pass\n",
        "def f(a):\n    pass\n",
    ),
    RuleCase(
        ChangeKind.PARAMETER_RENAMED,
        "def f(a):\n    pass\n",
        "def f(a):\n    pass\n",
    ),
    RuleCase(
        ChangeKind.PARAMETER_TYPE_CHANGED,
        "def f(a: int):\n    pass\n",
        "def f(a: int):\n    pass\n",
    ),
    RuleCase(
        ChangeKind.PARAMETER_BECAME_KEYWORD_ONLY,
        "def f(a):\n    pass\n",
        "def f(a):\n    pass\n",
    ),
    RuleCase(
        ChangeKind.DEFAULT_REMOVED,
        "def f(a=1):\n    pass\n",
        "def f(a=2):\n    pass\n",
    ),
    RuleCase(ChangeKind.CLASS_REMOVED, "class C:\n    pass\n", "class C:\n    pass\n"),
    RuleCase(
        ChangeKind.CLASS_RENAMED,
        "class C:\n    pass\n",
        "class C:\n    pass\n",
    ),
    RuleCase(
        ChangeKind.ENUM_MEMBER_REMOVED,
        "from enum import Enum\nclass E(Enum):\n    A = 1\n",
        "from enum import Enum\nclass E(Enum):\n    A = 1\n",
    ),
]


@pytest.mark.parametrize("case", NEGATIVE_CASES, ids=lambda case: case.expected.value)
def test_breaking_rule_negative(tmp_path: Path, case: RuleCase) -> None:
    assert case.expected not in compare(tmp_path, case)


EDGE_CASES = [
    RuleCase(ChangeKind.FUNCTION_REMOVED, "def _private():\n    pass\n", ""),
    RuleCase(
        ChangeKind.METHOD_REMOVED,
        "class C:\n    def _private(self):\n        pass\n",
        "class C:\n    pass\n",
    ),
    RuleCase(
        ChangeKind.FUNCTION_RENAMED,
        "def old():\n    pass\n",
        "def other():\n    pass\n",
        RenameMap({"sdk.old": "sdk.missing"}),
    ),
    RuleCase(
        ChangeKind.METHOD_RENAMED,
        "class C:\n    def old(self):\n        pass\n",
        "class C:\n    def other(self):\n        pass\n",
        RenameMap({"sdk.C.old": "sdk.C.missing"}),
    ),
    RuleCase(
        ChangeKind.REQUIRED_PARAMETER_ADDED,
        "def f(a):\n    pass\n",
        "def f(a, *, required):\n    pass\n",
    ),
    RuleCase(
        ChangeKind.PARAMETER_REMOVED,
        "def f(a, /):\n    pass\n",
        "def f():\n    pass\n",
    ),
    RuleCase(
        ChangeKind.PARAMETER_RENAMED,
        "def f(*, old=1):\n    pass\n",
        "def f(*, new=1):\n    pass\n",
        RenameMap(parameters={"sdk.f": {"old": "new"}}),
    ),
    RuleCase(
        ChangeKind.PARAMETER_TYPE_CHANGED,
        "def f(a: int):\n    pass\n",
        "def f(a):\n    pass\n",
    ),
    RuleCase(
        ChangeKind.PARAMETER_BECAME_KEYWORD_ONLY,
        "def f(a, /):\n    pass\n",
        "def f(*, a):\n    pass\n",
    ),
    RuleCase(
        ChangeKind.DEFAULT_REMOVED,
        "def f(*, a=1):\n    pass\n",
        "def f(*, a):\n    pass\n",
    ),
    RuleCase(ChangeKind.CLASS_REMOVED, "class _Private:\n    pass\n", ""),
    RuleCase(
        ChangeKind.CLASS_RENAMED,
        "class Old:\n    def f(self):\n        pass\n",
        "class New:\n    def f(self):\n        pass\n",
        RenameMap({"sdk.Old": "sdk.New"}),
    ),
    RuleCase(
        ChangeKind.ENUM_MEMBER_REMOVED,
        "from enum import Enum\nclass E(Enum):\n    A = 1\n    _PRIVATE = 2\n",
        "from enum import Enum\nclass E(Enum):\n    A = 1\n",
    ),
]


@pytest.mark.parametrize("case", EDGE_CASES, ids=lambda case: case.expected.value)
def test_breaking_rule_edge_case(tmp_path: Path, case: RuleCase) -> None:
    expected = case.expected
    private_ignored = expected in {
        ChangeKind.FUNCTION_REMOVED,
        ChangeKind.METHOD_REMOVED,
        ChangeKind.CLASS_REMOVED,
        ChangeKind.ENUM_MEMBER_REMOVED,
    }
    missing_rename = expected in {ChangeKind.FUNCTION_RENAMED, ChangeKind.METHOD_RENAMED}
    if private_ignored or missing_rename:
        assert expected not in compare(tmp_path, case)
    else:
        assert expected in compare(tmp_path, case)
