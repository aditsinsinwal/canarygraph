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
    if not base:
        base = module.split(".")
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
        self.modules_by_name = {module.name: module for module in modules}
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
        self.classes = {item.qualified_name: item for module in modules for item in module.classes}
        self.functions = {
            item.qualified_name: item for module in modules for item in module.all_functions
        }

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

        local_types = {**dict(module.global_types), **dict(function.local_types)}
        owner = function.qualified_name.rsplit(".", 1)[0]
        cls = next((item for item in module.classes if item.qualified_name == owner), None)
        if head == "self" and len(parts) >= 3 and cls:
            type_name = self._attribute_type(cls.qualified_name, parts[1], module, imports)
            if type_name:
                class_target, confidence = self._resolve_type(type_name, module, imports)
                return ResolvedCall(
                    function.qualified_name,
                    f"{class_target}.{'.'.join(parts[2:])}",
                    confidence,
                )
        if head in local_types and len(parts) >= 2:
            class_target, confidence = self._resolve_type(local_types[head], module, imports)
            return ResolvedCall(
                function.qualified_name,
                f"{class_target}.{'.'.join(parts[1:])}",
                confidence,
            )
        if head == "self" and len(parts) == 2:
            candidate = f"{owner}.{parts[1]}"
            if candidate in self.function_names:
                return ResolvedCall(function.qualified_name, candidate, Confidence.HIGH)
            if cls:
                inherited = self._inherited_method(cls.qualified_name, parts[1], module, imports)
                if inherited:
                    return ResolvedCall(function.qualified_name, inherited, Confidence.HIGH)
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

    def _resolve_type(
        self,
        raw_name: str,
        module: PythonModule,
        imports: dict[str, str],
        visited: set[tuple[str, str]] | None = None,
    ) -> tuple[str, Confidence]:
        name = raw_name.strip("'\"")
        if "[" in name:
            name = name.split("[", 1)[0]
        visited = visited or set()
        key = (module.name, name)
        if key in visited:
            return name, Confidence.LOW
        visited.add(key)
        imported = imports.get(name)
        if imported:
            return self._class_target(imported), Confidence.HIGH
        same_module = f"{module.name}.{name}"
        if same_module in self.class_names:
            return same_module, Confidence.HIGH
        function_target = same_module if same_module in self.functions else None
        if not function_target:
            candidates = self.simple_functions.get(name, [])
            function_target = candidates[0] if len(candidates) == 1 else None
        if function_target:
            return_type = self.functions[function_target].signature.return_annotation
            defining_module = self._module_for_symbol(function_target)
            if return_type and defining_module:
                defining_imports = {
                    item.local_name: _relative_import(defining_module.name, item.qualified_name)
                    for item in defining_module.imports
                }
                target, _ = self._resolve_type(
                    return_type, defining_module, defining_imports, visited
                )
                return target, Confidence.MEDIUM
        target = self._class_target(name)
        confidence = Confidence.MEDIUM if target != name else Confidence.LOW
        return target, confidence

    def _module_for_symbol(self, symbol: str) -> PythonModule | None:
        candidates = [
            module
            for module in self.modules
            if symbol == module.name or symbol.startswith(module.name + ".")
        ]
        return max(candidates, key=lambda item: len(item.name), default=None)

    def _attribute_type(
        self,
        class_name: str,
        attribute: str,
        module: PythonModule,
        imports: dict[str, str],
        visited: set[str] | None = None,
    ) -> str | None:
        visited = visited or set()
        if class_name in visited:
            return None
        visited.add(class_name)
        cls = self.classes.get(class_name)
        if not cls:
            return None
        own = dict(cls.attribute_types).get(attribute)
        if own:
            return own
        for base in cls.bases:
            base_name, _ = self._resolve_type(base, module, imports)
            inherited = self._attribute_type(base_name, attribute, module, imports, visited)
            if inherited:
                return inherited
        return None

    def _inherited_method(
        self,
        class_name: str,
        method: str,
        module: PythonModule,
        imports: dict[str, str],
    ) -> str | None:
        cls = self.classes.get(class_name)
        if not cls:
            return None
        for base in cls.bases:
            base_name, _ = self._resolve_type(base, module, imports)
            candidate = f"{base_name}.{method}"
            if candidate in self.function_names:
                return candidate
        return None


class ExternalUsageResolver:
    """Resolve calls to a known library without pretending Python is fully static."""

    def resolve(
        self,
        modules: tuple[PythonModule, ...],
        *,
        library: str,
        known_symbols: set[str],
        aliases: dict[str, str] | None = None,
    ) -> tuple[ApiUsage, ...]:
        resolver = SymbolResolver(modules)
        aliases = aliases or {}
        usages: list[ApiUsage] = []
        for module in modules:
            for function in module.all_functions:
                for call in function.calls:
                    resolved = resolver.resolve_call(module, function, call.expression)
                    symbol = self._match(resolved.target, known_symbols)
                    if not symbol:
                        continue
                    symbol = aliases.get(symbol, symbol)
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
