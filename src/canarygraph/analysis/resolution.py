"""Best-effort, explainable import, call, and external-usage resolution."""

from __future__ import annotations

from dataclasses import dataclass

from canarygraph.domain import ApiUsage, Confidence, PythonFunction, PythonModule


def _relative_import(module: str, imported: str) -> str:
    dots = len(imported) - len(imported.lstrip("."))
    if not dots:
        return imported
    tail = imported[dots:]
    base = module.split(".")[:-1]
    keep = max(0, len(base) - dots + 1)
    prefix = base[:keep]
    return ".".join([*prefix, *([tail] if tail else [])])


@dataclass(frozen=True, slots=True)
class ResolvedCall:
    caller: str
    target: str
    confidence: Confidence


class SymbolResolver:
    def __init__(self, modules: tuple[PythonModule, ...]) -> None:
        self.modules = modules
        self.function_names = {
            function.qualified_name for module in modules for function in module.all_functions
        }
        self.class_names = {cls.qualified_name for module in modules for cls in module.classes}
        self.simple_functions: dict[str, list[str]] = {}
        self.simple_classes: dict[str, list[str]] = {}
        for name in self.function_names:
            self.simple_functions.setdefault(name.rsplit(".", 1)[-1], []).append(name)
        for name in self.class_names:
            self.simple_classes.setdefault(name.rsplit(".", 1)[-1], []).append(name)

    def resolve_call(
        self, module: PythonModule, function: PythonFunction, expression: str
    ) -> ResolvedCall:
        imports = {
            item.local_name: _relative_import(module.name, item.qualified_name)
            for item in module.imports
        }
        parts = expression.split(".")
        head = parts[0]
        if head in imports:
            return ResolvedCall(
                function.qualified_name, ".".join([imports[head], *parts[1:]]), Confidence.HIGH
            )

        local_types = dict(function.local_types)
        owner = function.qualified_name.rsplit(".", 1)[0]
        cls = next((item for item in module.classes if item.qualified_name == owner), None)
        if head == "self" and len(parts) >= 3 and cls:
            type_name = dict(cls.attribute_types).get(parts[1])
            if type_name:
                imported_type = imports.get(type_name, type_name)
                class_target = self._class_target(imported_type)
                return ResolvedCall(
                    function.qualified_name,
                    f"{class_target}.{'.'.join(parts[2:])}",
                    Confidence.HIGH if class_target in self.class_names else Confidence.MEDIUM,
                )
        if head in local_types and len(parts) >= 2:
            type_name = imports.get(local_types[head], local_types[head])
            class_target = self._class_target(type_name)
            return ResolvedCall(
                function.qualified_name,
                f"{class_target}.{'.'.join(parts[1:])}",
                Confidence.HIGH if class_target in self.class_names else Confidence.MEDIUM,
            )
        if head == "self" and len(parts) == 2:
            candidate = f"{owner}.{parts[1]}"
            if candidate in self.function_names:
                return ResolvedCall(function.qualified_name, candidate, Confidence.HIGH)
        if len(parts) == 1:
            candidates = self.simple_functions.get(head, [])
            same_module = [item for item in candidates if item.startswith(module.name + ".")]
            if len(same_module) == 1:
                return ResolvedCall(function.qualified_name, same_module[0], Confidence.HIGH)
            if len(candidates) == 1:
                return ResolvedCall(function.qualified_name, candidates[0], Confidence.MEDIUM)
        return ResolvedCall(function.qualified_name, expression, Confidence.LOW)

    def _class_target(self, name: str) -> str:
        if name in self.class_names:
            return name
        simple = name.rsplit(".", 1)[-1]
        candidates = self.simple_classes.get(simple, [])
        return candidates[0] if len(candidates) == 1 else name


class ExternalUsageResolver:
    """Resolve calls to a known library without pretending Python is fully static."""

    def resolve(
        self,
        modules: tuple[PythonModule, ...],
        *,
        library: str,
        known_symbols: set[str],
    ) -> tuple[ApiUsage, ...]:
        resolver = SymbolResolver(modules)
        usages: list[ApiUsage] = []
        for module in modules:
            for function in module.all_functions:
                for call in function.calls:
                    resolved = resolver.resolve_call(module, function, call.expression)
                    symbol = self._match(resolved.target, known_symbols)
                    if not symbol:
                        continue
                    confidence = resolved.confidence
                    if (
                        not resolved.target.startswith(library + ".")
                        and confidence == Confidence.HIGH
                    ):
                        confidence = Confidence.MEDIUM
                    usages.append(
                        ApiUsage(
                            symbol,
                            call,
                            confidence,
                            f"Resolved {call.expression!r} to {resolved.target!r}",
                        )
                    )
        return tuple(usages)

    @staticmethod
    def _match(target: str, symbols: set[str]) -> str | None:
        if target in symbols:
            return target
        target_parts = target.split(".")
        matches = [
            symbol
            for symbol in symbols
            if symbol.endswith("." + ".".join(target_parts[-2:]))
            or target.endswith("." + ".".join(symbol.split(".")[-2:]))
        ]
        if len(matches) == 1:
            return matches[0]
        simple_matches = [
            symbol for symbol in symbols if symbol.rsplit(".", 1)[-1] == target_parts[-1]
        ]
        return simple_matches[0] if len(simple_matches) == 1 else None
