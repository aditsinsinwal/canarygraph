from pathlib import Path

from canarygraph.domain import MigrationPatch, MigrationStatus
from canarygraph.migration import ValidationPipeline


def test_validation_compiles_patch_in_isolated_copy(tmp_path: Path) -> None:
    source = tmp_path / "app.py"
    source.write_text("value = 1\n")
    patch = MigrationPatch(str(source), "value = 1\n", "value = 2\n", "")

    result = ValidationPipeline(timeout_seconds=10).validate(tmp_path, (patch,), run_ruff=True)

    assert result.status == MigrationStatus.VALIDATED
    assert result.static_check_succeeded is True
    assert source.read_text() == "value = 1\n"


def test_validation_rejects_invalid_syntax(tmp_path: Path) -> None:
    source = tmp_path / "app.py"
    source.write_text("value = 1\n")
    patch = MigrationPatch(str(source), "value = 1\n", "value =\n", "")

    result = ValidationPipeline().validate(tmp_path, (patch,))

    assert result.status == MigrationStatus.PARSE_FAILED


def test_validation_rejects_empty_migration(tmp_path: Path) -> None:
    result = ValidationPipeline().validate(tmp_path, ())

    assert result.status == MigrationStatus.UNSUPPORTED


def test_validation_rejects_symlink_escaping_repository(tmp_path: Path) -> None:
    repository = tmp_path / "repository"
    repository.mkdir()
    outside = tmp_path / "outside.py"
    outside.write_text("value = 1\n")
    (repository / "outside.py").symlink_to(outside)
    source = repository / "app.py"
    source.write_text("value = 1\n")
    patch = MigrationPatch(str(source), "value = 1\n", "value = 2\n", "")

    result = ValidationPipeline().validate(repository, (patch,))

    assert result.status == MigrationStatus.UNSUPPORTED
    assert "symlink" in result.output
