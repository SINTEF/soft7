"""Pytest fixtures for 'factories'."""

from __future__ import annotations

import pytest


@pytest.fixture(scope="session", autouse=True)
def _load_strategies() -> None:
    """Load entry points strategies."""
    from oteapi.plugins import load_strategies

    load_strategies(test_for_uniqueness=False)


# @pytest.fixture
# def assert_all_responses_were_requested() -> bool:
#     return False
