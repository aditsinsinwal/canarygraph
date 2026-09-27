"""End-to-end deterministic analysis orchestration."""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, replace
from pathlib import Path

from canarygraph.analysis import (
    CallGraph,
    ExternalUsageResolver,
    PythonRepositoryParser,
    SourceScanner,
)
from canarygraph.compatibility import (
    ApiDiffEngine,
    BlastRadiusAnalyzer,
    RenameMap,
    RiskScorer,
    SdkSurfaceExtractor,
    usage_is_affected,
)
from canarygraph.domain import (
    AnalysisMetrics,
    CompatibilityFinding,
    CompatibilityReport,
    MigrationStatus,
)
from canarygraph.migration import MigrationPlanner, SourceTransformer


@dataclass(frozen=True, slots=True)
class AnalysisRequest:
    repository: str
    old_api: str
    new_api: str
    library: str
    old_version: str = "old"
    new_version: str = "new"
    renames: RenameMap | None = None
    behavioral_fixture: str | None = None
    include_private: bool = False


class AnalysisService:
    def __init__(self) -> None:
        self.scanner = SourceScanner()
        self.parser = PythonRepositoryParser()
        self.diff = ApiDiffEngine()
        self.usage = ExternalUsageResolver()
        self.blast = BlastRadiusAnalyzer()
        self.risk = RiskScorer()
        self.planner = MigrationPlanner()
        self.transformer = SourceTransformer()

    def analyze(self, request: AnalysisRequest) -> CompatibilityReport:
        started = time.perf_counter()
        repository = self.scanner.scan(request.repository)
        parse_started = time.perf_counter()
        modules = self.parser.parse_repository(repository)
        parsing_ms = self._elapsed(parse_started)

        graph_started = time.perf_counter()
        graph = CallGraph.build(modules)
        graph_ms = self._elapsed(graph_started)

        sdk_extractor = SdkSurfaceExtractor(include_private=request.include_private)
        old_api = sdk_extractor.extract(
            request.old_api, library=request.library, version=request.old_version
        )
        new_api = sdk_extractor.extract(
            request.new_api, library=request.library, version=request.new_version
        )
        known_symbols = set(old_api.function_index) | set(new_api.function_index)
        known_symbols.update(item.qualified_name for item in old_api.classes)
        known_symbols.update(item.qualified_name for item in new_api.classes)
        aliases = {**dict(old_api.aliases), **dict(new_api.aliases)}
        known_symbols.update(aliases)
        usages = self.usage.resolve(
            modules,
            library=request.library,
            known_symbols=known_symbols,
            aliases=aliases,
        )

        behavioral = (
            self.diff.load_behavioral_fixture(request.behavioral_fixture)
            if request.behavioral_fixture
            else None
        )
        diff_started = time.perf_counter()
        changes = self.diff.compare(
            old_api,
            new_api,
            renames=request.renames,
            behavioral_changes=behavioral,
        )
        diff_ms = self._elapsed(diff_started)

        blast_started = time.perf_counter()
        findings: list[CompatibilityFinding] = []
        warnings: list[str] = []
        for change in changes:
            relevant = tuple(
                item
                for item in usages
                if item.symbol == change.symbol and usage_is_affected(change, item)
            )
            radius = self.blast.analyze(change, relevant, graph, modules)
            plan = self.planner.plan(change)
            if plan.status == MigrationStatus.AVAILABLE:
                patches = self.transformer.transform(change, relevant)
                plan = replace(plan, patches=patches)
            findings.append(
                CompatibilityFinding(
                    change.id,
                    change,
                    relevant,
                    radius,
                    self.risk.score(change, relevant, radius),
                    plan,
                )
            )
        blast_ms = self._elapsed(blast_started)

        if any(item.confidence.value != "HIGH" for item in usages):
            warnings.append(
                "Some SDK usages have medium/low confidence; dynamic dispatch may require review."
            )
        lines = sum(
            len(Path(item.path).read_text(encoding="utf-8").splitlines())
            for item in repository.files
        )
        metrics = AnalysisMetrics(
            len(repository.files),
            lines,
            len(modules),
            sum(len(module.all_functions) for module in modules),
            len(graph.nodes),
            len(graph.edges),
            parsing_ms,
            graph_ms,
            diff_ms,
            blast_ms,
            self._elapsed(started),
        )
        return CompatibilityReport(
            str(uuid.uuid4()),
            repository.root,
            request.library,
            request.old_version,
            request.new_version,
            changes,
            tuple(findings),
            metrics,
            tuple(warnings),
        )

    @staticmethod
    def _elapsed(started: float) -> float:
        return round((time.perf_counter() - started) * 1000, 3)
