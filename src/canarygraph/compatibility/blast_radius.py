"""Direct and transitive impact analysis."""

from __future__ import annotations

from canarygraph.analysis.call_graph import CallGraph
from canarygraph.domain import ApiUsage, BlastRadius, BreakingChange, PythonModule


class BlastRadiusAnalyzer:
    def analyze(
        self,
        change: BreakingChange,
        usages: tuple[ApiUsage, ...],
        graph: CallGraph,
        modules: tuple[PythonModule, ...],
    ) -> BlastRadius:
        direct = {usage.call_site.caller for usage in usages if usage.symbol == change.symbol}
        transitive: set[str] = set()
        paths: set[tuple[str, ...]] = set()
        for target in direct:
            transitive.update(graph.transitive_callers(target))
            for caller in graph.transitive_callers(target):
                path = graph.shortest_path(caller, target)
                if path:
                    paths.add((*path, change.symbol))
            paths.add((target, change.symbol))
        transitive -= direct
        all_affected = direct | transitive
        functions = {
            function.qualified_name: function
            for module in modules
            for function in module.all_functions
        }
        endpoints = []
        background_jobs = []
        affected_tests = []
        for name in all_affected:
            affected_function = functions.get(name)
            endpoint = affected_function.endpoint if affected_function else None
            if endpoint is not None:
                endpoints.append(endpoint)
            if affected_function and affected_function.background_job:
                background_jobs.append(affected_function.background_job)
            if affected_function and affected_function.is_test:
                affected_tests.append(name)
        endpoints_tuple = tuple(sorted(endpoints, key=lambda item: (item.path, item.method)))
        class_names = {
            cls.qualified_name
            for module in modules
            for cls in module.classes
            if any(name.startswith(cls.qualified_name + ".") for name in all_affected)
        }
        module_names = {
            module.name
            for module in modules
            if any(
                name == module.name or name.startswith(module.name + ".") for name in all_affected
            )
        }
        return BlastRadius(
            direct_functions=tuple(sorted(direct)),
            transitive_functions=tuple(sorted(transitive)),
            affected_classes=tuple(sorted(class_names)),
            affected_modules=tuple(sorted(module_names)),
            affected_endpoints=endpoints_tuple,
            paths_to_usage=tuple(sorted(paths)),
            affected_background_jobs=tuple(sorted(background_jobs, key=lambda item: item.function)),
            affected_tests=tuple(sorted(affected_tests)),
        )
