# Roadmap

V1 deliberately targets local Python projects and Python SDKs. The shipped MVP includes conservative
static resolution, packaging/re-export aliases, web/background/test entry points, structured behavior
fixtures, safe migrations, normalized persistence, CI, and reproducible synthetic benchmarks.

Before hosted multi-user operation, add per-tenant allowed roots, job queues, resource quotas,
content-retention controls, sandboxed validation workers, authentication, and audit logging. A graph
database, distributed stream, Kubernetes, language-general IR, and GitHub App remain out of scope
until measured workload or product needs justify them.
