"""Pytest fixtures for 'factoris'."""
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from typing import Union


@pytest.fixture
def generic_resource_config() -> "dict[str, Union[str, dict]]":
    """A generic resource config."""
    from oteapi import __version__ as oteapi_version
    from oteapi.models import ResourceConfig

    resource_config = {
        "accessService": "webelements",
        "accessUrl": "https://webelements.com",
    }

    assert ResourceConfig(**resource_config), (
        "Generic resource config defined for tests is invalid (using oteapi-core "
        f"version {oteapi_version})."
    )

    return resource_config
