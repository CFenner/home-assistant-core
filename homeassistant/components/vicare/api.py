"""API for Viessmann ViCare bound to Home Assistant OAuth."""

from asyncio import run_coroutine_threadsafe

from PyViCare.PyViCareAbstractOAuthManager import AbstractViCareOAuthManager

from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_entry_oauth2_flow

# TODO the following two API examples are based on our suggested best practices
# for libraries using OAuth2 with requests or aiohttp. Delete the one you won't use.
# For more info see the docs at https://developers.home-assistant.io/docs/api_lib_auth/#oauth2.


class ConfigEntryAuth(AbstractViCareOAuthManager):
    """Provide Viessmann ViCare authentication tied to an OAuth2 based config entry."""

    def __init__(
        self,
        hass: HomeAssistant,
        oauth_session: config_entry_oauth2_flow.OAuth2Session,
    ) -> None:
        """Initialize Viessmann ViCare Auth."""
        self.hass = hass
        self.session = oauth_session
        super().__init__(self.session.token)

    def renewToken(self) -> None:
        # def refresh_tokens(self) -> str:
        """Refresh Viessmann ViCare tokens using Home Assistant OAuth2 session."""
        run_coroutine_threadsafe(
            self.session.async_ensure_token_valid(), self.hass.loop
        ).result()
