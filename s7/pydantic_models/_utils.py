"""Utility functions and more for the pydantic models."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, overload

import httpx
import yaml
from pydantic import AnyUrl, BaseModel, ValidationError

from s7.exceptions import EntityNotFound, S7EntityError

if TYPE_CHECKING:  # pragma: no cover
    import sys
    from typing import Any

    from s7.exceptions import S7EntityError

    if sys.version_info >= (3, 10):
        from typing import Literal
    else:
        from typing_extensions import Literal


def is_valid_url(url: str | AnyUrl) -> bool:
    """Check if the URL is valid."""
    try:
        url = AnyUrl(str(url))
    except ValidationError:
        return False

    return not any(getattr(url, url_part) is None for url_part in ["scheme", "host"])


@overload
def try_load_from_json_yaml(
    source: str,
    exception_cls: type[S7EntityError] | None = None,
    exception_msg: str | None = None,
    assert_dict: Literal[True] = True,
    assert_dict_exception_msg: str | None = None,
) -> dict[Any, Any]: ...


@overload
def try_load_from_json_yaml(
    source: str,
    exception_cls: type[S7EntityError] | None = None,
    exception_msg: str | None = None,
    assert_dict: Literal[False] = False,
    assert_dict_exception_msg: str | None = None,
) -> Any: ...


def try_load_from_json_yaml(
    source: str,
    exception_cls: type[S7EntityError] | None = None,
    exception_msg: str | None = None,
    assert_dict=False,
    assert_dict_exception_msg: str | None = None,
):
    """Try to load the source from a JSON/YAML string."""
    if exception_cls is None:
        exception_cls = S7EntityError

    if exception_msg is None:
        exception_msg = "Could not parse the string. Expecting a YAML/JSON format."

    if assert_dict_exception_msg is None:
        assert_dict_exception_msg = (
            f"Could not find a SOFT7 source JSON/YAML file at {source}."
        )

    if not isinstance(exception_cls, type) and not issubclass(
        exception_cls, S7EntityError
    ):
        raise ValueError("exception_cls should be a subclass of S7EntityError.")

    if not isinstance(exception_msg, str):
        raise ValueError("exception_msg should be a string.")

    if assert_dict and not isinstance(assert_dict_exception_msg, str):
        raise ValueError(
            "assert_dict_exception_msg should be a string when assert_dict is True."
        )

    # Using YAML parser, since _if_ the content is JSON, it's still valid
    # YAML as JSON is a subset of YAML.
    try:
        res = yaml.safe_load(source)
    except yaml.YAMLError as error:
        raise exception_cls(exception_msg) from error

    if assert_dict and not isinstance(res, dict):
        raise exception_cls(assert_dict_exception_msg)

    return res


@overload
def try_load_from_url(
    source: AnyUrl | str,
    exception_cls: type[S7EntityError] | None = None,
    exception_msg: str | None = None,
    assert_dict: Literal[True] = True,
    assert_dict_exception_msg: str | None = None,
) -> dict[Any, Any]: ...


@overload
def try_load_from_url(
    source: AnyUrl | str,
    exception_cls: type[S7EntityError] | None = None,
    exception_msg: str | None = None,
    assert_dict: Literal[False] = False,
    assert_dict_exception_msg: str | None = None,
) -> Any: ...


def try_load_from_url(
    source: AnyUrl | str,
    exception_cls: type[S7EntityError] | None = None,
    exception_msg: str | None = None,
    assert_dict=False,
    assert_dict_exception_msg: str | None = None,
) -> dict[Any, Any]:
    """Try to load the source from a URL."""
    if exception_cls is None:
        exception_cls = S7EntityError

    if exception_msg is None:
        exception_msg = f"Could not retrieve the dict online from {source}"

    if assert_dict_exception_msg is None:
        assert_dict_exception_msg = (
            f"Could not find a SOFT7 source JSON/YAML file at {source}."
        )

    if not isinstance(exception_cls, type) and not issubclass(
        exception_cls, S7EntityError
    ):
        raise ValueError("exception_cls should be a subclass of S7EntityError.")

    if not isinstance(exception_msg, str):
        raise ValueError("exception_msg should be a string.")

    if assert_dict and not isinstance(assert_dict_exception_msg, str):
        raise ValueError(
            "assert_dict_exception_msg should be a string when assert_dict is True."
        )

    with httpx.Client(follow_redirects=True, timeout=10) as client:
        try:
            response = client.get(
                str(source),
                headers={"Accept": "application/yaml, application/json"},
            ).raise_for_status()
        except (httpx.HTTPStatusError, httpx.HTTPError) as error:
            raise exception_cls(exception_msg) from error

    return try_load_from_json_yaml(
        response.text,
        exception_cls=exception_cls,
        exception_msg=None,
        assert_dict=assert_dict,
        assert_dict_exception_msg=assert_dict_exception_msg,
    )


def get_dict_from_url_path_or_raw(
    source: AnyUrl | Path | str | bytes | bytearray,
    *,
    exception_cls: type[S7EntityError] | None = None,
    parameter_name: str | None = None,
    concept_name: str | None = None,
) -> dict[Any, Any]:
    """Get a dictionary from a URL, path or a raw JSON/YAML string."""
    # Handle inputs
    if exception_cls is None:
        exception_cls = S7EntityError

    if parameter_name is None:
        parameter_name = "source"

    if concept_name is None:
        concept_name = "SOFT7 source"

    if not isinstance(exception_cls, type) and not issubclass(
        exception_cls, S7EntityError
    ):
        raise ValueError("exception_cls should be a subclass of S7EntityError.")

    if not isinstance(parameter_name, str) or not isinstance(concept_name, str):
        raise ValueError("parameter_name and concept_name should be strings.")

    # Handle source as bytes or bytearray (raw JSON/YAML string)
    if isinstance(source, (bytes, bytearray)):
        return try_load_from_json_yaml(
            source.decode(),
            exception_cls=exception_cls,
            exception_msg=(
                f"Could not parse the {parameter_name} as {concept_name} "
                "(expecting a JSON/YAML format)."
            ),
            assert_dict=True,
            assert_dict_exception_msg=(
                f"Could not find {concept_name} JSON/YAML file at {source.decode()}"
            ),
        )

    # Handle source as a Path
    if isinstance(source, Path):
        source = source.resolve()

        if not source.exists():
            raise exception_cls(
                f"Could not find {concept_name} JSON/YAML file at {source}"
            )

        return try_load_from_json_yaml(
            source.read_text(encoding="utf-8"),
            exception_cls=exception_cls,
            exception_msg=(
                f"Could not parse the {parameter_name} as {concept_name} "
                f"from {source} (expecting a JSON/YAML format)."
            ),
            assert_dict=True,
            assert_dict_exception_msg=(
                f"Could not find {concept_name} JSON/YAML file at {source}"
            ),
        )

    # Handle source as a URL
    if is_valid_url(source):
        return try_load_from_url(
            source,
            exception_cls=exception_cls,
            exception_msg=f"Could not retrieve {concept_name} online from {source}",
            assert_dict=True,
            assert_dict_exception_msg=(
                f"Could not find {concept_name} JSON/YAML file at {source}"
            ),
        )

    # From here on out, we expect source to be a string
    if not isinstance(source, str):
        raise TypeError(
            f"Expected {parameter_name} to be a str at this point, "
            f"instead got {type(source)}."
        )

    # Handle source as a str (path or a raw JSON/YAML-formatted string)
    # Check whether it's a path
    source_path = Path(source).resolve()

    if source_path.exists():
        return try_load_from_json_yaml(
            source_path.read_text(encoding="utf-8"),
            exception_cls=exception_cls,
            exception_msg=(
                f"Could not parse the {parameter_name} string as {concept_name} "
                f"from {source_path} (expecting a JSON/YAML format)."
            ),
            assert_dict=True,
            assert_dict_exception_msg=(
                f"Could not find {concept_name} JSON/YAML file at {source_path}"
            ),
        )

    # Otherwise, assume it's a parseable JSON/YAML string.
    return try_load_from_json_yaml(
        source,
        exception_cls=exception_cls,
        exception_msg=(
            f"Could not parse the {parameter_name} string as {concept_name} "
            f"(expecting a JSON/YAML format)."
        ),
        assert_dict=True,
        assert_dict_exception_msg=(
            f"Could not find {concept_name} JSON/YAML file at {source_path}"
        ),
    )


def get_dict_from_any_model_input(data: Any) -> dict[Any, Any]:
    """Get a dictionary from any model input.

    Parameters:
        data: The data to convert to a dictionary.

    Returns:
        The dictionary representation of the input data.

    """
    # If the data is already a dictionary, we return it as is.
    if isinstance(data, dict):
        return data

    if isinstance(data, BaseModel):
        # If we get an instance of a pydantic model, we dump it as minimalistically
        # as possible.
        return data.model_dump(exclude_defaults=True, exclude_unset=True)

    if not isinstance(data, (AnyUrl, str, Path, bytes, bytearray)):
        raise ValueError(
            f"Input data is not valid for model input. Type: {type(data)}."
        )

    return get_dict_from_url_path_or_raw(
        data,
        exception_cls=EntityNotFound,
        parameter_name="data",
        concept_name="SOFT7 entity data",
    )
