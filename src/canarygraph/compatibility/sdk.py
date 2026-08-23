"""Extract a public Python SDK surface from source without importing it."""

from __future__ import annotations

from pathlib import Path

from canarygraph.analysis.parser import PythonRepositoryParser, SourceScanner
from canarygraph.domain import ApiClass, ApiFunction, ApiVersion, ExternalLibrary


class SdkSurfaceExtractor:
    def __init__(self, *, include_private: bool = False) -> None:
        self.include_private = include_private
        self.scanner = SourceScanner()
        self.parser = PythonRepositoryParser()

    def extract(self, root: str | Path, *, library: str, version: str) -> ApiVersion:
        repository = self.scanner.scan(root)
        modules = self.parser.parse_repository(repository)
        functions: list[ApiFunction] = []
        classes: list[ApiClass] = []
        for module in modules:
            for function in module.functions:
                if self._public(function.signature.name):
                    functions.append(
                        ApiFunction(function.qualified_name, function.signature, function.location)
                    )
            for cls in module.classes:
                class_name = cls.qualified_name.rsplit(".", 1)[-1]
                if not self._public(class_name):
                    continue
                methods = tuple(
                    ApiFunction(
                        method.qualified_name,
                        method.signature,
                        method.location,
                        cls.qualified_name,
                    )
                    for method in cls.methods
                    if self._public(method.signature.name)
                )
                classes.append(ApiClass(cls.qualified_name, methods, cls.enum_members))
        return ApiVersion(
            ExternalLibrary(library),
            version,
            tuple(sorted(functions, key=lambda item: item.qualified_name)),
            tuple(sorted(classes, key=lambda item: item.qualified_name)),
        )

    def _public(self, name: str) -> bool:
        return self.include_private or not name.startswith("_")
