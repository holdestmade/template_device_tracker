"""Shared schema definitions for the Template Device Tracker integration.

Kept deliberately lightweight: this module is imported by both __init__.py
(for YAML validation) and config_flow.py (which is loaded lazily inside the
event loop). Importing heavy integration modules at the top of this file
would trigger a blocking-import warning when the config flow is opened, so
the SourceType values are hardcoded as plain strings here and the enum is
only imported by device_tracker.py at runtime.
"""
from __future__ import annotations

import voluptuous as vol

from homeassistant.const import CONF_ICON, CONF_NAME, CONF_UNIQUE_ID
from homeassistant.helpers import config_validation as cv

from .const import (
    CONF_ALTITUDE,
    CONF_ATTRIBUTES,
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
)

# Mirrors homeassistant.components.device_tracker.SourceType but kept as
# plain strings so this module stays free of integration-level imports.
VALID_SOURCE_TYPES: list[str] = ["gps", "router", "bluetooth", "bluetooth_le"]


DEVICE_TRACKER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_NAME): cv.string,
        vol.Optional(CONF_UNIQUE_ID): cv.string,
        vol.Optional(CONF_STATE): cv.template,
        vol.Optional(CONF_LATITUDE): cv.template,
        vol.Optional(CONF_LONGITUDE): cv.template,
        vol.Optional(CONF_GPS_ACCURACY): cv.template,
        vol.Optional(CONF_ALTITUDE): cv.template,
        vol.Optional(CONF_SPEED): cv.template,
        vol.Optional(CONF_COURSE): cv.template,
        vol.Optional(CONF_SATELLITES): cv.template,
        vol.Optional(CONF_BATTERY_LEVEL): cv.template,
        vol.Optional(CONF_PICTURE): cv.template,
        vol.Optional(CONF_ICON): cv.template,
        vol.Optional(CONF_AVAILABILITY): cv.template,
        vol.Optional(CONF_SOURCE_TYPE): vol.In(VALID_SOURCE_TYPES),
        vol.Optional(CONF_ATTRIBUTES, default={}): vol.Schema(
            {cv.string: cv.template}
        ),
    }
)
