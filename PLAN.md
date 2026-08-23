# Delivery plan

All MVP phases were developed as one integrated vertical slice. The phase labels remain useful as
acceptance boundaries.

| Phase | Deliverable | Status |
|---|---|---|
| 1 | Package foundation and explicit domain models | Complete |
| 2 | Python AST parsing | Complete |
| 3 | Imports, aliases, constructor types, external usages | Complete |
| 4 | Function call graph and graph queries | Complete |
| 5 | SDK public API extraction | Complete |
| 6–7 | Structured API diff and breaking rules | Complete |
| 8 | Direct/transitive blast radius and endpoints | Complete |
| 9 | Documented deterministic risk score | Complete |
| 10 | PostgreSQL/SQLAlchemy/Alembic and FastAPI | Complete |
| 11 | LibCST migration engine | Complete for supported safe rewrites |
| 12 | Parse/compile/static/test validation | Complete |
| 13 | Breaking SDK and layered app fixtures | Complete |
| 14 | Docker image and Compose stack | Complete |

## Next milestones

1. Improve type inference with assignment flow, return-type propagation, protocols, and inheritance.
2. Interpret package `__all__` and re-exports as first-class API aliases.
3. Add pytest fixture-driven behavioral contract comparison.
4. Add background-job entry-point adapters for Celery, Dramatiq, and RQ.
5. Add synthetic repository generation and publish measured, reproducible benchmarks.
6. Queue large analyses and enforce tenant-specific repository roots before multi-user deployment.

