"""Pydantic data models for the SOFT7 OTEAPI plugin."""
from __future__ import annotations

from typing import Annotated, Literal

from oteapi.models import AttrDict, DataCacheConfig
from pydantic import Field

from s7.pydantic_models.oteapi import HashableFunctionConfig


class SOFT7GeneratorConfig(AttrDict):
    """SOFT7 Generator strategy-specific configuration."""

    datacache_config: Annotated[
        DataCacheConfig | None,
        Field(
            description=(
                "Configurations for the data cache for storing the downloaded file "
                "content."
            ),
        ),
    ] = None


class SOFT7FunctionConfig(HashableFunctionConfig):
    """SOFT7 OTEAPI Function strategy configuration."""

    functionType: Annotated[
        Literal["soft7", "SOFT7"],
        Field(
            description=HashableFunctionConfig.model_fields["functionType"].description,
        ),
    ]

    configuration: Annotated[
        SOFT7GeneratorConfig, Field(description=SOFT7GeneratorConfig.__doc__)
    ] = SOFT7GeneratorConfig()
