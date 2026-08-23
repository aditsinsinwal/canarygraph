import json
from pathlib import Path

from canarygraph.application import AnalysisRequest, AnalysisService
from canarygraph.compatibility import RenameMap
from canarygraph.domain import ChangeKind, MigrationStatus, RiskLevel
from canarygraph.reporting import render_text


def test_end_to_end_blast_radius_reaches_http_endpoint(examples: Path) -> None:
    request = AnalysisRequest(
        str(examples / "example_store"),
        str(examples / "payment_sdk_v1"),
        str(examples / "payment_sdk_v2"),
        "payment_sdk",
        "1.0.0",
        "2.0.0",
        RenameMap(
            {
                "payment_sdk.client.PaymentClient.capture": (
                    "payment_sdk.client.PaymentClient.authorize"
                )
            },
            {"payment_sdk.client.PaymentClient.create_payment": {"amount": "amount_cents"}},
        ),
    )
    report = AnalysisService().analyze(request)
    finding = next(
        item
        for item in report.findings
        if item.change.kind == ChangeKind.REQUIRED_PARAMETER_ADDED
        and item.change.symbol.endswith("create_payment")
    )

    assert finding.blast_radius.direct_functions == ("store.payment.PaymentService.charge",)
    assert "store.checkout.CheckoutService.checkout" in finding.blast_radius.transitive_functions
    assert finding.blast_radius.affected_endpoints[0].path == "/checkout"
    assert finding.migration.status == MigrationStatus.REVIEW_REQUIRED
    assert finding.risk.level in {RiskLevel.HIGH, RiskLevel.CRITICAL}
    assert "POST /checkout" in render_text(report)
    json.dumps(report.to_dict())


def test_known_method_rename_generates_source_preserving_patch(examples: Path) -> None:
    report = AnalysisService().analyze(
        AnalysisRequest(
            str(examples / "example_store"),
            str(examples / "payment_sdk_v1"),
            str(examples / "payment_sdk_v2"),
            "payment_sdk",
            renames=RenameMap(
                {
                    "payment_sdk.client.PaymentClient.capture": (
                        "payment_sdk.client.PaymentClient.authorize"
                    )
                }
            ),
        )
    )
    finding = next(
        item for item in report.findings if item.change.kind == ChangeKind.METHOD_RENAMED
    )

    assert finding.migration.status == MigrationStatus.AVAILABLE
    assert "self.client.authorize(payment_id)" in finding.migration.patches[0].after


def test_class_rename_updates_import_and_constructor(tmp_path: Path) -> None:
    app_root, old_root, new_root = tmp_path / "app", tmp_path / "old", tmp_path / "new"
    app_root.mkdir()
    old_root.mkdir()
    new_root.mkdir()
    (app_root / "app.py").write_text("from sdk import Old\n\ndef build():\n    return Old()\n")
    (old_root / "sdk.py").write_text("class Old:\n    pass\n")
    (new_root / "sdk.py").write_text("class New:\n    pass\n")

    report = AnalysisService().analyze(
        AnalysisRequest(
            str(app_root),
            str(old_root),
            str(new_root),
            "sdk",
            renames=RenameMap({"sdk.Old": "sdk.New"}),
        )
    )
    finding = next(item for item in report.findings if item.change.kind == ChangeKind.CLASS_RENAMED)

    assert finding.blast_radius.direct_functions == ("app.build",)
    assert "from sdk import New" in finding.migration.patches[0].after
    assert "return New()" in finding.migration.patches[0].after
