"""Pytest fixtures for 'factories'."""

from __future__ import annotations

import pytest


@pytest.fixture(scope="session", autouse=True)
def _load_strategies() -> None:
    """Load entry points strategies."""
    from oteapi.plugins import load_strategies

    load_strategies(test_for_uniqueness=False)


@pytest.fixture(autouse=True)
def _clear_cache() -> None:
    """Clear the cache before each test."""
    from s7.factories.datasource_factory import CACHE

    CACHE.clear()
