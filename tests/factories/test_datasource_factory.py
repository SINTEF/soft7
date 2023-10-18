"""Test the datasource factory."""
from typing import TYPE_CHECKING

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

    from s7.factories.datasource_factory import create_datasource

    # Creating the data resource
    requests_mock.post(
        "http://localhost:8080/api/v1/dataresource",
        json={"resource_id": "1234"},
    )

    # Getting the data resource
    # Create session
    requests_mock.post(
        "http://localhost:8080/api/v1/session",
        text=json.dumps({"session_id": "1234"}),
    )

    # Initialize
    requests_mock.post(
        "http://localhost:8080/api/v1/dataresource/1234/initialize",
        content=json.dumps({}).encode(encoding="utf-8"),
    )

    # Fetch
    requests_mock.get(
        "http://localhost:8080/api/v1/dataresource/1234",
        content=json.dumps(soft_datasource_init).encode(encoding="utf-8"),
    )

    create_datasource(entity=soft_entity_init, resource_config=generic_resource_config)
