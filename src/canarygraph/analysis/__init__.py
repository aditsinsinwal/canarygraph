"""Static-analysis building blocks."""

from .call_graph import CallGraph
from .parser import PythonRepositoryParser, SourceScanner
from .resolution import ExternalUsageResolver

__all__ = ["CallGraph", "ExternalUsageResolver", "PythonRepositoryParser", "SourceScanner"]
