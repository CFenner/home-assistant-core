"""Viessmann ViCare button device."""
from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
import logging

from PyViCare.PyViCareDevice import Device as PyViCareDevice
from PyViCare.PyViCareDeviceConfig import PyViCareDeviceConfig
from PyViCare.PyViCareUtils import (
    PyViCareInvalidDataError,
    PyViCareNotSupportedFeatureError,
    PyViCareRateLimitError,
)
import requests

from homeassistant.components.button import ButtonEntity, ButtonEntityDescription
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import ViCareRequiredKeysMixinWithSet
from .const import DOMAIN, VICARE_DEVICE_CONFIG_LIST
from .entity import ViCareEntity
from .utils import is_supported

_LOGGER = logging.getLogger(__name__)


@dataclass
class ViCareButtonEntityDescription(
    ButtonEntityDescription, ViCareRequiredKeysMixinWithSet
):
    """Describes ViCare button entity."""


BUTTON_DESCRIPTIONS: tuple[ViCareButtonEntityDescription, ...] = (
    ViCareButtonEntityDescription(
        key="activate_onetimecharge",
        translation_key="activate_onetimecharge",
        icon="mdi:shower-head",
        entity_category=EntityCategory.CONFIG,
        value_getter=lambda api: api.getOneTimeCharge(),
        value_setter=lambda api: api.activateOneTimeCharge(),
    ),
)


def _build_entity(
    vicare_api: PyViCareDevice,
    device_config: PyViCareDeviceConfig,
    entity_description: ViCareButtonEntityDescription,
):
    """Create a ViCare button entity."""
    if is_supported(entity_description.key, entity_description, vicare_api):
        return ViCareButton(
            vicare_api,
            device_config,
            entity_description,
        )
    return None


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Create the ViCare button entities."""
    entities = []

    # Currently we only support a single device
    device_config, device, _, _, _ = hass.data[DOMAIN][config_entry.entry_id][
        VICARE_DEVICE_CONFIG_LIST
    ][0]
    for description in BUTTON_DESCRIPTIONS:
        entity = await hass.async_add_executor_job(
            _build_entity,
            device,
            device_config,
            description,
        )
        if entity:
            entities.append(entity)

    async_add_entities(entities)


class ViCareButton(ViCareEntity, ButtonEntity):
    """Representation of a ViCare button."""

    entity_description: ViCareButtonEntityDescription

    def __init__(
        self,
        api: PyViCareDevice,
        device_config: PyViCareDeviceConfig,
        description: ViCareButtonEntityDescription,
    ) -> None:
        """Initialize the button."""
        super().__init__(device_config, api, description.key)
        self.entity_description = description

    def press(self) -> None:
        """Handle the button press."""
        try:
            with suppress(PyViCareNotSupportedFeatureError):
                self.entity_description.value_setter(self._api)
        except requests.exceptions.ConnectionError:
            _LOGGER.error("Unable to retrieve data from ViCare server")
        except ValueError:
            _LOGGER.error("Unable to decode data from ViCare server")
        except PyViCareRateLimitError as limit_exception:
            _LOGGER.error("Vicare API rate limit exceeded: %s", limit_exception)
        except PyViCareInvalidDataError as invalid_data_exception:
            _LOGGER.error("Invalid data from Vicare server: %s", invalid_data_exception)
