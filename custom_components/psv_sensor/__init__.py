"""Integrazione PSV Sensor per Home Assistant."""
from __future__ import annotations
import logging
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import Platform
from homeassistant.core import HomeAssistant
from .const import CONF_SCAN_HOUR, DEFAULT_SCAN_HOUR, DOMAIN
from .coordinator import PsvDataCoordinator

_LOGGER = logging.getLogger(__name__)
PLATFORMS = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    hass.data.setdefault(DOMAIN, {})
    scan_hour = entry.options.get(CONF_SCAN_HOUR, entry.data.get(CONF_SCAN_HOUR, DEFAULT_SCAN_HOUR))
    coordinator = PsvDataCoordinator(hass, scan_hour=scan_hour)
    hass.data[DOMAIN][entry.entry_id] = coordinator
    await coordinator.async_config_entry_first_refresh()
    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    return unload_ok

async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    await hass.config_entries.async_reload(entry.entry_id)
