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
from typing import TYPE_CHECKING, Annotated

import yaml
from oteapi.models import ResourceConfig
from otelib import OTEClient
from pydantic import Field, create_model

from s7.pydantic_models.oteapi import HashableResourceConfig
from s7.pydantic_models.soft7 import SOFT7DataEntity, SOFT7Entity, map_soft_to_py_types

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any, Optional, Union, Protocol

    class GetProperty(Protocol):
        """Protocol for getting a property."""

        def __call__(self, name: str) -> Any:
            ...


def _get_property(
    config: HashableResourceConfig, url: "Optional[str]" = None
) -> "GetProperty":
    """Get a property."""
    client = OTEClient(url or "http://localhost:8080")
    data_resource = client.create_dataresource(**config.model_dump())
    result: "dict[str, Any]" = json.loads(data_resource.get())

    # Remove unused variables from memory
    del client
    del data_resource

    def __get_property(name: str) -> "Any":
        if name in result:
            return result[name]

        raise AttributeError(f"{name!r} could not be determined")

    return __get_property


def create_entity(
    data_model: "Union[SOFT7Entity, dict[str, Any], Path, str]",
    resource_config: "Union[HashableResourceConfig, ResourceConfig, dict[str, Any]]",
) -> type[SOFT7DataEntity]:
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
    # Handle the case of data model being a string/path to a YAML file
    if isinstance(data_model, (str, Path)):
        data_model_path = Path(data_model).resolve()

        if not data_model_path.exists():
            raise FileNotFoundError(
                f"Could not find a data model YAML file at {data_model_path}"
            )

        data_model = yaml.safe_load(data_model_path.read_text(encoding="utf8"))

        if not isinstance(data_model, dict):
            raise TypeError(
                f"Data model YAML file at {data_model_path} did not contain a "
                "dictionary"
            )

    # Now the data model is either a SOFT7Entity instance or a dictionary, ready to be
    # used to create the SOFT7Entity instance.
    if isinstance(data_model, dict):
        data_model = SOFT7Entity(**data_model)

    if not isinstance(data_model, SOFT7Entity):
        raise TypeError(
            f"data_model must be a 'SOFT7Entity', instead it was a {type(data_model)}"
        )

    # Handle the case of resource_config being a dictionary or a "pure" OTEAPI Core
    # ResourceConfig. We need to convert it to a HashableResourceConfig.
    if isinstance(resource_config, dict):
        resource_config = HashableResourceConfig(**resource_config)

    if isinstance(resource_config, ResourceConfig) and not isinstance(
        resource_config, HashableResourceConfig
    ):
        resource_config = HashableResourceConfig(
            **resource_config.model_dump(exclude_defaults=True)
        )

    if not isinstance(resource_config, HashableResourceConfig):
        raise TypeError(
            "resource_config must be a 'HashableResourceConfig', instead it was a "
            f"{type(resource_config)}"
        )

    field_definitions = {
        property_name: Annotated[
            map_soft_to_py_types[property_value.type_],
            Field(
                # mypy cannot recognize that resource_config is HashableResourceConfig
                # even though it's checked above (see isinstance() check above)
                default_factory=lambda: _get_property(resource_config),  # type: ignore[arg-type]  # noqa: E501
                description=property_value.description or "",
                title=property_name.replace(" ", "_"),
                validate_default=True,
                json_schema_extra={
                    f"x-{field}": getattr(property_value, field)
                    for field in property_value.model_fields
                    if (
                        field not in ("description", "type_", "shape")
                        and getattr(property_value, field)
                    )
                },
            ),
        ]
        for property_name, property_value in data_model.properties.items()
    }

    return create_model(
        "DataSourceEntity",
        __config__=None,
        __base__=SOFT7DataEntity,
        __module__=__name__,
        __validators__=None,
        __cls_kwargs__=None,
        **field_definitions,
    )
