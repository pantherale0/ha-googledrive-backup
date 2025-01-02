"""Backup platform for Google Drive."""

import asyncio
import io
import json
from collections.abc import AsyncIterator, Callable, Coroutine
from typing import Any

from googleapiclient.http import MediaInMemoryUpload, MediaIoBaseDownload
from homeassistant.components.backup import AgentBackup, BackupAgent, BackupAgentError
from homeassistant.core import HomeAssistant

from .api import AsyncConfigEntryAuth
from .const import DOMAIN, LOGGER


async def async_get_backup_agents(
    hass: HomeAssistant,
    **kwargs: Any,  # noqa: ARG001
) -> list[BackupAgent]:
    """Return the cloud backup agent."""
    if not hass.config_entries.async_loaded_entries(DOMAIN):
        LOGGER.debug("No config entry found or entry is not loaded")
        return []

    return [
        DriveBackupAgent(hass=hass, gdrive=x.runtime_data)  # type: ignore  # noqa: PGH003
        for x in hass.config_entries.async_loaded_entries(DOMAIN)
    ]


async def get_all_bytes(iterator: AsyncIterator[bytes]) -> bytes:
    """
    Read all bytes from an AsyncIterator[bytes] and return a single bytes object.

    Args:
      iterator: The AsyncIterator[bytes] to read from.

    Returns:
      A bytes object containing all bytes read from the iterator.

    """
    all_bytes = bytearray()
    async for chunk in iterator:
        all_bytes.extend(chunk)
    return bytes(all_bytes)


def remove_list_item_by_value(data: list, key: str, value: str) -> list:
    """Remove a given item from a list, filtered by key value."""
    for i, d in enumerate(data):
        if d.get(key) == value:
            return data[:i] + data[i + 1 :]
    return data


class DriveBackupAgent(BackupAgent):
    """Google Drive backup agent."""

    domain = DOMAIN
    name = DOMAIN
    _running_config: list = []

    def __init__(self, hass: HomeAssistant, gdrive: AsyncConfigEntryAuth) -> None:
        """Init the backup agent."""
        super().__init__()
        self._gdrive = gdrive
        self._hass = hass

    async def retrieve_file_content(self, file_id: str, service) -> bytes:
        """Get file content from Google Drive."""
        query = service.files().get_media(fileId=file_id)  # type: ignore
        stream = io.BytesIO()
        downloader = MediaIoBaseDownload(stream, query)
        done = False
        while done is False:
            status, done = await self._hass.async_add_executor_job(
                downloader.next_chunk
            )
        return stream.getvalue()

    async def create_or_update_config(
        self, service, data: list[dict] | None = None
    ) -> None:
        """Create or update backups.json file that contains AgentBackup data."""
        if data is None:
            data = []
        await self.create_file(
            file_name="backups.json",
            stream=json.dumps(data).encode("utf-8"),
            service=service,
        )

    async def load_config(self, service) -> list[dict]:
        """Retrieve backups.json from Google Drive."""
        query = service.files().list(  # type: ignore
            spaces="appDataFolder",
            fields="files(id)",
            q="name = 'backups.json'",
        )
        data = await self._hass.async_add_executor_job(query.execute)
        if len(data.get("files", [])) == 0:
            await self.create_or_update_config(service=service)
            return []

        # download the file
        data = await self.retrieve_file_content(data["files"][0]["id"], service)
        self._running_config = json.loads(data.decode("utf-8"))
        return self._running_config

    async def get_files(self, service) -> list[AgentBackup]:
        """Get all files."""
        data = await self.load_config(service)
        files = []
        for file in data:
            files.append(AgentBackup.from_dict(file))  # noqa: PERF401
        return files

    async def get_file(self, backup_id: str, service) -> AgentBackup | None:
        """Get a file from Google Drive."""
        data = await self.get_files(service)
        for file in data:
            if file.backup_id == backup_id:
                return file
        return None

    async def get_google_drive_file_id(self, backup_id: str, service) -> str | None:
        """Retrun the Google Drive file id."""
        query = service.files().list(  # type: ignore
            spaces="appDataFolder",
            fields="files(id)",
            q=f"name = '{backup_id}.tar'",
        )
        data = await self._hass.async_add_executor_job(query.execute)
        if len(data.get("files", [])) == 0:
            return None
        return data["files"][0]["id"]

    async def download_backup(self, backup_id: str, service) -> bytes | None:
        """Get a backup from file storage (returns tar file)."""
        file_id = await self.get_google_drive_file_id(backup_id, service)
        # download the file
        return await self.retrieve_file_content(file_id, service)

    async def create_file(
        self, file_name: str, stream: AsyncIterator[bytes] | bytes, service
    ) -> str:
        """Create a file in Google Drive."""
        file_metadata = {
            "name": file_name,
            "parents": ["appDataFolder"],
        }
        if isinstance(stream, AsyncIterator):
            media = MediaInMemoryUpload(
                await get_all_bytes(stream),
                resumable=True,
                chunksize=1024 * 1024,
            )
        else:
            media = MediaInMemoryUpload(
                stream,
                resumable=True,
                chunksize=1024 * 1024,
            )
        request = service.files().create(  # type: ignore  # noqa: PGH003
            body=file_metadata, media_body=media, fields="id"
        )
        response = None
        while response is None:
            status, response = await self._hass.async_add_executor_job(
                request.next_chunk
            )
            if response is None and status is not None:
                LOGGER.debug("File %s uploaded %s%", file_name, status.progress() * 100)
        return response.get("id")

    async def create_backup(
        self, stream: AsyncIterator[bytes] | bytes, backup: AgentBackup, service
    ) -> None:
        """Create a backup."""
        # first upload
        file_id = await self.create_file(f"{backup.backup_id}.tar", stream, service)
        if not file_id:
            raise BackupAgentError("Unknown Google Drive Error")  # noqa: EM101, TRY003
        # now update backups.json
        conf = await self.load_config(service)
        conf.append(backup.as_dict())
        await self.create_or_update_config(service, conf)

    async def delete_file(self, file_id: str, service) -> None:
        """Delete a given file."""
        await self._hass.async_add_executor_job(
            service.files().delete(fileId=file_id).execute  # type: ignore  # noqa: PGH003
        )

    async def async_download_backup(
        self,
        backup_id: str,
        **kwargs: Any,  # noqa: ARG002
    ) -> AsyncIterator[bytes]:
        """Download an existing backup."""
        service = await self._gdrive.get_resource()
        details = await self.get_file(backup_id, service)
        if not details:
            raise BackupAgentError("Backup not found")  # noqa: EM101, TRY003
        data = await self.download_backup(backup_id, service)
        if data is not None:
            reader = asyncio.StreamReader()
            reader.feed_data(data)
            reader.feed_eof()
            return reader
        raise BackupAgentError("Backup not found")  # noqa: EM101, TRY003

    async def async_upload_backup(
        self,
        *,
        open_stream: Callable[[], Coroutine[Any, Any, AsyncIterator[bytes]]],
        backup: AgentBackup,
        **kwargs: Any,  # noqa: ARG002
    ) -> None:
        service = await self._gdrive.get_resource()
        """Upload a new backup."""
        return await self.create_backup(await open_stream(), backup, service)

    async def async_delete_backup(self, backup_id: str, **kwargs: Any) -> None:  # noqa: ARG002
        """Delete a given backup."""
        service = await self._gdrive.get_resource()
        details = await self.get_file(backup_id, service)
        if not details:
            raise BackupAgentError("Backup not found")  # noqa: EM101, TRY003
        file_id = await self.get_google_drive_file_id(details.backup_id, service)
        await self.create_or_update_config(
            service,
            remove_list_item_by_value(self._running_config, "backup_id", backup_id),
        )
        if not file_id:
            raise BackupAgentError("Backup not found")  # noqa: EM101, TRY003
        await self.delete_file(file_id, service)

    async def async_list_backups(self, **kwargs: Any) -> list[AgentBackup]:  # noqa: ARG002
        """List all backups."""
        service = await self._gdrive.get_resource()
        return await self.get_files(service)

    async def async_get_backup(
        self,
        backup_id: str,
        **kwargs: Any,  # noqa: ARG002
    ) -> AgentBackup | None:
        """Return a given backup."""
        service = await self._gdrive.get_resource()
        return await self.get_file(backup_id, service)
