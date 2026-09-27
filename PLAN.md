# Delivery plan

All MVP phases were developed as one integrated vertical slice. The phase labels remain useful as
acceptance boundaries.

| Phase | Deliverable | Status |
|---|---|---|
| 1 | Package foundation and explicit domain models | Complete |
| 2 | Python AST parsing | Complete |
| 3 | Imports, aliases, annotations, factories, inheritance, re-exports | Complete |
| 4 | Function call graph, confidence, and graph queries | Complete |
| 5 | SDK public API extraction, enums, visibility, aliases | Complete |
| 6–7 | Structured API diff and positive/negative/edge rule tests | Complete |
| 8 | Direct/transitive impact, endpoints, jobs, and tests | Complete |
| 9 | Documented deterministic risk score | Complete |
| 10 | Normalized PostgreSQL/SQLAlchemy/Alembic records and FastAPI | Complete |
| 11 | Safe LibCST callable/class/import/keyword transformations | Complete |
| 12 | Parse/compile/Ruff/mypy/pytest validation with safety controls | Complete |
| 13 | Breaking SDK and layered app fixtures | Complete |
| 14 | Docker image, migration-gated Compose stack, and CI | Complete |

## Post-MVP roadmap

1. Add protocol/generic-aware data-flow and interprocedural return-type inference.
2. Compare recorded runtime contract fixtures rather than configuration-only behavioral declarations.
3. Run untrusted validation in a hardened container or microVM with CPU, memory, and network limits.
4. Queue large analyses and add authentication, tenant quotas, retention, and audit logs.
5. Add more framework adapters and eventually a language-neutral intermediate representation.
