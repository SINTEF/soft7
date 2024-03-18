"""A module to import certain factory-generated classes from."""

from __future__ import annotations


def register_class(cls: type) -> None:
    """Register a class with the module's globals.

    Parameters:
        cls: The class to register.

    """
    globals()[cls.__name__] = cls
