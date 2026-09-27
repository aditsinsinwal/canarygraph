"""Extract a public Python SDK surface from source without importing it."""

from __future__ import annotations

from pathlib import Path

from canarygraph.analysis.parser import PythonRepositoryParser, SourceScanner
from canarygraph.analysis.resolution import _relative_import
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
        aliases: dict[str, str] = {}
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
                classes.append(
                    ApiClass(
                        cls.qualified_name,
                        methods,
                        tuple(member for member in cls.enum_members if self._public(member)),
                    )
                )
        class_index = {item.qualified_name: item for item in classes}
        function_index = {item.qualified_name: item for item in functions}
        for module in modules:
            if Path(module.path).name != "__init__.py":
                continue
            allowed = set(module.explicit_exports)
            for binding in module.imports:
                if allowed and binding.local_name not in allowed:
                    continue
                if not self._public(binding.local_name):
                    continue
                target = _relative_import(module.name, binding.qualified_name)
                alias = f"{module.name}.{binding.local_name}"
                if target in class_index:
                    aliases[alias] = target
                    for method in class_index[target].methods:
                        aliases[f"{alias}.{method.signature.name}"] = method.qualified_name
                elif target in function_index:
                    aliases[alias] = target
        return ApiVersion(
            ExternalLibrary(library),
            version,
            tuple(sorted(functions, key=lambda item: item.qualified_name)),
            tuple(sorted(classes, key=lambda item: item.qualified_name)),
            tuple(sorted(aliases.items())),
        )

    def _public(self, name: str) -> bool:
        return self.include_private or not name.startswith("_")
