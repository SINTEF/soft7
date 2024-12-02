"""SOFT7"""

from __future__ import annotations

import logging

from .pydantic_models.soft7_entity import SOFT7Entity, SOFT7EntityPropertyType
from .pydantic_models.soft7_entity import parse_input_entity as get_entity

__version__ = "0.3.0"

__all__ = ("SOFT7Entity", "SOFT7EntityPropertyType", "__version__", "get_entity")

logging.getLogger("s7").setLevel(logging.DEBUG)
