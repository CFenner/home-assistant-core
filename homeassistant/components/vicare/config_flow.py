"""Config flow for ViCare integration."""

from __future__ import annotations

from collections.abc import Mapping
import logging
from typing import Any

from PyViCare.PyViCareUtils import (
    PyViCareInvalidConfigurationError,
    PyViCareInvalidCredentialsError,
)
import voluptuous as vol

from homeassistant.components import dhcp
from homeassistant.config_entries import (
    ConfigEntry,
    ConfigFlow,
    ConfigFlowResult,
    OptionsFlow,
)
from homeassistant.const import CONF_CLIENT_ID, CONF_PASSWORD, CONF_USERNAME
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv
from homeassistant.helpers.device_registry import format_mac

from . import vicare_login
from .const import (
    CONF_EXTENDED_API,
    CONF_HEATING_TYPE,
    DEFAULT_HEATING_TYPE,
    DOMAIN,
    VICARE_NAME,
    HeatingType,
)

_LOGGER = logging.getLogger(__name__)

REAUTH_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_PASSWORD): cv.string,
        vol.Required(CONF_CLIENT_ID): cv.string,
    }
)

USER_SCHEMA = REAUTH_SCHEMA.extend(
    {
        vol.Required(CONF_USERNAME): cv.string,
        vol.Required(CONF_HEATING_TYPE, default=DEFAULT_HEATING_TYPE.value): vol.In(
            [e.value for e in HeatingType]
        ),
    }
)

OPTIONS_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EXTENDED_API): bool,
    }
)


class ViCareConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for ViCare."""

    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Invoke when a user initiates a flow via the user interface."""
        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        errors: dict[str, str] = {}

        if user_input is not None:
            try:
                await self.hass.async_add_executor_job(
                    vicare_login, self.hass, user_input
                )
            except (PyViCareInvalidConfigurationError, PyViCareInvalidCredentialsError):
                errors["base"] = "invalid_auth"
            else:
                return self.async_create_entry(title=VICARE_NAME, data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=USER_SCHEMA,
            errors=errors,
        )

    def __init__(self) -> None:
        """Initialize."""
        self.entry: ConfigEntry | None = None

    async def async_step_reauth(
        self, entry_data: Mapping[str, Any]
    ) -> ConfigFlowResult:
        """Handle re-authentication with ViCare."""
        self.entry = self.hass.config_entries.async_get_entry(self.context["entry_id"])
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm re-authentication with ViCare."""
        errors: dict[str, str] = {}
        assert self.entry is not None

        if user_input:
            data = {
                **self.entry.data,
                **user_input,
            }

            try:
                await self.hass.async_add_executor_job(vicare_login, self.hass, data)
            except (PyViCareInvalidConfigurationError, PyViCareInvalidCredentialsError):
                errors["base"] = "invalid_auth"
            else:
                self.hass.config_entries.async_update_entry(
                    self.entry,
                    data=data,
                )
                await self.hass.config_entries.async_reload(self.entry.entry_id)
                return self.async_abort(reason="reauth_successful")

        return self.async_show_form(
            step_id="reauth_confirm",
            data_schema=self.add_suggested_values_to_schema(
                REAUTH_SCHEMA, self.entry.data
            ),
            errors=errors,
        )

    async def async_step_dhcp(
        self, discovery_info: dhcp.DhcpServiceInfo
    ) -> ConfigFlowResult:
        """Invoke when a Viessmann MAC address is discovered on the network."""
        formatted_mac = format_mac(discovery_info.macaddress)
        _LOGGER.debug("Found device with mac %s", formatted_mac)

        await self.async_set_unique_id(formatted_mac)
        self._abort_if_unique_id_configured()

        if self._async_current_entries():
            return self.async_abort(reason="single_instance_allowed")

        return await self.async_step_user()

    @staticmethod
    @callback
    def async_get_options_flow(
        config_entry: ConfigEntry,
    ) -> OptionsFlow:
        """Create the options flow."""
        return OptionsFlowHandler(config_entry)


class OptionsFlowHandler(OptionsFlow):
    """Options flow handler."""

    def __init__(self, config_entry: ConfigEntry) -> None:
        """Initialize options flow."""
        self.entry = config_entry

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Manage the options."""
        errors: dict[str, str] = {}
        if user_input is not None:
            return self.async_create_entry(data=user_input)

        return self.async_show_form(
            step_id="init",
            description_placeholders={
                "api_plan_url": "https://developer.viessmann.com/start/pricing.html",
            },
            data_schema=self.add_suggested_values_to_schema(
                OPTIONS_SCHEMA,
                user_input or dict(self.entry.options),
            ),
            errors=errors,
        )
