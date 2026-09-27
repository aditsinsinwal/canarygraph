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


def test_parser_extracts_globals_exports_jobs_parameters_and_tests(tmp_path: Path) -> None:
    package = tmp_path / "package"
    tests = tmp_path / "tests"
    package.mkdir()
    tests.mkdir()
    (package / "__init__.py").write_text("from .worker import run\n\n__all__ = ['run']\n")
    (package / "worker.py").write_text(
        "class Client:\n"
        "    pass\n\n"
        "client = Client()\n\n"
        "@dramatiq.actor\n"
        "def run(value: Client):\n"
        "    return value\n"
    )
    (tests / "test_worker.py").write_text("def test_run():\n    pass\n")

    modules = PythonRepositoryParser().parse_repository(SourceScanner().scan(tmp_path))
    init = next(module for module in modules if module.name == "package")
    worker = next(module for module in modules if module.name == "package.worker")
    test_module = next(module for module in modules if module.name == "tests.test_worker")

    assert init.explicit_exports == ("run",)
    assert worker.global_types == (("client", "Client"),)
    assert dict(worker.functions[0].local_types)["value"] == "Client"
    assert worker.functions[0].background_job is not None
    assert test_module.functions[0].is_test


def test_parser_records_starred_call_uncertainty(tmp_path: Path) -> None:
    source = tmp_path / "calls.py"
    source.write_text(
        "def invoke(client, args, kwargs):\n    return client.call(*args, **kwargs)\n"
    )

    module = PythonRepositoryParser().parse_repository(SourceScanner().scan(tmp_path))[0]
    call = module.functions[0].calls[0]

    assert call.has_star_arguments
    assert call.has_star_keywords
