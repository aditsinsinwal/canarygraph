from pathlib import Path

import pytest

from canarygraph.analysis.parser import PythonRepositoryParser, SourceScanner
from canarygraph.exceptions import InvalidRepositoryError


def test_parser_extracts_aliases_calls_and_endpoint(examples: Path) -> None:
    repository = SourceScanner().scan(examples / "example_store")
    modules = PythonRepositoryParser().parse_repository(repository)
    api = next(module for module in modules if module.name == "store.api")
    endpoint = api.functions[0]

    assert endpoint.endpoint is not None
    assert (endpoint.endpoint.method, endpoint.endpoint.path) == ("POST", "/checkout")
    assert [call.expression for call in endpoint.calls] == [
        "CheckoutService",
        "checkout_service.checkout",
    ]


def test_scanner_rejects_non_directory(tmp_path: Path) -> None:
    missing = tmp_path / "missing"
    with pytest.raises(InvalidRepositoryError):
        SourceScanner().scan(missing)


def test_parser_supports_async_and_keyword_only(tmp_path: Path) -> None:
    source = tmp_path / "sample.py"
    source.write_text("async def run(a: int, /, *, b: str = 'x') -> bool:\n    return True\n")
    module = PythonRepositoryParser().parse_repository(SourceScanner().scan(tmp_path))[0]
    signature = module.functions[0].signature

    assert signature.is_async
    assert signature.render() == "async run(a: int, /, *, b: str = 'x') -> bool"
