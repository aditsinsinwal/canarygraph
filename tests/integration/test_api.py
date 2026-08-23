from pathlib import Path

from fastapi.testclient import TestClient

from canarygraph.api import create_app
from canarygraph.persistence import Database


def test_analysis_rest_lifecycle(examples: Path, tmp_path: Path) -> None:
    app = create_app(Database(f"sqlite:///{tmp_path / 'test.db'}"))
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
