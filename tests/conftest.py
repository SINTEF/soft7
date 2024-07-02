"""Pytest fixtures for all tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from pathlib import Path
    from typing import Any, Union


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
def soft_entity_init_source(static_folder: Path) -> Path:
    """Source to the SOFT7 entity YAML file used in the `soft_entity_init` fixture."""
    return static_folder / "soft_datasource_entity.yaml"


@pytest.fixture()
def soft_entity_init(
    soft_entity_init_source: Path,
) -> dict[str, Union[str, dict[str, Any]]]:
    """A dict for initializing a `SOFT7Entity`."""
    import yaml

    assert soft_entity_init_source.exists()
    entity = yaml.safe_load(soft_entity_init_source.read_text(encoding="utf-8"))

    # entity should be parsed as a dict.
    assert isinstance(entity, dict)

    return entity


@pytest.fixture()
def soft_instance_data_source(static_folder: Path) -> Path:
    """Source to the SOFT7 instance data YAML file used in the `soft_instance_data`
    fixture.
    """
    return static_folder / "soft_datasource_entity_test_data.yaml"


@pytest.fixture()
def soft_instance_data(soft_instance_data_source: Path) -> dict[str, dict[str, Any]]:
    """A dict for initializing a `SOFT7Instance` based on the entity expressed in the
    `soft_entity_init` fixture."""
    import yaml

    assert soft_instance_data_source.exists()
    instance_data = yaml.safe_load(
        soft_instance_data_source.read_text(encoding="utf-8")
    )

    # instance_data should be parsed as a dict.
    assert isinstance(instance_data, dict)

    return instance_data
