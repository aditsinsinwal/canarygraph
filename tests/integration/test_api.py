from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import func, select

from canarygraph.api import create_app
from canarygraph.persistence import Database
from canarygraph.persistence.models import (
    ApiVersionRecord,
    BlastRadiusRecord,
    BreakingChangeRecord,
    FindingRecord,
)


def test_analysis_rest_lifecycle(examples: Path, tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'test.db'}")
    app = create_app(database)
    client = TestClient(app)
    response = client.post(
        "/api/v1/analyses",
        json={
            "repository": str(examples / "example_store"),
            "old_api": str(examples / "payment_sdk_v1"),
            "new_api": str(examples / "payment_sdk_v2"),
            "library": "payment_sdk",
        },
    )

    assert response.status_code == 201
    analysis_id = response.json()["id"]
    assert client.get(f"/api/v1/analyses/{analysis_id}").status_code == 200
    assert client.get(f"/api/v1/analyses/{analysis_id}/changes").json()["items"]
    assert client.get(f"/api/v1/analyses/{analysis_id}/blast-radius").status_code == 200
    assert client.get(f"/api/v1/analyses/{analysis_id}/graph").status_code == 200
    assert client.get("/health/ready").json() == {"status": "ready"}
    with database.sessions() as session:
        assert session.scalar(select(func.count()).select_from(ApiVersionRecord)) == 2
        changes = session.scalar(select(func.count()).select_from(BreakingChangeRecord))
        findings = session.scalar(select(func.count()).select_from(FindingRecord))
        radii = session.scalar(select(func.count()).select_from(BlastRadiusRecord))
        assert changes == findings == radii


def test_migration_creation_and_validation_lifecycle(examples: Path, tmp_path: Path) -> None:
    database = Database(f"sqlite:///{tmp_path / 'test.db'}")
    client = TestClient(create_app(database))
    response = client.post(
        "/api/v1/analyses",
        json={
            "repository": str(examples / "example_store"),
            "old_api": str(examples / "payment_sdk_v1"),
            "new_api": str(examples / "payment_sdk_v2"),
            "library": "payment_sdk",
            "symbol_renames": {
                "payment_sdk.client.PaymentClient.capture": (
                    "payment_sdk.client.PaymentClient.authorize"
                )
            },
        },
    )
    report = client.get(f"/api/v1/analyses/{response.json()['id']}").json()
    finding = next(
        item for item in report["findings"] if item["change"]["kind"] == "METHOD_RENAMED"
    )

    migration = client.post(f"/api/v1/findings/{finding['id']}/migrations")
    validation = client.post(
        f"/api/v1/migrations/{migration.json()['id']}/validate",
        json={"run_ruff": False, "run_mypy": False, "run_tests": False},
    )

    assert migration.status_code == 201
    assert validation.status_code == 200
    assert validation.json()["status"] == "VALIDATED"


def test_missing_analysis_returns_structured_error(tmp_path: Path) -> None:
    client = TestClient(create_app(Database(f"sqlite:///{tmp_path / 'test.db'}")))

    response = client.get("/api/v1/analyses/missing")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "ANALYSIS_NOT_FOUND"


def test_configured_root_blocks_arbitrary_server_paths(
    examples: Path, tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("CANARYGRAPH_ALLOWED_REPOSITORY_ROOTS", str(examples))
    client = TestClient(create_app(Database(f"sqlite:///{tmp_path / 'test.db'}")))

    response = client.post(
        "/api/v1/analyses",
        json={
            "repository": str(tmp_path),
            "old_api": str(examples / "payment_sdk_v1"),
            "new_api": str(examples / "payment_sdk_v2"),
            "library": "payment_sdk",
        },
    )

    assert response.status_code == 400
    assert response.json()["error"]["code"] == "INVALID_REPOSITORY"
