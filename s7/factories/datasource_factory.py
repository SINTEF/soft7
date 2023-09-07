"""Generate SOFT7 entities based on basic information:

1. Data source (DB, File, Webpage, ...)
2. Generic data source parser
3. Data source parser configuration
4. SOFT7 entity data model.

Parts 2 and 3 are together considered to produce the "specific parser".
Parts 1 through 3 are provided through a single dictionary based on the
`ResourceConfig` from `oteapi.models`.

"""
import json
from pathlib import Path
from typing import Any, Optional, Type, Union

import yaml
from oteapi.models import ResourceConfig
from otelib import OTEClient
from pydantic import Field, create_model

from s7.pydantic_models.oteapi import HashableResourceConfig
from s7.pydantic_models.soft7 import SOFT7DataEntity, SOFT7Entity


def _get_property(config: HashableResourceConfig, url: Optional[str] = None) -> Any:
    """Get a property."""
    client = OTEClient(url or "http://localhost:8080")
    data_resource = client.create_dataresource(**config.dict())
    result: dict[str, Any] = json.loads(data_resource.get())

    def __get_property(name: str) -> Any:
        if name in result:
            return result[name]

        raise AttributeError(f"{name!r} could not be determined")

    return __get_property


# def _get_property_local(
#     config: HashableResourceConfig,
# ) -> Any:
#     """TEMPORARY - Get a property - local."""
#     from s7.temporary.xlsparser import XLSParser

#     parser = XLSParser(config.configuration).get()

#     def __get_property_local(name: str) -> Any:
#         if name in parser:
#             return parser[name]

#         raise ValueError(f"Could find no data for {name!r}")

#     return __get_property_local


def create_entity(
    data_model: Union[SOFT7Entity, Path, str, dict[str, Any]],
    resource_config: Union[HashableResourceConfig, ResourceConfig, dict[str, Any]],
) -> Type[SOFT7DataEntity]:
    """Create and return a SOFT7 entity wrapped as a pydantic model.

    Parameters:
        data_model: A SOFT7 data model entity or a string/path to a YAML file of the
            data model.
        resource_config: A
            [`ResourceConfig`](https://emmc-asbl.github.io/oteapi-core/latest/
            all_models/#oteapi.models.ResourceConfig)
            or a valid dictionary that can be used to instantiate it.

    Returns:
        A SOFT7 entity class wrapped as a pydantic data model.

    """
    if isinstance(data_model, (str, Path)):
        if not Path(data_model).resolve().exists():
            raise FileNotFoundError(
                f"Could not find a data model YAML file at {data_model!r}"
            )
        data_model: dict[str, Any] = yaml.safe_load(  # type: ignore[no-redef]
            Path(data_model).resolve().read_text(encoding="utf8")
        )
    if isinstance(data_model, dict):
        data_model = SOFT7Entity(**data_model)
    if not isinstance(data_model, SOFT7Entity):
        raise TypeError("data_model must be a 'SOFT7Entity'")

    if isinstance(resource_config, dict):
        resource_config = HashableResourceConfig(**resource_config)
    if isinstance(resource_config, ResourceConfig) and not isinstance(
        resource_config, HashableResourceConfig
    ):
        resource_config = HashableResourceConfig(
            **resource_config.dict(exclude_defaults=True)
        )
    if not isinstance(resource_config, HashableResourceConfig):
        raise TypeError("resource_config must be a 'ResourceConfig' (from oteapi-core)")
    resource_config: HashableResourceConfig  # type: ignore[no-redef]  # Satisfy mypy

    if any(property_name.startswith("_") for property_name in data_model.properties):
        raise ValueError(
            "data model property names may not start with an underscore (_)"
        )

    return create_model(  # type: ignore[call-overload]
        __model_name="DataSourceEntity",
        __config__=None,
        __base__=SOFT7DataEntity,
        __module__=__name__,
        __validators__=None,
        __cls_kwargs__=None,
        **{
            property_name: Field(  # type: ignore[pydantic-field]
                default_factory=lambda: _get_property(resource_config),
                description=property_value.description or "",
                title=property_name.replace(" ", "_"),
                type=property_value.type_.py_cls,
                **{
                    f"x-{field}": getattr(property_value, field)
                    for field in property_value.__fields__
                    if field not in ("description", "type_", "shape")
                    and getattr(property_value, field)
                },
            )
            for property_name, property_value in data_model.properties.items()
        },
    )
