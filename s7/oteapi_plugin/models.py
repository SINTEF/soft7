"""Pydantic data models for the SOFT7 OTEAPI plugin."""
from __future__ import annotations

from typing import Annotated, Literal, Optional

from oteapi.models import AttrDict, DataCacheConfig
from pydantic import Field

from s7.pydantic_models.oteapi import HashableFunctionConfig
from s7.pydantic_models.soft7_instance import SOFT7IdentityURI


class SOFT7GeneratorConfig(AttrDict):
    """SOFT7 Generator strategy-specific configuration."""

    datacache_config: Annotated[
        Optional[DataCacheConfig],
        Field(
            description=(
                "Configurations for the data cache for storing the downloaded file "
                "content."
            ),
        ),
    ] = None

    entity_identity: Annotated[
        Optional[SOFT7IdentityURI], Field(description="The top-level entity identity.")
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
