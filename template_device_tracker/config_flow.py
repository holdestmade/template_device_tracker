"""Config flow for the Template Device Tracker integration."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any

import voluptuous as vol

from homeassistant.const import CONF_ICON, CONF_NAME
from homeassistant.helpers import selector
from homeassistant.helpers.schema_config_entry_flow import (
    SchemaConfigFlowHandler,
    SchemaFlowFormStep,
)

from .const import (
    CONF_ALTITUDE,
    CONF_AVAILABILITY,
    CONF_BATTERY_LEVEL,
    CONF_COURSE,
    CONF_GPS_ACCURACY,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_PICTURE,
    CONF_SATELLITES,
    CONF_SOURCE_TYPE,
    CONF_SPEED,
    CONF_STATE,
    DOMAIN,
)
from .schema import VALID_SOURCE_TYPES

_TEMPLATE = selector.TemplateSelector()
_TEXT = selector.TextSelector()
_ICON = selector.IconSelector()
_SOURCE_TYPE = selector.SelectSelector(
    selector.SelectSelectorConfig(
        options=VALID_SOURCE_TYPES,
        mode=selector.SelectSelectorMode.DROPDOWN,
        translation_key="source_type",
    )
)


# A plain vol.Schema — SchemaFlowFormStep accepts either a Schema instance
# (handled synchronously) or an async callable returning one. We have no
# dynamic content, so the Schema goes in directly.
OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): _TEXT,
        vol.Optional(CONF_STATE): _TEMPLATE,
        vol.Optional(CONF_LATITUDE): _TEMPLATE,
        vol.Optional(CONF_LONGITUDE): _TEMPLATE,
        vol.Optional(CONF_GPS_ACCURACY): _TEMPLATE,
        vol.Optional(CONF_ALTITUDE): _TEMPLATE,
        vol.Optional(CONF_SPEED): _TEMPLATE,
        vol.Optional(CONF_COURSE): _TEMPLATE,
        vol.Optional(CONF_SATELLITES): _TEMPLATE,
        vol.Optional(CONF_BATTERY_LEVEL): _TEMPLATE,
        vol.Optional(CONF_PICTURE): _TEMPLATE,
        vol.Optional(CONF_ICON): _ICON,
        vol.Optional(CONF_AVAILABILITY): _TEMPLATE,
        vol.Optional(CONF_SOURCE_TYPE): _SOURCE_TYPE,
    }
)


CONFIG_FLOW: dict[str, SchemaFlowFormStep] = {
    "user": SchemaFlowFormStep(OPTIONS_SCHEMA),
}

OPTIONS_FLOW: dict[str, SchemaFlowFormStep] = {
    "init": SchemaFlowFormStep(OPTIONS_SCHEMA),
}


class TemplateDeviceTrackerConfigFlowHandler(
    SchemaConfigFlowHandler, domain=DOMAIN
):
    """Handle config & options flows for Template Device Tracker."""

    config_flow = CONFIG_FLOW
    options_flow = OPTIONS_FLOW

    def async_config_entry_title(self, options: Mapping[str, Any]) -> str:
        """Return the title of the resulting config entry."""
        return options[CONF_NAME]
