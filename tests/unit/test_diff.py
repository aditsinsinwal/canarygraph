from pathlib import Path

from canarygraph.compatibility import ApiDiffEngine, RenameMap, SdkSurfaceExtractor
from canarygraph.domain import ChangeKind


def _changes(examples: Path):
    extractor = SdkSurfaceExtractor()
    old = extractor.extract(examples / "payment_sdk_v1", library="payment_sdk", version="1")
    new = extractor.extract(examples / "payment_sdk_v2", library="payment_sdk", version="2")
    renames = RenameMap(
        {"payment_sdk.client.PaymentClient.capture": "payment_sdk.client.PaymentClient.authorize"},
        {"payment_sdk.client.PaymentClient.create_payment": {"amount": "amount_cents"}},
    )
    return ApiDiffEngine().compare(old, new, renames=renames)


def test_detects_all_fixture_breaking_change_families(examples: Path) -> None:
    kinds = {item.kind for item in _changes(examples)}

    assert {
        ChangeKind.CLASS_REMOVED,
        ChangeKind.FUNCTION_REMOVED,
        ChangeKind.METHOD_RENAMED,
        ChangeKind.PARAMETER_RENAMED,
        ChangeKind.REQUIRED_PARAMETER_ADDED,
        ChangeKind.PARAMETER_BECAME_KEYWORD_ONLY,
        ChangeKind.DEFAULT_REMOVED,
        ChangeKind.ENUM_MEMBER_REMOVED,
    } <= kinds


def test_unchanged_surface_has_no_changes(examples: Path) -> None:
    extractor = SdkSurfaceExtractor()
    api = extractor.extract(examples / "payment_sdk_v1", library="payment_sdk", version="1")

    assert ApiDiffEngine().compare(api, api) == ()


def test_optional_parameter_added_is_not_breaking(tmp_path: Path) -> None:
    old_root, new_root = tmp_path / "old", tmp_path / "new"
    old_root.mkdir()
    new_root.mkdir()
    (old_root / "sdk.py").write_text("def f(a):\n    pass\n")
    (new_root / "sdk.py").write_text("def f(a, b=1):\n    pass\n")
    extractor = SdkSurfaceExtractor()

    changes = ApiDiffEngine().compare(
        extractor.extract(old_root, library="sdk", version="1"),
        extractor.extract(new_root, library="sdk", version="2"),
    )
    assert changes == ()
