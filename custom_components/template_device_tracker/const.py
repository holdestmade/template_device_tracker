"""Constants for the Template Device Tracker integration."""
from __future__ import annotations

from typing import Final

from homeassistant.const import Platform

DOMAIN: Final = "template_device_tracker"

PLATFORMS: Final = [Platform.DEVICE_TRACKER]

# Configuration keys
CONF_STATE: Final = "state"
CONF_LATITUDE: Final = "latitude"
CONF_LONGITUDE: Final = "longitude"
CONF_BATTERY_LEVEL: Final = "battery_level"
CONF_GPS_ACCURACY: Final = "gps_accuracy"
CONF_ALTITUDE: Final = "altitude"
CONF_SPEED: Final = "speed"
CONF_COURSE: Final = "course"
CONF_SATELLITES: Final = "satellites"
CONF_PICTURE: Final = "picture"  # not present in homeassistant.const, defined locally
CONF_AVAILABILITY: Final = "availability"
CONF_ATTRIBUTES: Final = "attributes"
CONF_SOURCE_TYPE: Final = "source_type"
CONF_TRACKERS: Final = "trackers"
