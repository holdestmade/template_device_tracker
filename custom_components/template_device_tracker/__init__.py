"""The Template Device Tracker integration.

Adds template-driven device_tracker entities to Home Assistant. Supports both
YAML configuration (under the `template_device_tracker:` domain key) and the
UI helper flow.
"""
from __future__ import annotations

import logging

import voluptuous as vol

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.discovery import async_load_platform
from homeassistant.helpers.typing import ConfigType

from .const import CONF_TRACKERS, DOMAIN, PLATFORMS
from .schema import DEVICE_TRACKER_SCHEMA

_LOGGER = logging.getLogger(__name__)


CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Optional(CONF_TRACKERS, default=[]): vol.All(
                    cv.ensure_list, [DEVICE_TRACKER_SCHEMA]
                ),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


async def async_setup(hass: HomeAssistant, config: ConfigType) -> bool:
    """Set up Template Device Tracker from YAML."""
    domain_config = config.get(DOMAIN)
    if not domain_config:
        return True

    trackers = domain_config.get(CONF_TRACKERS, [])
    if trackers:
        hass.async_create_task(
            async_load_platform(
                hass,
                Platform.DEVICE_TRACKER,
                DOMAIN,
                {CONF_TRACKERS: trackers},
                config,
            )
        )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a Template Device Tracker config entry."""
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a Template Device Tracker config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Reload the entry when options change."""
    await hass.config_entries.async_reload(entry.entry_id)
