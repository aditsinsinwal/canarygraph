from pathlib import Path

from canarygraph.domain import MigrationPatch, MigrationStatus
from canarygraph.migration import ValidationPipeline


def test_validation_compiles_patch_in_isolated_copy(tmp_path: Path) -> None:
    source = tmp_path / "app.py"
    source.write_text("value = 1\n")
    patch = MigrationPatch(str(source), "value = 1\n", "value = 2\n", "")

    result = ValidationPipeline(timeout_seconds=10).validate(tmp_path, (patch,))

    assert result.status == MigrationStatus.VALIDATED
    assert source.read_text() == "value = 1\n"


def test_validation_rejects_invalid_syntax(tmp_path: Path) -> None:
    source = tmp_path / "app.py"
    source.write_text("value = 1\n")
    patch = MigrationPatch(str(source), "value = 1\n", "value =\n", "")

    result = ValidationPipeline().validate(tmp_path, (patch,))

    assert result.status == MigrationStatus.PARSE_FAILED
