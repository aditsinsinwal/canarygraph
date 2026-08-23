"""CanaryGraph command-line interface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

from canarygraph.application import AnalysisRequest, AnalysisService
from canarygraph.compatibility import RenameMap
from canarygraph.reporting import render_text

app = typer.Typer(no_args_is_help=True, help="Analyze Python SDK upgrade blast radius.")


@app.callback()
def main() -> None:
    """CanaryGraph command group."""


def _renames(path: Path | None) -> RenameMap | None:
    if path is None:
        return None
    data = json.loads(path.read_text(encoding="utf-8"))
    return RenameMap(data.get("symbols", {}), data.get("parameters", {}))


@app.command()
def analyze(
    repo: Annotated[Path, typer.Option(exists=True, file_okay=False)],
    old_api: Annotated[Path, typer.Option(exists=True, file_okay=False)],
    new_api: Annotated[Path, typer.Option(exists=True, file_okay=False)],
    library: Annotated[str, typer.Option()] = "payment_sdk",
    old_version: Annotated[str, typer.Option()] = "1.0.0",
    new_version: Annotated[str, typer.Option()] = "2.0.0",
    rename_map: Annotated[Path | None, typer.Option(exists=True, dir_okay=False)] = None,
    behavioral_fixture: Annotated[Path | None, typer.Option(exists=True, dir_okay=False)] = None,
    output: Annotated[Path | None, typer.Option()] = None,
    json_output: Annotated[bool, typer.Option("--json")] = False,
) -> None:
    """Analyze REPO against two local SDK source trees."""

    report = AnalysisService().analyze(
        AnalysisRequest(
            str(repo),
            str(old_api),
            str(new_api),
            library,
            old_version,
            new_version,
            _renames(rename_map),
            str(behavioral_fixture) if behavioral_fixture else None,
        )
    )
    rendered = json.dumps(report.to_dict(), indent=2) if json_output else render_text(report)
    if output:
        output.write_text(rendered + ("\n" if json_output else ""), encoding="utf-8")
    else:
        typer.echo(rendered, nl=False)


if __name__ == "__main__":
    app()
