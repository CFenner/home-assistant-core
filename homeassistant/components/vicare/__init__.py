"""The ViCare integration."""
from __future__ import annotations

from contextlib import suppress
import logging
import os

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import STORAGE_DIR

from .const import (
    CONF_HEATING_TYPE,
    DOMAIN,
    HEATING_TYPE_TO_CREATOR_METHOD,
    PLATFORMS,
    VICARE_API,
    VICARE_DEVICE_CONFIG,
    VICARE_DEVICE_CONFIG_LIST,
    VICARE_TOKEN_FILENAME,
    HeatingType,
)
from .utils import login

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up from config entry."""
    _LOGGER.debug("Setting up ViCare component")

    hass.data[DOMAIN] = {}
    hass.data[DOMAIN][entry.entry_id] = {}

    await hass.async_add_executor_job(setup_vicare_api, hass, entry)

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True


def setup_vicare_api(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Set up PyVicare API."""
    vicare_api = login(hass, entry.data)

    for device in vicare_api.devices:
        _LOGGER.info(
            "Found device: %s (online: %s)", device.getModel(), str(device.isOnline())
        )

    # Currently we only support a single device
    device_list = vicare_api.devices
    device = device_list[0]
    hass.data[DOMAIN][entry.entry_id][VICARE_DEVICE_CONFIG_LIST] = device_list
    hass.data[DOMAIN][entry.entry_id][VICARE_DEVICE_CONFIG] = device
    hass.data[DOMAIN][entry.entry_id][VICARE_API] = getattr(
        device,
        HEATING_TYPE_TO_CREATOR_METHOD[HeatingType(entry.data[CONF_HEATING_TYPE])],
    )()


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload ViCare config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)

    with suppress(FileNotFoundError):
        await hass.async_add_executor_job(
            os.remove, hass.config.path(STORAGE_DIR, VICARE_TOKEN_FILENAME)
        )

    return unload_ok
