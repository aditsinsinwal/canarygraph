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
        and item.change.parameter == "currency"
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


def test_inheritance_factory_jobs_tests_and_package_reexports(
    examples: Path, tmp_path: Path
) -> None:
    app_root = tmp_path / "application"
    tests_root = app_root / "tests"
    app_root.mkdir()
    tests_root.mkdir()
    (app_root / "app.py").write_text(
        "from payment_sdk import PaymentClient\n\n"
        "class BaseService:\n"
        "    def __init__(self):\n"
        "        self.client = PaymentClient()\n\n"
        "class PaymentService(BaseService):\n"
        "    def charge(self, amount):\n"
        "        return self.client.create_payment(amount)\n\n"
        "def build_service() -> PaymentService:\n"
        "    return PaymentService()\n\n"
        "service = build_service()\n\n"
        "@dramatiq.actor\n"
        "def charge_job(amount):\n"
        "    return service.charge(amount)\n"
    )
    (tests_root / "test_app.py").write_text(
        "from app import charge_job\n\ndef test_charge():\n    return charge_job(100)\n"
    )

    report = AnalysisService().analyze(
        AnalysisRequest(
            str(app_root),
            str(examples / "payment_sdk_v1"),
            str(examples / "payment_sdk_v2"),
            "payment_sdk",
        )
    )
    finding = next(
        item
        for item in report.findings
        if item.change.kind == ChangeKind.REQUIRED_PARAMETER_ADDED
        and item.change.symbol.endswith("create_payment")
        and item.change.parameter == "currency"
    )

    assert finding.blast_radius.direct_functions == ("app.PaymentService.charge",)
    assert "app.charge_job" in finding.blast_radius.transitive_functions
    assert finding.blast_radius.affected_background_jobs[0].framework == "Dramatiq"
    assert finding.blast_radius.affected_tests == ("tests.test_app.test_charge",)
    assert finding.usages[0].confidence.value == "HIGH"


def test_function_and_module_rename_preserves_import_alias(tmp_path: Path) -> None:
    app_root = tmp_path / "app"
    old_root = tmp_path / "old"
    new_root = tmp_path / "new"
    (old_root / "sdk").mkdir(parents=True)
    (new_root / "sdk").mkdir(parents=True)
    app_root.mkdir()
    (old_root / "sdk" / "old_module.py").write_text("def old():\n    return 1\n")
    (new_root / "sdk" / "new_module.py").write_text("def new():\n    return 1\n")
    (app_root / "app.py").write_text(
        "from sdk.old_module import old as invoke\n\ndef use():\n    return invoke()\n"
    )
    renames = RenameMap({"sdk.old_module.old": "sdk.new_module.new"})

    report = AnalysisService().analyze(
        AnalysisRequest(str(app_root), str(old_root), str(new_root), "sdk", renames=renames)
    )
    finding = next(
        item for item in report.findings if item.change.kind == ChangeKind.FUNCTION_RENAMED
    )
    after = finding.migration.patches[0].after

    assert "from sdk.new_module import new as invoke" in after
    assert "return invoke()" in after


def test_keyword_rename_and_keyword_only_rewrites_are_source_preserving(
    examples: Path, tmp_path: Path
) -> None:
    app_root = tmp_path / "app"
    app_root.mkdir()
    (app_root / "usage.py").write_text(
        "from payment_sdk import PaymentClient\n\n"
        "client = PaymentClient()\n\n"
        "def create():\n"
        "    return client.create_payment(amount=100)\n\n"
        "def refund():\n"
        "    return client.refund('payment-id', 'duplicate')\n"
    )
    report = AnalysisService().analyze(
        AnalysisRequest(
            str(app_root),
            str(examples / "payment_sdk_v1"),
            str(examples / "payment_sdk_v2"),
            "payment_sdk",
            renames=RenameMap(
                parameters={
                    "payment_sdk.client.PaymentClient.create_payment": {"amount": "amount_cents"}
                }
            ),
        )
    )
    renamed = next(
        item for item in report.findings if item.change.kind == ChangeKind.PARAMETER_RENAMED
    )
    keyword_only = next(
        item
        for item in report.findings
        if item.change.kind == ChangeKind.PARAMETER_BECAME_KEYWORD_ONLY
    )

    assert "create_payment(amount_cents=100)" in renamed.migration.patches[0].after
    assert "refund('payment-id', reason = 'duplicate')" in keyword_only.migration.patches[0].after
