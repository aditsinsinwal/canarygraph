# Architecture

```mermaid
flowchart TD
  Repo[Application repository] --> Scan[Safe source scanner]
  Scan --> AST[AST intermediate model]
  AST --> Resolve[Symbol and SDK usage resolver]
  AST --> Graph[Caller to callee graph]
  Old[Old SDK] --> Surface1[Public API extractor]
  New[New SDK] --> Surface2[Public API extractor]
  Surface1 --> Diff[Structured compatibility rules]
  Surface2 --> Diff
  Resolve --> Impact[Blast-radius analyzer]
  Graph --> Impact
  Diff --> Impact
  Impact --> Risk[Risk scorer]
  Impact --> Plan[Migration planner]
  Plan --> CST[LibCST transformer]
  CST --> Validate[Isolated validator]
  Risk --> Report[Compatibility report]
  Validate --> Report
  Report --> CLI[CLI]
  Report --> API[FastAPI]
  API --> DB[(PostgreSQL)]
```

The dependency direction is inward. `domain.py`, `analysis`, `compatibility`, and `migration` have no
dependency on FastAPI or SQLAlchemy. The application service composes deterministic core components;
CLI, HTTP, and persistence are replaceable adapters.

One process is intentional for V1. NetworkX holds the graph in memory. SQL stores the immutable report
plus normalized API-version, change, finding, blast-radius, and migration records. Alembic owns
relational schema evolution, and Docker Compose blocks API startup until migrations succeed.
