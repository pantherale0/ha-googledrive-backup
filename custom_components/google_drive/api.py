"""API for Google Drive bound to Home Assistant OAuth."""

from functools import partial

from aiohttp.client_exceptions import ClientError, ClientResponseError
from cachetools import Cache
from google.auth.exceptions import RefreshError
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import Resource, build
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import CONF_ACCESS_TOKEN
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryNotReady,
    HomeAssistantError,
)
from homeassistant.helpers import config_entry_oauth2_flow


# fixes [googleapiclient.discovery_cache] file_cache is only supported with oauth2client<4.0.0  # noqa: E501
# https://github.com/googleapis/google-api-python-client/issues/325#issuecomment-274349841
class MemoryCache(Cache):
    _CACHE = {}

    def get(self, url):
        return MemoryCache._CACHE.get(url)

    def set(self, url, content):
        MemoryCache._CACHE[url] = content


class AsyncConfigEntryAuth:
    """Provide Google Drive authentication tied to an OAuth2 based config entry."""

    def __init__(
        self,
        hass: HomeAssistant,
        oauth2_session: config_entry_oauth2_flow.OAuth2Session,
    ) -> None:
        """Initialize Google Drive Auth."""
        self._hass = hass
        self.oauth_session = oauth2_session

    @property
    def access_token(self) -> str:
        """Return the access token."""
        return self.oauth_session.token[CONF_ACCESS_TOKEN]

    async def check_and_refresh_token(self) -> str:
        """Check the token."""
        try:
            await self.oauth_session.async_ensure_token_valid()
        except (RefreshError, ClientResponseError, ClientError) as ex:
            if (
                self.oauth_session.config_entry.state
                is ConfigEntryState.SETUP_IN_PROGRESS
            ):
                if isinstance(ex, ClientResponseError) and 400 <= ex.status < 500:
                    raise ConfigEntryAuthFailed(  # noqa: TRY003
                        "OAuth session is not valid, reauth required"  # noqa: EM101
                    ) from ex
                raise ConfigEntryNotReady from ex
            if isinstance(ex, RefreshError) or (
                hasattr(ex, "status") and ex.status == 400  # noqa: PLR2004
            ):
                self.oauth_session.config_entry.async_start_reauth(
                    self.oauth_session.hass
                )
            raise HomeAssistantError(ex) from ex
        return self.access_token

    async def get_resource(self) -> Resource:
        """Get current resource."""
        credentials = Credentials(await self.check_and_refresh_token())
        return await self._hass.async_add_executor_job(
            partial(
                build,
                "drive",
                "v3",
                credentials=credentials,
                cache=MemoryCache(maxsize=50),
            )
        )
