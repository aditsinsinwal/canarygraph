"""Versioned REST API with durable analysis results."""

from __future__ import annotations

from collections.abc import Iterator
from dataclasses import asdict
from itertools import pairwise
from pathlib import Path
from typing import Any

from fastapi import Depends, FastAPI, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from canarygraph.api.schemas import AnalysisCreate, AnalysisCreated, ValidationRequest
from canarygraph.application import AnalysisRequest, AnalysisService
from canarygraph.compatibility import RenameMap
from canarygraph.domain import MigrationPatch
from canarygraph.exceptions import CanaryGraphError, InvalidRepositoryError
from canarygraph.migration import ValidationPipeline
from canarygraph.persistence import AnalysisStore, Database, get_database
from canarygraph.persistence.database import Settings


def create_app(database: Database | None = None) -> FastAPI:
    database = database or get_database()
    settings = Settings()
    allowed_roots = tuple(
        Path(item).expanduser().resolve()
        for item in settings.allowed_repository_roots.split(",")
        if item.strip()
    )
    database.create_schema()
    app = FastAPI(title="CanaryGraph", version="0.1.0")

    def session_dependency() -> Iterator[Session]:
        with database.sessions() as session:
            yield session

    def store_dependency(session: Session = Depends(session_dependency)) -> AnalysisStore:
        return AnalysisStore(session)

    def enforce_allowed_paths(payload: AnalysisCreate) -> None:
        if not allowed_roots:
            return
        candidates = [payload.repository, payload.old_api, payload.new_api]
        if payload.behavioral_fixture:
            candidates.append(payload.behavioral_fixture)
        for candidate in candidates:
            path = Path(candidate).resolve()
            if not any(path == root or path.is_relative_to(root) for root in allowed_roots):
                raise InvalidRepositoryError(f"Path is outside configured repository roots: {path}")

    @app.exception_handler(CanaryGraphError)
    async def canarygraph_error(_request: Any, exc: CanaryGraphError) -> JSONResponse:
        code = 404 if exc.code.endswith("NOT_FOUND") else 400
        return JSONResponse(
            status_code=code,
            content={"error": {"code": exc.code, "message": str(exc)}},
        )

    @app.exception_handler(ValueError)
    async def invalid_value(_request: Any, exc: ValueError) -> JSONResponse:
        return JSONResponse(
            status_code=400,
            content={"error": {"code": "INVALID_REQUEST", "message": str(exc)}},
        )

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.post(
        "/api/v1/analyses", response_model=AnalysisCreated, status_code=status.HTTP_201_CREATED
    )
    def create_analysis(
        payload: AnalysisCreate, store: AnalysisStore = Depends(store_dependency)
    ) -> AnalysisCreated:
        enforce_allowed_paths(payload)
        report = AnalysisService().analyze(
            AnalysisRequest(
                payload.repository,
                payload.old_api,
                payload.new_api,
                payload.library,
                payload.old_version,
                payload.new_version,
                RenameMap(payload.symbol_renames, payload.parameter_renames),
                payload.behavioral_fixture,
            )
        )
        store.save(report)
        return AnalysisCreated(id=report.id, status="COMPLETED")

    @app.get("/api/v1/analyses/{analysis_id}")
    def get_analysis(
        analysis_id: str, store: AnalysisStore = Depends(store_dependency)
    ) -> dict[str, Any]:
        return store.get(analysis_id).report

    @app.get("/api/v1/analyses/{analysis_id}/changes")
    def get_changes(
        analysis_id: str, store: AnalysisStore = Depends(store_dependency)
    ) -> dict[str, Any]:
        return {"items": store.get(analysis_id).report["changes"]}

    @app.get("/api/v1/analyses/{analysis_id}/blast-radius")
    def get_blast_radius(
        analysis_id: str, store: AnalysisStore = Depends(store_dependency)
    ) -> dict[str, Any]:
        findings = store.get(analysis_id).report["findings"]
        return {"items": [item["blast_radius"] for item in findings]}

    @app.get("/api/v1/analyses/{analysis_id}/graph")
    def get_graph(
        analysis_id: str, store: AnalysisStore = Depends(store_dependency)
    ) -> dict[str, Any]:
        findings = store.get(analysis_id).report["findings"]
        edges: set[tuple[str, str]] = set()
        for finding in findings:
            for path in finding["blast_radius"]["paths_to_usage"]:
                edges.update(pairwise(path))
        nodes = sorted({node for edge in edges for node in edge})
        return {
            "nodes": [{"id": node} for node in nodes],
            "edges": [{"caller": a, "callee": b} for a, b in sorted(edges)],
        }

    @app.post("/api/v1/findings/{finding_id}/migrations", status_code=status.HTTP_201_CREATED)
    def create_migration(
        finding_id: str, store: AnalysisStore = Depends(store_dependency)
    ) -> dict[str, Any]:
        analysis, finding = store.finding(finding_id)
        record = store.save_migration(analysis, finding)
        return {"id": record.id, "status": record.status, "patches": record.patches}

    @app.post("/api/v1/migrations/{migration_id}/validate")
    def validate_migration(
        migration_id: str,
        payload: ValidationRequest,
        store: AnalysisStore = Depends(store_dependency),
    ) -> dict[str, Any]:
        record = store.get_migration(migration_id)
        patches = tuple(MigrationPatch(**item) for item in record.patches)
        result = ValidationPipeline().validate(
            record.repository,
            patches,
            run_mypy=payload.run_mypy,
            run_tests=payload.run_tests,
        )
        record.status = result.status.value
        record.validation = asdict(result)
        store.session.commit()
        return asdict(result)

    return app


app = create_app()
