"""Viessmann ViCare base entity."""
from homeassistant.helpers.entity import DeviceInfo, Entity

from ..const import DOMAIN


class ViCareEntity(Entity):
    """Representation of a ViCare base entity."""

    def __init__(self, name, api, device_config) -> None:
        """Initialize the base entity."""
        self._state = None
        self._name = name
        self._api = api
        self._device_config = device_config

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this entity."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_config.getConfig().serial)},
            name=self._device_config.getModel(),
            model=self._device_config.getModel(),
            manufacturer="Viessmann",
            configuration_url="https://developer.viessmann.com/",
        )
