"""The SOFT7 OTEAPI Function strategy.

It expects mappings to be present in the session, and will use them to transform
the parsed data source into a SOFT7 Entity instance.
"""
from __future__ import annotations

import logging
from typing import Annotated, Any

from oteapi.models import SessionUpdate
from oteapi.strategies.mapping.mapping import MappingSessionUpdate
from pydantic import BaseModel, Field, ValidationError

from s7.exceptions import InvalidOrMissingSession
from s7.oteapi_plugin.models import SOFT7FunctionConfig

LOGGER = logging.getLogger(__name__)


class SOFT7Generator(BaseModel):
    """SOFT7 Generator function strategy for OTEAPI."""

    function_config: Annotated[
        SOFT7FunctionConfig, Field(description=SOFT7FunctionConfig.__doc__)
    ]

    def initialize(self, _: dict[str, Any] | None) -> SessionUpdate:
        """Initialize the SOFT7 Generator function strategy."""
        return SessionUpdate()

    def get(self, session: dict[str, Any] | None) -> SessionUpdate:
        """Execute the SOFT7 Generator function strategy."""
        if session is None:
            raise InvalidOrMissingSession("Session is missing.")

        # TODO: Update this to be more flexible and "knowledge agnostic" - with this, I
        # mean, I only knew "content" would be in the session for the core JSON and CSV
        # parsers. There should be a "generic" or data model-strict way to get the
        # parsed data - and most likely not from the session.
        if "content" in session:
            parsed_data: dict = session["content"]
        else:
            raise NotImplementedError(
                "For now, the SOFT7 Generator function strategy only supports data "
                "parsed into the 'content' key of the session."
            )

        # Expect the mapping strategy "triples" to have run already.
        try:
            mapping_session = MappingSessionUpdate(**session)
        except ValidationError as exc:
            error_message = "Session is missing required keys."
            LOGGER.error("%s\nsession: %r\nerror: %s", error_message, session, exc)
            raise InvalidOrMissingSession(error_message) from exc

        return SessionUpdate()
