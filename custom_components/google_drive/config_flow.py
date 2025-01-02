"""Config flow for Google Drive"""

from __future__ import annotations

import logging  # noqa: TC003
from collections.abc import Mapping  # noqa: TC003
from typing import Any

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from homeassistant.config_entries import SOURCE_REAUTH, ConfigFlowResult
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_TOKEN
from homeassistant.helpers import config_entry_oauth2_flow

from .const import DOMAIN, LOGGER, SCOPES


class OAuth2FlowHandler(
    config_entry_oauth2_flow.AbstractOAuth2FlowHandler, domain=DOMAIN
):
    """OAuth handler for Google Drive authentication."""

    DOMAIN = DOMAIN

    @property
    def logger(self) -> logging.Logger:
        """Return logger."""
        return LOGGER

    @property
    def extra_authorize_data(self) -> dict[str, Any]:
        """Extra data to add to authorize URL."""
        return {
            "scope": " ".join(SCOPES),
            "access_type": "offline",
            "prompt": "consent",
        }

    async def async_step_reauth(
        self,
        entry_data: Mapping[str, Any],  # noqa: ARG002
    ) -> ConfigFlowResult:
        """Perform reauth during API error."""
        return await self.async_step_reauth_confirm()

    async def async_step_reauth_confirm(
        self, user_input: dict[str, Any] | None = None
    ) -> ConfigFlowResult:
        """Confirm reauth dialog."""
        if user_input is None:
            return self.async_show_form(step_id="reauth_confirm")
        return await self.async_step_user()

    async def async_oauth_create_entry(self, data: dict[str, Any]) -> ConfigFlowResult:
        """Create an entry for the flow or update an existing entry."""

        def _list_files() -> list:
            """List files via executor."""
            drive = build("drive", "v3", credentials=creds)
            results = (
                drive.files()
                .list(spaces="appDataFolder", fields="files(id, name)")
                .execute()
            )
            items = results.get("files", [])

        creds = Credentials(data[CONF_TOKEN][CONF_ACCESS_TOKEN])

        if self.source == SOURCE_REAUTH:
            reauth_entry = self._get_reauth_entry()
            LOGGER.debug("service.open_by_key")
            # try:
            await self.hass.async_add_executor_job(_list_files)
            # except AuthError as err:
            #     LOGGER.error("Authentication error occured: %s", str(err))
            #     return self.async_abort(reason="oauth_failed")
            return self.async_update_reload_and_abort(reauth_entry, data=data)

        # try:
        await self.hass.async_add_executor_job(_list_files)
        # except AuthError as err:
        #     LOGGER.error("Authentication error occured: %s", str(err))
        #     return self.async_abort(reason="oauth_failed")
        await self.async_set_unique_id("Google Drive")
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title="Google Drive", data=data)
