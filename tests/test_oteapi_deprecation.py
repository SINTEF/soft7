"""Test the deprecation of all OTEAPI-related functionality.

See https://github.com/SINTEF/soft7/issues/222.
"""

from __future__ import annotations

import importlib
import sys
import warnings
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Callable, Generator
    from typing import Any


DEPRECATED_EXCEPTIONS = (
    "ConfigsNotFound",
    "InsufficientData",
    "InvalidMapping",
    "S7OTEAPIPluginError",
    "SOFT7FunctionError",
)

ISSUE_URL = "https://github.com/SINTEF/soft7/issues/222"


@pytest.fixture
def fresh_s7() -> Generator[Callable[[], type[Warning]]]:
    """Unload all `s7` modules, so they are imported anew in the test.

    The original modules are restored afterwards.

    Since `s7.exceptions` is imported anew as well, the returned function must be used
    to retrieve the matching `OTEAPIDeprecationWarning` class.
    """

    def _is_s7(name: str) -> bool:
        return name == "s7" or name.startswith("s7.")

    saved_modules = {
        name: module for name, module in sys.modules.items() if _is_s7(name)
    }
    for name in saved_modules:
        del sys.modules[name]

    def _warning_category() -> type[Warning]:
        from s7.exceptions import OTEAPIDeprecationWarning

        return OTEAPIDeprecationWarning

    try:
        yield _warning_category
    finally:
        for name in [name for name in sys.modules if _is_s7(name)]:
            del sys.modules[name]
        sys.modules.update(saved_modules)


def _oteapi_warnings(
    records: list[warnings.WarningMessage], category: type[Warning]
) -> list[warnings.WarningMessage]:
    """Return only the recorded OTEAPI deprecation warnings."""
    return [record for record in records if issubclass(record.category, category)]


@pytest.mark.parametrize(
    "module",
    ["s7.oteapi_plugin", "s7.pydantic_models.oteapi", "s7.pydantic_models.datasource"],
)
def test_deprecated_module_import(
    module: str, fresh_s7: Callable[[], type[Warning]]
) -> None:
    """Ensure importing a deprecated module emits a single deprecation warning,
    attributed to the importing code."""
    pytest.importorskip("oteapi", reason="Requires the 'oteapi' extra.")
    category = fresh_s7()

    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        importlib.import_module(module)

    oteapi_warnings = _oteapi_warnings(records, category)
    assert len(oteapi_warnings) == 1, [str(record.message) for record in records]
    assert f"{module!r} module is deprecated" in str(oteapi_warnings[0].message)
    assert ISSUE_URL in str(oteapi_warnings[0].message)


@pytest.mark.parametrize(
    "module", ["s7.oteapi_plugin.soft7_function", "s7.oteapi_plugin.yaml_parser"]
)
def test_oteapi_plugin_strategy_import(
    module: str, fresh_s7: Callable[[], type[Warning]]
) -> None:
    """Ensure importing an OTEAPI plugin strategy, e.g., through the `oteapi.*` entry
    points, emits only the `s7.oteapi_plugin` deprecation warning, and no cascade of
    warnings from the deprecated modules it imports internally."""
    pytest.importorskip("oteapi", reason="Requires the 'oteapi' extra.")
    category = fresh_s7()

    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        importlib.import_module(module)

    oteapi_warnings = _oteapi_warnings(records, category)
    assert len(oteapi_warnings) == 1, [str(record.message) for record in records]
    assert "'s7.oteapi_plugin' module is deprecated" in str(oteapi_warnings[0].message)


def test_import_warning_attributed_to_importer(
    fresh_s7: Callable[[], type[Warning]],
) -> None:
    """Ensure the import deprecation warning points to the line importing the
    deprecated module."""
    pytest.importorskip("oteapi", reason="Requires the 'oteapi' extra.")
    category = fresh_s7()

    with pytest.warns(category) as records:
        import s7.pydantic_models.oteapi  # noqa: F401

    assert records[0].filename == __file__


def test_dynamic_import_warning_attributed_to_caller(
    fresh_s7: Callable[[], type[Warning]],
) -> None:
    """Ensure the import deprecation warning points to the code calling
    `importlib.import_module()` or loading an entry point, not into `importlib`."""
    import inspect
    from importlib.metadata import entry_points

    pytest.importorskip("oteapi", reason="Requires the 'oteapi' extra.")
    category = fresh_s7()

    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        lineno = inspect.currentframe().f_lineno + 1  # type: ignore[union-attr]
        importlib.import_module("s7.pydantic_models.oteapi")

    [record] = _oteapi_warnings(records, category)
    assert (record.filename, record.lineno) == (__file__, lineno)

    # Entry points registered for OTEAPI Core (see pyproject.toml)
    [entry_point] = [
        entry_point
        for entry_point in entry_points(group="oteapi.function")
        if entry_point.name == "soft7.soft7"
    ]

    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        lineno = inspect.currentframe().f_lineno + 1  # type: ignore[union-attr]
        entry_point.load()

    [record] = _oteapi_warnings(records, category)
    assert "'s7.oteapi_plugin' module" in str(record.message)
    assert (record.filename, record.lineno) == (__file__, lineno)


@pytest.mark.parametrize("importer", ["s7.graphtools.utils", "s7", "s7_extension"])
def test_import_from_s7_namespace_extension(
    importer: str, fresh_s7: Callable[[], type[Warning]]
) -> None:
    """Ensure modules extending the `s7` namespace, e.g., `s7.graphtools` from SOFT7
    GraphTools, are warned when importing a deprecated module.

    Only SOFT7's own OTEAPI-related modules are considered internal importers.
    """
    pytest.importorskip("oteapi", reason="Requires the 'oteapi' extra.")
    category = fresh_s7()

    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        exec("import s7.pydantic_models.oteapi", {"__name__": importer})  # noqa: S102

    assert len(_oteapi_warnings(records, category)) == 1


def test_datasource_factory_import_is_silent(
    fresh_s7: Callable[[], type[Warning]],
) -> None:
    """Ensure importing `create_datasource()` does not warn, only calling it does."""
    pytest.importorskip("otelib", reason="Requires the 'oteapi' extra.")
    category = fresh_s7()

    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        from s7.factories import create_datasource  # noqa: F401
        from s7.factories.datasource_factory import CACHE  # noqa: F401

    assert not _oteapi_warnings(records, category)


# The `soft_datasource_configs` fixture imports `s7.pydantic_models.oteapi`
@pytest.mark.filterwarnings("ignore::s7.exceptions.OTEAPIDeprecationWarning")
def test_create_datasource(
    soft_entity_init: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
    request: pytest.FixtureRequest,
) -> None:
    """Ensure calling `create_datasource()` emits a single deprecation warning,
    attributed to the caller, and still works."""
    pytest.importorskip("otelib", reason="Requires the 'oteapi' extra.")

    # Only request the fixture now, since it requires the `oteapi` extra.
    soft_datasource_configs: dict[str, dict[str, Any]] = request.getfixturevalue(
        "soft_datasource_configs"
    )

    from s7.exceptions import OTEAPIDeprecationWarning
    from s7.factories import create_datasource
    from s7.pydantic_models.datasource import SOFT7DataSource

    # Avoid setting up an OTEAPI pipeline, which requires an OTEAPI service.
    # Dimensions are resolved upon creation, i.e., they must return an integer.
    def _get_data(*_: Any, **__: Any) -> Callable[..., int]:
        return lambda soft7_property: 2  # noqa: ARG005

    monkeypatch.setattr("s7.factories.datasource_factory._get_data", _get_data)

    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        datasource = create_datasource(
            entity=soft_entity_init, configs=soft_datasource_configs
        )

    assert isinstance(datasource, SOFT7DataSource)

    oteapi_warnings = _oteapi_warnings(records, OTEAPIDeprecationWarning)
    assert len(oteapi_warnings) == 1, [str(record.message) for record in records]
    assert "`s7.factories.create_datasource()` is deprecated" in str(
        oteapi_warnings[0].message
    )
    assert oteapi_warnings[0].filename == __file__


@pytest.mark.parametrize("name", DEPRECATED_EXCEPTIONS)
def test_deprecated_exceptions(name: str) -> None:
    """Ensure the OTEAPI-related exceptions are deprecated, but otherwise unchanged."""
    import s7._oteapi_exceptions
    import s7.exceptions
    from s7.exceptions import OTEAPIDeprecationWarning

    with pytest.warns(
        OTEAPIDeprecationWarning, match=rf"`s7\.exceptions\.{name}` is deprecated"
    ) as records:
        exception = getattr(s7.exceptions, name)

    assert records[0].filename == __file__
    assert exception is getattr(s7._oteapi_exceptions, name)
    assert issubclass(exception, s7.exceptions.S7Error)


def test_deprecated_exceptions_from_import() -> None:
    """Ensure importing a deprecated exception warns and keeps its class hierarchy."""
    import pickle

    from s7.exceptions import OTEAPIDeprecationWarning, S7EntityError, S7Error

    with pytest.warns(OTEAPIDeprecationWarning) as records:
        from s7.exceptions import (
            ConfigsNotFound,
            InsufficientData,
            InvalidMapping,
            S7OTEAPIPluginError,
            SOFT7FunctionError,
        )

    assert len(records) == len(DEPRECATED_EXCEPTIONS)
    assert {record.filename for record in records} == {__file__}

    assert issubclass(ConfigsNotFound, S7EntityError)
    assert issubclass(ConfigsNotFound, FileNotFoundError)
    assert issubclass(S7OTEAPIPluginError, S7Error)
    assert issubclass(SOFT7FunctionError, S7OTEAPIPluginError)
    for exception in (InsufficientData, InvalidMapping):
        assert issubclass(exception, SOFT7FunctionError)
        assert issubclass(exception, ValueError)

    # Raising and catching does not emit (further) warnings
    with pytest.raises(SOFT7FunctionError, match="Invalid mapping"):
        raise InvalidMapping("Invalid mapping")

    # The classes are still presented as part of `s7.exceptions`
    assert repr(InvalidMapping) == "<class 's7.exceptions.InvalidMapping'>"

    # Pickling looks up the class through `s7.exceptions`, i.e., it warns
    error = InvalidMapping("Invalid mapping")
    with pytest.warns(OTEAPIDeprecationWarning):
        pickled = pickle.dumps(error)
    with pytest.warns(OTEAPIDeprecationWarning):
        restored = pickle.loads(pickled)

    assert isinstance(restored, InvalidMapping)
    assert str(restored) == str(error)

    # Previous versions of SOFT7 can unpickle it
    assert b"s7.exceptions" in pickled
    assert b"_oteapi_exceptions" not in pickled


def test_unpickle_deprecated_exception_from_previous_version() -> None:
    """Ensure deprecated exceptions pickled by a previous SOFT7 version can be
    unpickled."""
    import pickle

    from s7._oteapi_exceptions import InvalidMapping
    from s7.exceptions import OTEAPIDeprecationWarning

    # `pickle.dumps(InvalidMapping("Invalid mapping"), protocol=4)` with SOFT7 v0.6.0
    pickled = (
        b"\x80\x04\x95:\x00\x00\x00\x00\x00\x00\x00\x8c\rs7.exceptions\x94\x8c"
        b"\x0eInvalidMapping\x94\x93\x94\x8c\x0fInvalid mapping\x94\x85\x94R\x94."
    )

    with pytest.warns(OTEAPIDeprecationWarning):
        restored = pickle.loads(pickled)

    assert type(restored) is InvalidMapping
    assert str(restored) == "Invalid mapping"


def test_exceptions_star_import() -> None:
    """Ensure `from s7.exceptions import *` exports the public, non-deprecated names
    only, without emitting deprecation warnings."""
    import s7.exceptions

    namespace: dict[str, Any] = {}
    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")
        exec("from s7.exceptions import *", namespace)  # noqa: S102

    assert not _oteapi_warnings(records, s7.exceptions.OTEAPIDeprecationWarning)

    namespace.pop("__builtins__")
    assert set(namespace) == {
        "EntityNotFound",
        "MissingExtra",
        "OTEAPIDeprecationWarning",
        "S7EntityError",
        "S7Error",
        "raise_if_extra_missing",
    }
    assert not set(namespace) & set(DEPRECATED_EXCEPTIONS)


def test_unknown_exceptions_attribute() -> None:
    """Ensure `s7.exceptions.__getattr__()` does not hide unknown attributes."""
    import s7.exceptions

    with pytest.raises(AttributeError, match="has no attribute 'non_existent'"):
        s7.exceptions.non_existent


def test_no_deprecation_warnings_for_core_usage(
    soft_entity_init: dict[str, Any], fresh_s7: Callable[[], type[Warning]]
) -> None:
    """Ensure using SOFT7 without OTEAPI emits no OTEAPI deprecation warnings.

    This covers the top-level `s7` API, the non-deprecated exceptions, and
    creating entities and entity instances.
    """
    with warnings.catch_warnings(record=True) as records:
        warnings.simplefilter("always")

        import s7
        import s7.factories
        from s7 import SOFT7Entity, SOFT7EntityPropertyType, get_entity  # noqa: F401
        from s7.exceptions import (  # noqa: F401
            EntityNotFound,
            MissingExtra,
            S7EntityError,
            S7Error,
            raise_if_extra_missing,
        )
        from s7.factories import create_entity

        entity = get_entity(soft_entity_init)
        assert isinstance(entity, SOFT7Entity)

        instance = create_entity(entity)(
            dimensions={"N": 2},
            properties={
                "atom": ["Si", "Ti"],
                "electrons": [14, 22],
                "mass": [28.0855, 47.867],
                "radius": [1.11, 1.47],
            },
        )
        assert instance.properties.electrons == [14, 22]

        assert "create_entity" in dir(s7.factories)

    assert not _oteapi_warnings(records, fresh_s7())
