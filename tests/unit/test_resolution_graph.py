from pathlib import Path

from canarygraph.analysis import (
    CallGraph,
    ExternalUsageResolver,
    PythonRepositoryParser,
    SourceScanner,
)
from canarygraph.compatibility import SdkSurfaceExtractor


def test_alias_resolution_and_transitive_call_graph(examples: Path) -> None:
    modules = PythonRepositoryParser().parse_repository(
        SourceScanner().scan(examples / "example_store")
    )
    api = SdkSurfaceExtractor().extract(
        examples / "payment_sdk_v1", library="payment_sdk", version="1"
    )
    usages = ExternalUsageResolver().resolve(
        modules, library="payment_sdk", known_symbols=set(api.function_index)
    )
    create_usage = next(item for item in usages if item.symbol.endswith("create_payment"))
    graph = CallGraph.build(modules)

    assert create_usage.call_site.caller == "store.payment.PaymentService.charge"
    assert graph.shortest_path(
        "store.api.checkout_endpoint", "store.payment.PaymentService.charge"
    ) == (
        "store.api.checkout_endpoint",
        "store.checkout.CheckoutService.checkout",
        "store.payment.PaymentService.charge",
    )


def test_call_graph_direction_is_caller_to_callee(examples: Path) -> None:
    modules = PythonRepositoryParser().parse_repository(
        SourceScanner().scan(examples / "example_store")
    )
    graph = CallGraph.build(modules)

    assert graph.direct_callees("store.checkout.CheckoutService.checkout") == (
        "store.payment.PaymentService.charge",
    )
    assert graph.direct_callers("store.payment.PaymentService.charge") == (
        "store.checkout.CheckoutService.checkout",
    )
