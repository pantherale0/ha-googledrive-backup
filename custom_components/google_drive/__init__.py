"""Google Drive integration for backups."""

from __future__ import annotations

import aiohttp
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import (
    ConfigEntryAuthFailed,
    ConfigEntryNotReady,
    HomeAssistantError,
)
from homeassistant.helpers.config_entry_oauth2_flow import (
    OAuth2Session,
    async_get_config_entry_implementation,
)

from .api import AsyncConfigEntryAuth

type GoogleDriveConfigEntry = ConfigEntry[AsyncConfigEntryAuth]


async def async_setup_entry(hass: HomeAssistant, entry: GoogleDriveConfigEntry) -> bool:
    """Set up Google Drive from a config entry."""
    implementation = await async_get_config_entry_implementation(hass, entry)
    session = OAuth2Session(hass, entry, implementation)
    try:
        await session.async_ensure_token_valid()
    except aiohttp.ClientResponseError as err:
        if 400 <= err.status < 500:
            raise ConfigEntryAuthFailed(
                "OAuth session is not valid, reauth required"
            ) from err
        raise ConfigEntryNotReady from err
    except aiohttp.ClientError as err:
        raise ConfigEntryNotReady from err

    entry.runtime_data = AsyncConfigEntryAuth(hass, session)

    return True
