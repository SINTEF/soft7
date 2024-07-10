"""Strategy class for application/yaml."""

from __future__ import annotations

import sys
from typing import Annotated, Optional, Union

if sys.version_info >= (3, 10):
    from typing import Literal
else:
    from typing_extensions import Literal

import yaml
from oteapi.datacache import DataCache
from oteapi.models import (
    AttrDict,
    DataCacheConfig,
    HostlessAnyUrl,
    ParserConfig,
    ResourceConfig,
)
from oteapi.plugins import create_strategy
from pydantic import Field
from pydantic.dataclasses import dataclass


class YAMLConfig(AttrDict):
    """YAML parse-specific Configuration Data Model.

    From https://github.com/mime-types/mime-types-data it seems there are only two
    official MIME types for YAML:

    - `application/yaml`
    - `text/x-yaml`

    Where, `application/yaml` is the official MIME type for YAML 1.2 (new) and
    `text/x-yaml` is the old MIME type.
    """

    downloadUrl: Annotated[
        Optional[HostlessAnyUrl],
        Field(description=ResourceConfig.model_fields["downloadUrl"].description),
    ] = None

    mediaType: Annotated[
        Literal["application/yaml", "text/x-yaml"],
        Field(description=ResourceConfig.model_fields["mediaType"].description),
    ] = "application/yaml"

    datacache_config: Annotated[
        Optional[DataCacheConfig],
        Field(
            description=(
                "Configuration for the data cache for storing the downloaded file "
                "content."
            ),
        ),
    ] = None


class YAMLParserConfig(ParserConfig):
    """YAML parse strategy filter config."""

    parserType: Annotated[
        Literal["parser/yaml", "parser/yml"],
        Field(description=ParserConfig.model_fields["parserType"].description),
    ] = "parser/yaml"

    configuration: Annotated[
        YAMLConfig, Field(description="YAML parse strategy-specific configuration.")
    ] = YAMLConfig()


class YAMLParseResult(AttrDict):
    """Class for returning values from YAML Parse."""

    content: Annotated[
        Union[dict, list[dict]], Field(description="Content of the YAML document.")
    ]


@dataclass
class YAMLDataParseStrategy:
    """Parse strategy for YAML.

    **Registers strategies**:

    - `("mediaType", "parser/yaml")`
    - `("mediaType", "parser/yml")`

    """

    parse_config: YAMLParserConfig

    def initialize(self) -> AttrDict:
        """Initialize."""
        return AttrDict()

    def get(self) -> YAMLParseResult:
        """Parse YAML."""
        downloader = create_strategy(
            "download", self.parse_config.configuration.model_dump()
        )
        output = downloader.get()
        cache = DataCache(self.parse_config.configuration.datacache_config)
        content = cache.get(output["key"])

        if isinstance(content, (dict, list)):
            return YAMLParseResult(content=content)

        parsed_content = list(yaml.safe_load_all(content))
        if len(parsed_content) == 1:
            parsed_content = parsed_content[0]

        return YAMLParseResult(content=parsed_content)
