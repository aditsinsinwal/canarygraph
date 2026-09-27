"""Reproducible synthetic-repository benchmarks using the real analysis pipeline."""

from __future__ import annotations

import tempfile
import tracemalloc
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from canarygraph.application import AnalysisRequest, AnalysisService


@dataclass(frozen=True, slots=True)
class BenchmarkResult:
    requested_modules: int
    requested_functions_per_module: int
    peak_memory_bytes: int
    metrics: dict[str, Any]
    breaking_changes: int
    affected_findings: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class SyntheticRepositoryGenerator:
    """Generate deterministic call chains without executing generated code."""

    def generate(
        self, root: Path, *, modules: int, functions_per_module: int
    ) -> tuple[Path, Path, Path]:
        if modules < 1 or functions_per_module < 1:
            raise ValueError("modules and functions_per_module must be positive")
        repository = root / "repository"
        package = repository / "synthetic"
        old_api = root / "payment_sdk_v1" / "payment_sdk"
        new_api = root / "payment_sdk_v2" / "payment_sdk"
        package.mkdir(parents=True)
        old_api.mkdir(parents=True)
        new_api.mkdir(parents=True)
        (package / "__init__.py").write_text("", encoding="utf-8")
        (old_api / "__init__.py").write_text(
            "from .client import PaymentClient\n\n__all__ = ['PaymentClient']\n",
            encoding="utf-8",
        )
        (new_api / "__init__.py").write_text(
            "from .client import PaymentClient\n\n__all__ = ['PaymentClient']\n",
            encoding="utf-8",
        )
        (old_api / "client.py").write_text(
            "class PaymentClient:\n"
            "    def create_payment(self, amount: int):\n"
            "        return amount\n",
            encoding="utf-8",
        )
        (new_api / "client.py").write_text(
            "class PaymentClient:\n"
            "    def create_payment(self, amount: int, currency: str):\n"
            "        return amount, currency\n",
            encoding="utf-8",
        )
        for index in range(modules):
            lines: list[str] = []
            if index == 0:
                lines.extend(["from fastapi import APIRouter", "", "router = APIRouter()", ""])
            if index + 1 < modules:
                lines.extend(
                    [
                        f"from synthetic.module_{index + 1} import entry_{index + 1}",
                        "",
                    ]
                )
            else:
                lines.extend(
                    [
                        "from payment_sdk import PaymentClient",
                        "",
                        "client = PaymentClient()",
                        "",
                    ]
                )
            if index == 0:
                lines.append('@router.post("/synthetic")')
            lines.extend([f"def entry_{index}(amount: int):"])
            if index + 1 < modules:
                lines.append(f"    return entry_{index + 1}(amount)")
            else:
                lines.append("    return client.create_payment(amount)")
            for helper in range(1, functions_per_module):
                lines.extend(
                    [
                        "",
                        f"def helper_{index}_{helper}(value: int):",
                        "    return value",
                    ]
                )
            (package / f"module_{index}.py").write_text("\n".join(lines) + "\n", encoding="utf-8")
        return repository, old_api.parent, new_api.parent


def run_benchmark(*, modules: int = 100, functions_per_module: int = 5) -> BenchmarkResult:
    with tempfile.TemporaryDirectory(prefix="canarygraph-benchmark-") as directory:
        repository, old_api, new_api = SyntheticRepositoryGenerator().generate(
            Path(directory),
            modules=modules,
            functions_per_module=functions_per_module,
        )
        tracemalloc.start()
        report = AnalysisService().analyze(
            AnalysisRequest(
                str(repository),
                str(old_api),
                str(new_api),
                "payment_sdk",
                "1.0.0",
                "2.0.0",
            )
        )
        _, peak_memory = tracemalloc.get_traced_memory()
        tracemalloc.stop()
        return BenchmarkResult(
            modules,
            functions_per_module,
            peak_memory,
            asdict(report.metrics),
            len(report.changes),
            sum(bool(finding.usages) for finding in report.findings),
        )
