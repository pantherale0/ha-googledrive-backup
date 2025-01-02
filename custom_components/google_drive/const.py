"""Constants for integration_blueprint."""

from logging import Logger, getLogger


LOGGER: Logger = getLogger(__package__)

DOMAIN = "google_drive"

SCOPES = [
    "https://www.googleapis.com/auth/drive.appdata",
    "https://www.googleapis.com/auth/drive.appfolder",
]
