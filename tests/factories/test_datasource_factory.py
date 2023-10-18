"""Test the datasource factory."""
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from typing import Any, Union

    from requests_mock import Mocker


def test_create_datasource(
    soft_entity_init: "dict[str, Union[str, dict]]",
    soft_datasource_init: "dict[str, Any]",
    generic_resource_config: "dict[str, Union[str, dict]]",
    requests_mock: "Mocker",
) -> None:
    """Test a straight forward call to create_datasource()."""
    import json

    from otelib.settings import Settings

    from s7.factories.datasource_factory import create_datasource

    default_oteapi_url = "http://localhost:8080"
    rest_api_prefix = Settings().prefix

    oteapi_url = f"{default_oteapi_url}{rest_api_prefix}"

    # Creating the data resource
    requests_mock.post(
        f"{oteapi_url}/dataresource",
        json={"resource_id": "1234"},
    )

    # Getting the data resource
    # Create session
    requests_mock.post(
        f"{oteapi_url}/session",
        text=json.dumps({"session_id": "1234"}),
    )

    # Initialize
    requests_mock.post(
        f"{oteapi_url}/dataresource/1234/initialize",
        content=json.dumps({}).encode(encoding="utf-8"),
    )

    # Fetch
    requests_mock.get(
        f"{oteapi_url}/dataresource/1234",
        content=json.dumps(soft_datasource_init).encode(encoding="utf-8"),
    )

    create_datasource(entity=soft_entity_init, resource_config=generic_resource_config)


@pytest.mark.usefixtures("load_test_strategies")
def test_inspect_created_dataresource(
    soft_entity_init: "dict[str, Union[str, dict]]",
    soft_datasource_init: "dict[str, Any]",
    generic_resource_config: "dict[str, Union[str, dict]]",
) -> None:
    """Test the generated data source contains the expected attributes and metadata."""
    from s7.factories.datasource_factory import create_datasource

    datasource = create_datasource(
        entity=soft_entity_init,
        resource_config=generic_resource_config,
        oteapi_url="python",
    )
    print(datasource)
