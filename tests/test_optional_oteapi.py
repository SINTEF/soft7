"""Test `soft7` works without the `oteapi` extra installed."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from collections.abc import Generator
    from typing import Any


OTEAPI_EXTRA_PACKAGES = ("oteapi", "otelib")


def _is_reloaded_module(name: str) -> bool:
    """Whether a module should be (re)imported fresh while OTEAPI is "uninstalled"."""
    return any(
        name == package or name.startswith(f"{package}.")
        for package in ("s7", *OTEAPI_EXTRA_PACKAGES)
    )


@pytest.fixture
def _without_oteapi() -> Generator[None]:
    """Make the `oteapi` extra packages non-importable.

    All `s7` modules are removed from `sys.modules` so they are imported anew without
    access to the `oteapi` extra packages. The original modules are restored after the
    test.
    """
    saved_modules = {
        name: module
        for name, module in sys.modules.items()
        if _is_reloaded_module(name)
    }
    for name in saved_modules:
        del sys.modules[name]

    for package in OTEAPI_EXTRA_PACKAGES:
        # A `None` value in `sys.modules` makes an import raise ModuleNotFoundError.
        sys.modules[package] = None  # type: ignore[assignment]

    try:
        yield
    finally:
        for name in [name for name in sys.modules if _is_reloaded_module(name)]:
            del sys.modules[name]
        sys.modules.update(saved_modules)


@pytest.mark.usefixtures("_without_oteapi")
def test_entity_without_oteapi(soft_entity_init: dict[str, Any]) -> None:
    """Ensure SOFT7 entities can be created and instantiated without OTEAPI."""
    from s7 import SOFT7Entity
    from s7.factories import create_entity

    entity = SOFT7Entity(**soft_entity_init)
    entity_cls = create_entity(entity)

    instance = entity_cls(
        dimensions={"N": 2},
        properties={
            "atom": ["Si", "Ti"],
            "electrons": [14, 22],
            "mass": [28.0855, 47.867],
            "radius": [1.11, 1.47],
        },
    )
    assert instance.properties.electrons == [14, 22]

    assert not [
        name
        for name in sys.modules
        if name.startswith(
            (
                "s7.factories.datasource_factory",
                "s7.oteapi_plugin",
                "s7.pydantic_models.datasource",
                "s7.pydantic_models.oteapi",
            )
        )
    ]


@pytest.mark.usefixtures("_without_oteapi")
@pytest.mark.parametrize(
    "import_statement",
    [
        "from s7.factories import create_datasource",
        "import s7.factories.datasource_factory",
        "import s7.oteapi_plugin.soft7_function",
        "import s7.oteapi_plugin.yaml_parser",
        "import s7.pydantic_models.datasource",
        "import s7.pydantic_models.oteapi",
    ],
)
def test_oteapi_functionality_without_oteapi(import_statement: str) -> None:
    """Ensure a helpful error is raised when using OTEAPI functionality without
    OTEAPI."""
    from s7.exceptions import MissingExtra

    with pytest.raises(MissingExtra, match=r"pip install 'soft7\[oteapi\]'") as exc:
        exec(import_statement)  # noqa: S102

    assert exc.value.extra == "oteapi"
    assert isinstance(exc.value, ImportError)


def test_lazy_create_datasource() -> None:
    """Ensure `create_datasource()` can be imported from `s7.factories` with OTEAPI."""
    pytest.importorskip("otelib", reason="Requires the 'oteapi' extra.")

    from s7.factories import create_datasource
    from s7.factories.datasource_factory import (
        create_datasource as original_create_datasource,
    )

    assert create_datasource is original_create_datasource


def test_unknown_factories_attribute() -> None:
    """Ensure the lazy loading in `s7.factories` does not hide unknown attributes."""
    import s7.factories

    with pytest.raises(AttributeError, match="has no attribute 'non_existent'"):
        s7.factories.non_existent
