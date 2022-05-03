"""Customized OTEAPI pydantic models."""
from oteapi.models import ResourceConfig


class HashableResourceConfig(ResourceConfig):
    """ResourceConfig, but hashable."""

    def __hash__(self) -> int:
        return hash(
            tuple(
                (field_name, field_value)
                if isinstance(field_value, (str, bytes, tuple, frozenset, int, float)) or field_value is None
                else (field_name, None)
                for field_name, field_value in self.__dict__.items()
            )
        )
