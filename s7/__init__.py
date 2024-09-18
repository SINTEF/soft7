"""SOFT7"""

from __future__ import annotations

import logging

from .pydantic_models.soft7_entity import SOFT7Entity, SOFT7EntityPropertyType
from .pydantic_models.soft7_entity import parse_input_entity as get_entity

__version__ = "0.2.1"

__all__ = ("__version__", "SOFT7Entity", "SOFT7EntityPropertyType", "get_entity")

logging.getLogger("s7").setLevel(logging.DEBUG)
