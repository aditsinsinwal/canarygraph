"""Typed domain language shared by all CanaryGraph adapters.

The analysis core intentionally uses dataclasses and has no dependency on FastAPI,
SQLAlchemy, or a persistence technology.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from enum import StrEnum
from pathlib import Path
from typing import Any


class Confidence(StrEnum):
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ParameterKind(StrEnum):
    POSITIONAL_ONLY = "POSITIONAL_ONLY"
    POSITIONAL_OR_KEYWORD = "POSITIONAL_OR_KEYWORD"
    VAR_POSITIONAL = "VAR_POSITIONAL"
    KEYWORD_ONLY = "KEYWORD_ONLY"
    VAR_KEYWORD = "VAR_KEYWORD"


class ChangeKind(StrEnum):
    FUNCTION_REMOVED = "FUNCTION_REMOVED"
    METHOD_REMOVED = "METHOD_REMOVED"
    FUNCTION_RENAMED = "FUNCTION_RENAMED"
    METHOD_RENAMED = "METHOD_RENAMED"
    REQUIRED_PARAMETER_ADDED = "REQUIRED_PARAMETER_ADDED"
    PARAMETER_REMOVED = "PARAMETER_REMOVED"
    PARAMETER_RENAMED = "PARAMETER_RENAMED"
    PARAMETER_TYPE_CHANGED = "PARAMETER_TYPE_CHANGED"
    PARAMETER_BECAME_KEYWORD_ONLY = "PARAMETER_BECAME_KEYWORD_ONLY"
    DEFAULT_REMOVED = "DEFAULT_REMOVED"
    CLASS_REMOVED = "CLASS_REMOVED"
    CLASS_RENAMED = "CLASS_RENAMED"
    ENUM_MEMBER_REMOVED = "ENUM_MEMBER_REMOVED"
    BEHAVIORAL_CHANGE = "BEHAVIORAL_CHANGE"


class RiskLevel(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"


class MigrationStatus(StrEnum):
    AVAILABLE = "AVAILABLE"
    VALIDATED = "VALIDATED"
    PARSE_FAILED = "PARSE_FAILED"
    TYPE_CHECK_FAILED = "TYPE_CHECK_FAILED"
    TEST_FAILED = "TEST_FAILED"
    REVIEW_REQUIRED = "REVIEW_REQUIRED"
    UNSUPPORTED = "UNSUPPORTED"


@dataclass(frozen=True, slots=True)
class SourceLocation:
    path: str
    line: int
    column: int = 0


@dataclass(frozen=True, slots=True)
class Parameter:
    name: str
    kind: ParameterKind
    annotation: str | None = None
    default: str | None = None

    @property
    def required(self) -> bool:
        return self.default is None and self.kind not in {
            ParameterKind.VAR_POSITIONAL,
            ParameterKind.VAR_KEYWORD,
        }


@dataclass(frozen=True, slots=True)
class FunctionSignature:
    name: str
    parameters: tuple[Parameter, ...] = ()
    return_annotation: str | None = None
    is_async: bool = False
    decorators: tuple[str, ...] = ()

    def render(self) -> str:
        parts: list[str] = []
        saw_kw_marker = False
        positional_only = sum(p.kind == ParameterKind.POSITIONAL_ONLY for p in self.parameters)
        for index, parameter in enumerate(self.parameters):
            if parameter.kind == ParameterKind.KEYWORD_ONLY and not saw_kw_marker:
                parts.append("*")
                saw_kw_marker = True
            prefix = ""
            if parameter.kind == ParameterKind.VAR_POSITIONAL:
                prefix, saw_kw_marker = "*", True
            elif parameter.kind == ParameterKind.VAR_KEYWORD:
                prefix = "**"
            text = prefix + parameter.name
            if parameter.annotation:
                text += f": {parameter.annotation}"
            if parameter.default is not None:
                text += f" = {parameter.default}"
            parts.append(text)
            if positional_only and index + 1 == positional_only:
                parts.append("/")
        async_prefix = "async " if self.is_async else ""
        returns = f" -> {self.return_annotation}" if self.return_annotation else ""
        return f"{async_prefix}{self.name}({', '.join(parts)}){returns}"


@dataclass(frozen=True, slots=True)
class ImportBinding:
    local_name: str
    qualified_name: str
    location: SourceLocation


@dataclass(frozen=True, slots=True)
class CallSite:
    caller: str
    expression: str
    location: SourceLocation
    positional_arguments: int = 0
    keyword_arguments: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class WebEndpoint:
    function: str
    framework: str
    method: str
    path: str


@dataclass(frozen=True, slots=True)
class PythonFunction:
    qualified_name: str
    signature: FunctionSignature
    location: SourceLocation
    calls: tuple[CallSite, ...] = ()
    local_types: tuple[tuple[str, str], ...] = ()
    endpoint: WebEndpoint | None = None


@dataclass(frozen=True, slots=True)
class PythonClass:
    qualified_name: str
    location: SourceLocation
    methods: tuple[PythonFunction, ...] = ()
    attribute_types: tuple[tuple[str, str], ...] = ()
    bases: tuple[str, ...] = ()
    enum_members: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class PythonModule:
    name: str
    path: str
    imports: tuple[ImportBinding, ...] = ()
    functions: tuple[PythonFunction, ...] = ()
    classes: tuple[PythonClass, ...] = ()

    @property
    def all_functions(self) -> tuple[PythonFunction, ...]:
        return self.functions + tuple(method for cls in self.classes for method in cls.methods)


@dataclass(frozen=True, slots=True)
class SourceFile:
    path: str
    size_bytes: int


@dataclass(frozen=True, slots=True)
class ProjectRepository:
    root: str
    files: tuple[SourceFile, ...]


@dataclass(frozen=True, slots=True)
class ApiFunction:
    qualified_name: str
    signature: FunctionSignature
    location: SourceLocation
    owner_class: str | None = None


@dataclass(frozen=True, slots=True)
class ApiClass:
    qualified_name: str
    methods: tuple[ApiFunction, ...] = ()
    enum_members: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ExternalLibrary:
    name: str


@dataclass(frozen=True, slots=True)
class ApiVersion:
    library: ExternalLibrary
    version: str
    functions: tuple[ApiFunction, ...] = ()
    classes: tuple[ApiClass, ...] = ()

    @property
    def function_index(self) -> dict[str, ApiFunction]:
        result = {item.qualified_name: item for item in self.functions}
        for cls in self.classes:
            result.update({method.qualified_name: method for method in cls.methods})
        return result


@dataclass(frozen=True, slots=True)
class ApiUsage:
    symbol: str
    call_site: CallSite
    confidence: Confidence
    reason: str


@dataclass(frozen=True, slots=True)
class CallGraphNode:
    qualified_name: str
    kind: str = "function"


@dataclass(frozen=True, slots=True)
class CallGraphEdge:
    caller: str
    callee: str
    confidence: Confidence = Confidence.HIGH


@dataclass(frozen=True, slots=True)
class BreakingChange:
    id: str
    kind: ChangeKind
    symbol: str
    message: str
    severity: int
    old_signature: FunctionSignature | None = None
    new_signature: FunctionSignature | None = None
    replacement: str | None = None
    parameter: str | None = None
    metadata: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True, slots=True)
class BlastRadius:
    direct_functions: tuple[str, ...] = ()
    transitive_functions: tuple[str, ...] = ()
    affected_classes: tuple[str, ...] = ()
    affected_modules: tuple[str, ...] = ()
    affected_endpoints: tuple[WebEndpoint, ...] = ()
    paths_to_usage: tuple[tuple[str, ...], ...] = ()


@dataclass(frozen=True, slots=True)
class RiskScore:
    score: int
    level: RiskLevel
    factors: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MigrationPatch:
    path: str
    before: str
    after: str
    diff: str


@dataclass(frozen=True, slots=True)
class MigrationPlan:
    status: MigrationStatus
    reason: str
    operations: tuple[str, ...] = ()
    patches: tuple[MigrationPatch, ...] = ()


@dataclass(frozen=True, slots=True)
class ValidationResult:
    status: MigrationStatus
    parse_succeeded: bool
    type_check_succeeded: bool | None = None
    tests_succeeded: bool | None = None
    output: str = ""


@dataclass(frozen=True, slots=True)
class CompatibilityFinding:
    id: str
    change: BreakingChange
    usages: tuple[ApiUsage, ...]
    blast_radius: BlastRadius
    risk: RiskScore
    migration: MigrationPlan


@dataclass(frozen=True, slots=True)
class AnalysisMetrics:
    files: int
    lines: int
    modules: int
    functions: int
    graph_nodes: int
    graph_edges: int
    parsing_ms: float
    graph_ms: float
    diff_ms: float
    blast_radius_ms: float
    total_ms: float


@dataclass(frozen=True, slots=True)
class CompatibilityReport:
    id: str
    repository: str
    library: str
    old_version: str
    new_version: str
    changes: tuple[BreakingChange, ...]
    findings: tuple[CompatibilityFinding, ...]
    metrics: AnalysisMetrics
    warnings: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def relative_module(root: Path, path: Path) -> str:
    """Return a stable Python module name for a file below *root*."""

    relative = path.relative_to(root).with_suffix("")
    parts = list(relative.parts)
    if parts and parts[-1] == "__init__":
        parts.pop()
    return ".".join(parts)
