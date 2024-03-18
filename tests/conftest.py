"""Pytest fixtures for all tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Union


def static_folder() -> Path:
    """Path to the 'static' folder.

    This is here to support _generate_entity_test_cases() in
    tests/oteapi_plugin/test_soft7_function.py.
    """
    from pathlib import Path

    return Path(__file__).resolve().parent.resolve() / "static"


@pytest.fixture(name="static_folder")
def static_folder_fixture() -> Path:
    """Path to the 'static' folder."""
    path = static_folder()

    assert path.exists()
    assert path.is_dir()

    return path


@pytest.fixture()
def soft_entity_init(static_folder: Path) -> dict[str, Union[str, dict]]:
    """A dict for initializing a `SOFT7Entity`."""
    import yaml

    entity_path = static_folder / "soft_datasource_entity.yaml"
    assert entity_path.exists()
    entity = yaml.safe_load(entity_path.read_text(encoding="utf-8"))

    # entity should be parsed as a dict.
    assert isinstance(entity, dict)

    return entity
