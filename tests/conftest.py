from pathlib import Path

import pytest


@pytest.fixture
def examples() -> Path:
    return Path(__file__).parents[1] / "examples"
