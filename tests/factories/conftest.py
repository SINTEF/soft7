"""Pytest fixtures for 'factoris'."""
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Iterable
    from importlib.metadata import EntryPoint
    from typing import Any, Union, Protocol

    class MockEntryPoints(Protocol):
        """Mock `importlib.metadata.entry_points()`.

        Parameters:
            entry_points: Either an iterable of `importlib.metadata.EntryPoint`s or of
                dictionaries with which `importlib.metadata.EntryPoint`s can be
                initiated.
                These need to include the keys: `name`, `value`, and `group`.
                Regex for EntryPoints:

                ```ini
                group =
                  name = value
                ```

        """

        def __call__(
            self, entry_points: Iterable[Union[EntryPoint, dict[str, Any]]]
        ) -> None:
            ...

    class CreateEntryPoints(Protocol):
        """Create EntryPoint.

        Parameters:
            entry_point: A two line string representing an entry point in a `setup.cfg`
                file.

        Returns:
            A tuple of `importlib.metadata.EntryPoint`s from the information given in
            `entry_point`.

        """

        def __call__(self, entry_point: str) -> tuple[EntryPoint, ...]:
            ...


### Fixtures from oteapi-core - should be made available through pytest plugin instead


@pytest.fixture(autouse=True)
def add_mock_strategies_to_path() -> None:
    """Add test strategies to global PATH."""
    import sys
    from pathlib import Path

    tests_folder = Path(__file__).resolve().parent.parent.resolve()
    assert tests_folder.exists() and tests_folder.is_dir()

    assert (tests_folder / "static" / "datasource_oteapi_resource_strategy.py").exists()

    sys.path.append(str(tests_folder))


@pytest.fixture
def mock_importlib_entry_points(monkeypatch: pytest.MonkeyPatch) -> "MockEntryPoints":
    """Mock `importlib.metadata.entry_points()` to return a specific set of entry
    points.

    Important:
        This fixture should be called prior to importing anything from `oteapi`!

    """
    from importlib.metadata import EntryPoint

    from oteapi.plugins import entry_points as oteapi_entry_points

    def _mock_entry_points(
        entry_points: "Iterable[Union[EntryPoint, dict[str, Any]]]",
    ) -> None:
        """Mock `importlib.metadata.entry_points()`.

        Parameters:
            entry_points: Either an iterable of `importlib.metadata.EntryPoint`s or of
                dictionaries with which `importlib.metadata.EntryPoint`s can be
                initiated.
                These need to include the keys: `name`, `value`, and `group`.
                Regex for EntryPoints:

                ```ini
                group =
                  name = value
                ```

        """
        load_entry_points: "dict[str, list[EntryPoint]]" = {}
        for entry_point in entry_points:
            if isinstance(entry_point, dict):
                if not all(
                    necessary_key in entry_point
                    for necessary_key in ("name", "value", "group")
                ):
                    raise ValueError(
                        "The entry_point dicts must include the keys 'name', 'value', "
                        f"and 'group'. Checked entry_point dict: {entry_point}"
                    )
                entry_point = EntryPoint(**entry_point)
            elif not isinstance(entry_point, EntryPoint):
                raise TypeError(
                    "entry_points must be either an iterable of "
                    "`importlib.metadata.EntryPoint`s or dicts. "
                    f"Got an entry point of type {type(entry_point)}."
                )

            if load_entry_points.get(entry_point.group, []):
                load_entry_points[entry_point.group].append(entry_point)
            else:
                load_entry_points[entry_point.group] = [entry_point]

        monkeypatch.setattr(
            oteapi_entry_points,
            "get_entry_points",
            lambda: {key: tuple(value) for key, value in load_entry_points.items()},
        )

    return _mock_entry_points


@pytest.fixture
def create_importlib_entry_points() -> "CreateEntryPoints":
    """Generate `importlib.metadata.EntryPoint`s from a parsed `setup.cfg` file's
    `[options.entry_points]` group.

    Example:
        The provided `entry_points` could look like:

        ```ini
        oteapi.parse =
          oteapi.image/jpeg = oteapi.strategies.parse.image:ImageDataParseStrategy
          my_oteapi_test_package.test = my_test:MyTestStrategy
        oteapi.transformation =
          oteapi.celery/remote = oteapi.strategies.transformation.celery_remote:CeleryRemoteStrategy
        ```

    """  # noqa: E501
    import re
    from importlib.metadata import EntryPoint

    def _create_entry_points(entry_points: str) -> "tuple[EntryPoint, ...]":
        """Create EntryPoint.

        Parameters:
            entry_point: A two line string representing an entry point in a `setup.cfg`
                file.

        Returns:
            A tuple of `importlib.metadata.EntryPoint`s from the information given in
            `entry_point`.

        """
        entry_point_lines = entry_points.splitlines()
        if len(entry_point_lines) <= 1:
            raise ValueError(
                "Two lines or more were expected from `entry_points` "
                "(group + entry point)."
            )

        parsed_entry_points: "dict[str, list[str]]" = {}
        current_group = ""

        for line in entry_point_lines:
            if not line:
                # Empty line
                continue
            match = re.match(r"^(?P<group>\S+)\s*=$", line.strip())
            if match is None:
                match = re.match(r"^(?P<name>\S+)\s*=\s*(?P<value>\S+)$", line.strip())
                if match is None:
                    raise ValueError(
                        "Could not determine whether line defines a group or an entry "
                        f"point-entry: {line!r}"
                    )
                # Entry point-entry line
                if not current_group:
                    raise RuntimeError(
                        "`current_group` is not set. This shouldn't happen! "
                        f"Current line: {line!r}"
                    )
                parsed_entry_points[current_group].append(
                    {"name": match.group("name"), "value": match.group("value")}
                )
            else:
                # Group line
                current_group = match.group("group")
                if current_group in parsed_entry_points:
                    raise ValueError(
                        f"Duplicate groups - the group {match.group('group')!r} has "
                        "already been parsed once. Only supply a group once for the "
                        "input."
                    )
                parsed_entry_points[current_group] = []

        res: "list[EntryPoint]" = []
        for group, entries in parsed_entry_points.items():
            res.extend(
                EntryPoint(name=entry["name"], value=entry["value"], group=group)
                for entry in entries
            )
        return tuple(res)

    return _create_entry_points


@pytest.fixture
def load_test_strategies(
    create_importlib_entry_points: "CreateEntryPoints",
    mock_importlib_entry_points: "MockEntryPoints",
) -> None:
    """Load strategies under `tests/static/`."""
    setup_cfg = """\
oteapi.resource =
  soft_tests.example = static.datasource_oteapi_resource_strategy:ResourceTestStrategy
"""
    entry_points = create_importlib_entry_points(setup_cfg)
    mock_importlib_entry_points(entry_points)

    from oteapi.plugins.factories import load_strategies

    load_strategies()


### Local fixtures


@pytest.fixture
def generic_resource_config() -> "dict[str, Union[str, dict]]":
    """A generic resource config.

    Use the accessService `example` as defined in the `load_test_strategies` fixture.
    """
    from oteapi import __version__ as oteapi_version
    from oteapi.models import ResourceConfig

    resource_config = {
        "accessService": "example",
        "accessUrl": "https://example.org",
    }

    assert ResourceConfig(**resource_config), (
        "Generic resource config defined for tests is invalid (using oteapi-core "
        f"version {oteapi_version})."
    )

    return resource_config
