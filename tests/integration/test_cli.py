import json
from pathlib import Path

from typer.testing import CliRunner

from canarygraph.cli import app

runner = CliRunner()


def test_cli_analyze_emits_machine_readable_report(examples: Path) -> None:
    result = runner.invoke(
        app,
        [
            "analyze",
            "--repo",
            str(examples / "example_store"),
            "--old-api",
            str(examples / "payment_sdk_v1"),
            "--new-api",
            str(examples / "payment_sdk_v2"),
            "--library",
            "payment_sdk",
            "--json",
        ],
    )

    assert result.exit_code == 0
    report = json.loads(result.stdout)
    assert report["library"] == "payment_sdk"
    assert report["changes"]


def test_cli_benchmark_reports_measured_values() -> None:
    result = runner.invoke(
        app,
        ["benchmark", "--modules", "2", "--functions-per-module", "2"],
    )

    assert result.exit_code == 0
    benchmark = json.loads(result.stdout)
    assert benchmark["requested_modules"] == 2
    assert benchmark["peak_memory_bytes"] > 0
