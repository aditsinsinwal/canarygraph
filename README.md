# CanaryGraph

CanaryGraph is a deterministic behavioral API compatibility and blast-radius analyzer for
Python repositories. It compares two local Python SDK source trees, finds structured breaking
changes, resolves application call sites, walks transitive callers to web entry points, scores
risk, and proposes only source transformations it can justify.

It does not execute repositories during analysis and it is not an LLM wrapper.

## Implemented MVP

- Safe Python source discovery and AST extraction for imports, aliases, classes, sync/async
  functions, signatures, calls, constructor types, enums, FastAPI routes, and Flask routes.
- Function-level caller → callee graph with direct, transitive, and shortest-path queries.
- Public SDK surface extraction and twelve deterministic compatibility rule families.
- Direct and transitive SDK impact, affected modules/classes/endpoints, transparent risk scores,
  machine-readable JSON, and terminal reports.
- Configured behavioral-change fixtures and explicit confidence/warnings for uncertain dispatch.
- LibCST callable/parameter rename and positional-to-keyword transformations.
- Isolated parse/compile/mypy/pytest validation with timeouts; tests are opt-in because validation
  executes repository code.
- Typer CLI, FastAPI REST API, SQLAlchemy persistence, PostgreSQL/Alembic, and Docker Compose.

## Quick start

Python 3.12 is required.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'

canarygraph analyze \
  --repo examples/example_store \
  --old-api examples/payment_sdk_v1 \
  --new-api examples/payment_sdk_v2 \
  --library payment_sdk \
  --rename-map examples/rename_map.json
```

Use `--json` for structured output or `--output report.json` to write a report. A behavioral
fixture can be supplied with `--behavioral-fixture examples/behavioral_changes.json`.

Run checks:

```bash
pytest
ruff check .
mypy src/canarygraph
```

## REST API

```bash
docker compose up --build
```

The API is served on `http://localhost:8000`; OpenAPI is at `/docs`.

| Method | Path | Purpose |
|---|---|---|
| POST | `/api/v1/analyses` | Run and persist a local analysis |
| GET | `/api/v1/analyses/{id}` | Get the complete report |
| GET | `/api/v1/analyses/{id}/changes` | Get structured changes |
| GET | `/api/v1/analyses/{id}/blast-radius` | Get impact results |
| GET | `/api/v1/analyses/{id}/graph` | Get affected graph paths |
| POST | `/api/v1/findings/{id}/migrations` | Persist a proposed migration |
| POST | `/api/v1/migrations/{id}/validate` | Validate patches in an isolated copy |

Example request:

```json
{
  "repository": "/workspace/examples/example_store",
  "old_api": "/workspace/examples/payment_sdk_v1",
  "new_api": "/workspace/examples/payment_sdk_v2",
  "library": "payment_sdk",
  "old_version": "1.0.0",
  "new_version": "2.0.0",
  "symbol_renames": {
    "payment_sdk.client.PaymentClient.capture":
      "payment_sdk.client.PaymentClient.authorize"
  }
}
```

## Design boundaries

Static resolution is necessarily conservative. Monkey patching, runtime imports, container-based
dependency injection, decorators that replace callables, and polymorphic dispatch may be unresolved
or marked with lower confidence. Behavioral differences are accepted only as structured, reviewed
fixtures in this version. See [docs/static_analysis.md](docs/static_analysis.md).

The REST service is intended for trusted local/on-premise operation. Configure an allowed workspace
at the deployment boundary, mount repositories read-only, and enable test validation only for trusted
code. Analysis itself reads source but never imports it.

## Project layout

```text
src/canarygraph/
  analysis/       # scanning, parsing, symbols, usage, call graph
  compatibility/  # SDK extraction, structured diff, impact, risk
  migration/      # planning, LibCST patches, isolated validation
  application/    # end-to-end orchestration
  api/             # FastAPI adapter and contracts
  persistence/     # SQLAlchemy adapter
  reporting/       # text report
examples/          # two SDK versions plus layered FastAPI application
tests/             # unit and end-to-end coverage
```

Read [PLAN.md](PLAN.md) for phase status and [docs/architecture.md](docs/architecture.md) for the
component model.

