"""Pytest fixtures for the pydantic models tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from typing import Literal

    from s7.pydantic_models.oteapi import (
        HashableFunctionConfig,
        HashableMappingConfig,
        HashableParserConfig,
        HashableResourceConfig,
    )


@pytest.fixture
def name_to_config_type_mapping() -> dict[
    Literal["dataresource", "function", "mapping", "parser"],
    type[
        HashableFunctionConfig
        | HashableMappingConfig
        | HashableParserConfig
        | HashableResourceConfig
    ],
]:
    from s7.pydantic_models.oteapi import (
        HashableFunctionConfig,
        HashableMappingConfig,
        HashableParserConfig,
        HashableResourceConfig,
    )

    return {
        "dataresource": HashableResourceConfig,
        "function": HashableFunctionConfig,
        "mapping": HashableMappingConfig,
        "parser": HashableParserConfig,
    }
