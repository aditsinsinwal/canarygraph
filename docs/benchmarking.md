# Benchmarking

CanaryGraph includes a deterministic synthetic repository generator. It creates a configurable
number of modules, functions, and a transitive call chain ending at a deliberately changed SDK
method. The command runs the real scanner, parser, graph, diff, and blast-radius pipeline.

```bash
canarygraph benchmark --modules 100 --functions-per-module 5
```

The JSON result reports actual files, lines, modules, functions, graph nodes and edges, phase
timings, total analysis time, and peak Python memory measured by `tracemalloc`. Results are never
hard-coded; record the machine, Python version, commit, and command whenever publishing numbers.
