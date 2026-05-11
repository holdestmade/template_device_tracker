"""Template-driven device_tracker platform."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.device_tracker import SourceType
from homeassistant.components.device_tracker.config_entry import TrackerEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    CONF_ICON,
    CONF_NAME,
    CONF_UNIQUE_ID,
    STATE_HOME,
    STATE_NOT_HOME,
    STATE_UNAVAILABLE,
    STATE_UNKNOWN,
)
from homeassistant.core import Event, HomeAssistant, callback
from homeassistant.exceptions import TemplateError
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import (
    TrackTemplate,
    TrackTemplateResult,
    async_track_template_result,
)
from homeassistant.helpers.template import Template
from homeassistant.helpers.typing import ConfigType, DiscoveryInfoType

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
    CONF_TRACKERS,
)

_LOGGER = logging.getLogger(__name__)

# All keys in config that may carry a Template object.
_TEMPLATE_KEYS = (
    CONF_STATE,
    CONF_LATITUDE,
    CONF_LONGITUDE,
    CONF_GPS_ACCURACY,
    CONF_ALTITUDE,
    CONF_SPEED,
    CONF_COURSE,
    CONF_SATELLITES,
    CONF_BATTERY_LEVEL,
    CONF_PICTURE,
    CONF_ICON,
    CONF_AVAILABILITY,
)


async def async_setup_platform(
    hass: HomeAssistant,
    config: ConfigType,
    async_add_entities: AddEntitiesCallback,
    discovery_info: DiscoveryInfoType | None = None,
) -> None:
    """Set up template device trackers from YAML (via discovery)."""
    if discovery_info is None:
        return

    entities = [
        TemplateDeviceTracker(hass, conf) for conf in discovery_info[CONF_TRACKERS]
    ]
    async_add_entities(entities)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up a template device tracker from a config entry."""
    options = {**config_entry.options}
    options[CONF_UNIQUE_ID] = config_entry.entry_id

    # Options coming from the helper config flow are stored as plain strings;
    # promote them to Template objects so the entity can treat YAML and
    # config-flow paths identically.
    for key in _TEMPLATE_KEYS:
        value = options.get(key)
        if isinstance(value, str) and value:
            options[key] = Template(value, hass)
        elif value in ("", None):
            options.pop(key, None)

    raw_attributes = options.get(CONF_ATTRIBUTES) or {}
    options[CONF_ATTRIBUTES] = {
        key: Template(val, hass) if isinstance(val, str) else val
        for key, val in raw_attributes.items()
    }

    async_add_entities([TemplateDeviceTracker(hass, options)])


class TemplateDeviceTracker(TrackerEntity):
    """A device_tracker entity whose attributes are computed from templates."""

    _attr_should_poll = False
    _attr_has_entity_name = False

    def __init__(self, hass: HomeAssistant, config: dict[str, Any]) -> None:
        """Initialise the tracker from a validated config dict."""
        self.hass = hass

        self._attr_name = config[CONF_NAME]
        self._attr_unique_id = config.get(CONF_UNIQUE_ID)

        # Templates (any may be None if not configured).
        self._tpl_state: Template | None = config.get(CONF_STATE)
        self._tpl_latitude: Template | None = config.get(CONF_LATITUDE)
        self._tpl_longitude: Template | None = config.get(CONF_LONGITUDE)
        self._tpl_gps_accuracy: Template | None = config.get(CONF_GPS_ACCURACY)
        self._tpl_altitude: Template | None = config.get(CONF_ALTITUDE)
        self._tpl_speed: Template | None = config.get(CONF_SPEED)
        self._tpl_course: Template | None = config.get(CONF_COURSE)
        self._tpl_satellites: Template | None = config.get(CONF_SATELLITES)
        self._tpl_battery_level: Template | None = config.get(CONF_BATTERY_LEVEL)
        self._tpl_picture: Template | None = config.get(CONF_PICTURE)
        self._tpl_icon: Template | None = config.get(CONF_ICON)
        self._tpl_availability: Template | None = config.get(CONF_AVAILABILITY)
        self._tpl_attributes: dict[str, Template] = config.get(CONF_ATTRIBUTES, {})

        # Static configuration.
        self._configured_source_type: SourceType | None = None
        if (raw := config.get(CONF_SOURCE_TYPE)) is not None:
            self._configured_source_type = SourceType(raw)

        # Rendered values.
        self._state_value: str | None = None
        self._latitude_value: float | None = None
        self._longitude_value: float | None = None
        self._gps_accuracy_value: int = 0
        self._altitude_value: float | None = None
        self._speed_value: float | None = None
        self._course_value: float | None = None
        self._satellites_value: int | None = None
        self._battery_level_value: int | None = None
        self._available: bool = True
        self._extra_attrs: dict[str, Any] = {}

    # -- TrackerEntity properties -----------------------------------------

    @property
    def source_type(self) -> SourceType:
        """Return the configured source type or infer from coordinates."""
        if self._configured_source_type is not None:
            return self._configured_source_type
        if self._latitude_value is not None and self._longitude_value is not None:
            return SourceType.GPS
        return SourceType.ROUTER

    @property
    def latitude(self) -> float | None:
        """Return latitude, if known."""
        return self._latitude_value

    @property
    def longitude(self) -> float | None:
        """Return longitude, if known."""
        return self._longitude_value

    @property
    def location_name(self) -> str | None:
        """Return the state-derived location name (home, not_home, zone)."""
        return self._state_value

    @property
    def battery_level(self) -> int | None:
        """Return battery level percentage, if known."""
        return self._battery_level_value

    @property
    def location_accuracy(self) -> int:
        """Return the GPS accuracy in metres."""
        return self._gps_accuracy_value

    @property
    def available(self) -> bool:
        """Return availability."""
        return self._available

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return user-defined attributes plus GPS-flavoured extras."""
        attrs: dict[str, Any] = dict(self._extra_attrs)
        if self._altitude_value is not None:
            attrs["altitude"] = self._altitude_value
        if self._speed_value is not None:
            attrs["speed"] = self._speed_value
        if self._course_value is not None:
            attrs["course"] = self._course_value
        if self._satellites_value is not None:
            attrs["satellites"] = self._satellites_value
        return attrs

    # -- Lifecycle ---------------------------------------------------------

    async def async_added_to_hass(self) -> None:
        """Subscribe to template results when the entity is added."""
        await super().async_added_to_hass()

        track: list[TrackTemplate] = []
        for tpl in (
            self._tpl_state,
            self._tpl_latitude,
            self._tpl_longitude,
            self._tpl_gps_accuracy,
            self._tpl_altitude,
            self._tpl_speed,
            self._tpl_course,
            self._tpl_satellites,
            self._tpl_battery_level,
            self._tpl_picture,
            self._tpl_icon,
            self._tpl_availability,
        ):
            if tpl is not None:
                track.append(TrackTemplate(tpl, None))
        for tpl in self._tpl_attributes.values():
            track.append(TrackTemplate(tpl, None))

        if not track:
            return

        result_info = async_track_template_result(
            self.hass, track, self._handle_results
        )
        self.async_on_remove(result_info.async_remove)
        result_info.async_refresh()

    # -- Template handling -------------------------------------------------

    @callback
    def _handle_results(
        self,
        event: Event | None,
        updates: list[TrackTemplateResult],
    ) -> None:
        """Apply a batch of template results."""
        for upd in updates:
            tpl = upd.template
            result = upd.result
            if isinstance(result, TemplateError):
                _LOGGER.warning(
                    "Template error in %s for %s: %s",
                    self._template_label(tpl),
                    self.entity_id or self._attr_unique_id or self._attr_name,
                    result,
                )
                self._apply_error(tpl)
                continue
            self._apply_result(tpl, result)

        self.async_write_ha_state()

    def _template_label(self, tpl: Template) -> str:
        """Return a human-readable label for a template (logging only)."""
        for key, candidate in (
            (CONF_STATE, self._tpl_state),
            (CONF_LATITUDE, self._tpl_latitude),
            (CONF_LONGITUDE, self._tpl_longitude),
            (CONF_GPS_ACCURACY, self._tpl_gps_accuracy),
            (CONF_ALTITUDE, self._tpl_altitude),
            (CONF_SPEED, self._tpl_speed),
            (CONF_COURSE, self._tpl_course),
            (CONF_SATELLITES, self._tpl_satellites),
            (CONF_BATTERY_LEVEL, self._tpl_battery_level),
            (CONF_PICTURE, self._tpl_picture),
            (CONF_ICON, self._tpl_icon),
            (CONF_AVAILABILITY, self._tpl_availability),
        ):
            if tpl is candidate:
                return key
        for attr_key, candidate in self._tpl_attributes.items():
            if tpl is candidate:
                return f"attribute:{attr_key}"
        return "<unknown>"

    def _apply_error(self, tpl: Template) -> None:
        """Reset state on template error."""
        if tpl is self._tpl_availability:
            self._available = False
        # All other fields are best left at their last good value rather
        # than thrashing the entity state on transient errors.

    def _apply_result(self, tpl: Template, result: Any) -> None:
        """Route a successful template result to the right field."""
        if tpl is self._tpl_state:
            self._state_value = self._coerce_state(result)
        elif tpl is self._tpl_latitude:
            self._latitude_value = self._coerce_float(result, CONF_LATITUDE)
        elif tpl is self._tpl_longitude:
            self._longitude_value = self._coerce_float(result, CONF_LONGITUDE)
        elif tpl is self._tpl_gps_accuracy:
            value = self._coerce_int(result, CONF_GPS_ACCURACY)
            self._gps_accuracy_value = value if value is not None else 0
        elif tpl is self._tpl_altitude:
            self._altitude_value = self._coerce_float(result, CONF_ALTITUDE)
        elif tpl is self._tpl_speed:
            self._speed_value = self._coerce_float(result, CONF_SPEED)
        elif tpl is self._tpl_course:
            self._course_value = self._coerce_float(result, CONF_COURSE)
        elif tpl is self._tpl_satellites:
            self._satellites_value = self._coerce_int(result, CONF_SATELLITES)
        elif tpl is self._tpl_battery_level:
            self._battery_level_value = self._coerce_int(result, CONF_BATTERY_LEVEL)
        elif tpl is self._tpl_picture:
            self._attr_entity_picture = self._coerce_str(result)
        elif tpl is self._tpl_icon:
            self._attr_icon = self._coerce_str(result)
        elif tpl is self._tpl_availability:
            self._available = self._coerce_bool(result)
        else:
            for key, candidate in self._tpl_attributes.items():
                if tpl is candidate:
                    self._extra_attrs[key] = result
                    return

    # -- Coercion helpers --------------------------------------------------

    @staticmethod
    def _coerce_state(result: Any) -> str | None:
        """Normalise a state-template result into home/not_home or a zone name."""
        if result in (None, "", "None", STATE_UNKNOWN, STATE_UNAVAILABLE):
            return None
        if isinstance(result, bool):
            return STATE_HOME if result else STATE_NOT_HOME
        text = str(result).strip()
        lower = text.lower()
        if lower in ("true", "home", "1", STATE_HOME):
            return STATE_HOME
        if lower in ("false", "not_home", "away", "0", STATE_NOT_HOME):
            return STATE_NOT_HOME
        return text

    @staticmethod
    def _coerce_str(result: Any) -> str | None:
        """Normalise an optional string result, treating empty/None as missing."""
        if result in (None, "", "None", STATE_UNKNOWN, STATE_UNAVAILABLE):
            return None
        return str(result)

    @staticmethod
    def _coerce_float(result: Any, name: str) -> float | None:
        """Coerce a result to float, returning None and logging on failure."""
        if result in (None, "", "None", STATE_UNKNOWN, STATE_UNAVAILABLE):
            return None
        try:
            return float(result)
        except (ValueError, TypeError):
            _LOGGER.warning("Invalid %s template result: %r", name, result)
            return None

    @staticmethod
    def _coerce_int(result: Any, name: str) -> int | None:
        """Coerce a result to int (via float for '95.0' style inputs)."""
        if result in (None, "", "None", STATE_UNKNOWN, STATE_UNAVAILABLE):
            return None
        try:
            return int(float(result))
        except (ValueError, TypeError):
            _LOGGER.warning("Invalid %s template result: %r", name, result)
            return None

    @staticmethod
    def _coerce_bool(result: Any) -> bool:
        """Coerce a result to bool using HA-typical truthy strings."""
        if isinstance(result, bool):
            return result
        if result is None:
            return False
        return str(result).strip().lower() in (
            "true",
            "1",
            "yes",
            "on",
            "available",
            STATE_HOME,
        )
