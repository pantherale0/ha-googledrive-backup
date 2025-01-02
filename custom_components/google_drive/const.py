"""Constants for integration_blueprint."""

from logging import Logger, getLogger

from aiogoogle.client import Aiogoogle
from homeassistant.util.hass_dict import HassKey

LOGGER: Logger = getLogger(__package__)

DOMAIN = "google_drive"

SCOPES = [
    "https://www.googleapis.com/auth/drive.appdata",
    "https://www.googleapis.com/auth/drive.appfolder",
]

DATA_DRIVE: HassKey[Aiogoogle] = HassKey(DOMAIN)
