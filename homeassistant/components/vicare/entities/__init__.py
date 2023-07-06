from homeassistant.helpers.entity import DeviceInfo, Entity

from ..const import DOMAIN


class ViCareEntity(Entity):
    """Representation of a ViCare entity."""
    _attr_has_entity_name = True

    def __init__(
        self, name, api, device_config
    ) -> None:
        """Initialize the sensor."""
        self._attr_name = name
        self._api = api
        self._device_config = device_config
        self._state = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info for this device."""
        return DeviceInfo(
            identifiers={(DOMAIN, self._device_config.getConfig().serial)},
            name=self._device_config.getModel(),
            manufacturer="Viessmann",
            model=self._device_config.getModel(),
            configuration_url="https://developer.viessmann.com/",
        )

    @property
    def available(self):
        """Return True if entity is available."""
        return self._state is not None

    @property
    def unique_id(self) -> str:
        """Return unique ID for this device."""
        tmp_id = (
            f"{self._device_config.getConfig().serial}-{self.entity_description.key}"
        )
        if hasattr(self._api, "id"):
            return f"{tmp_id}-{self._api.id}"
        return tmp_id

    @property
    def native_value(self):
        """Return the state of the sensor."""
        return self._state
