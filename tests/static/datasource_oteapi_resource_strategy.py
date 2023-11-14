"""Resource test strategy class."""
from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import yaml
from oteapi.models import ResourceConfig, SessionUpdate
from pydantic.dataclasses import dataclass

if TYPE_CHECKING:
    from typing import Any


@dataclass
class ResourceTestStrategy:
    """Test resource strategy.

    Is currently used by `tests.factories.conftest:load_test_strategies()` fixture,
    where it is registered as: `accessService=example`.
    """

    resource_config: ResourceConfig

    def initialize(self, session: dict[str, Any] | None = None) -> SessionUpdate:
        """Initialize."""
        return SessionUpdate()

    def get(self, session: dict[str, Any] | None = None) -> SessionUpdate:
        """Run resource strategy."""
        test_data_path = (
            Path(__file__).resolve().parent / "soft_datasource_content.yaml"
        )
        test_data = yaml.safe_load(test_data_path.read_text(encoding="utf-8"))
        return SessionUpdate(**test_data)
