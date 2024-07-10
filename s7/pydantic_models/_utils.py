"""Utility functions and more for the pydantic models."""

from __future__ import annotations

from typing import TYPE_CHECKING

import yaml
from pydantic import AnyUrl, ValidationError

if TYPE_CHECKING:  # pragma: no cover
    from typing import Any

    from s7.exceptions import S7EntityError


def is_valid_url(url: str | AnyUrl) -> bool:
    """Check if the URL is valid."""
    try:
        url = AnyUrl(str(url))
    except ValidationError:
        return False

    return not any(getattr(url, url_part) is None for url_part in ["scheme", "host"])


def try_load_from_json_yaml(
    source: str,
    exception_cls: type[S7EntityError] | None = None,
    exception_msg: str | None = None,
) -> dict[Any, Any]:
    """Try to load the source from a JSON/YAML string."""
    if exception_cls is None:
        from s7.exceptions import S7EntityError

        exception_cls = S7EntityError

    if exception_msg is None:
        exception_msg = "Could not parse the string. Expecting a YAML/JSON format."

    if not isinstance(exception_cls, type) and not issubclass(
        exception_cls, S7EntityError
    ):
        raise ValueError("exception_cls should be a subclass of S7EntityError.")

    if not isinstance(exception_msg, str):
        raise ValueError("exception_msg should be a string.")

    try:
        return yaml.safe_load(source)
    except yaml.YAMLError as error:
        raise exception_cls(exception_msg) from error
