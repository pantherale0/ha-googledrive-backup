# Google Drive Backup

[![GitHub Release][releases-shield]][releases]
[![GitHub Activity][commits-shield]][commits]
[![License][license-shield]](LICENSE)

[![hacs][hacsbadge]][hacs]

_Integration to provide a backup provider for Google Drive._

**This integration does not set up any platforms.**

## Pre-configuration

You will need to add the [Google Drive API](https://console.cloud.google.com/apis/library/drive.googleapis.com) to a project in the Google Developers Console. You can use an existing project if you wish.

Follow the instructions found for the [Google Calendar integration](https://www.home-assistant.io/integrations/google) on the Home Assistant website to create new application credentials.

In the instructions on the Home Assistant website, rather than setting up the Google Calendar API, you should enable the Google Drive API instead otherwise this will not work.

NOTE: You must copy and save your Client ID and Client Secret in a safe and secure location. If you need to restore a backup from new, you will not be able to download the files directly from Google Drive.

## Installation

[![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=pantherale0&repository=ha-googledrive-backup&category=integration)

1. Add repository URL into HACS and install "Google Drive"
1. Restart Home Assistant

## Configuration is done in the UI

[![Open your Home Assistant instance and Manage your application credentials.](https://my.home-assistant.io/badges/application_credentials.svg)](https://my.home-assistant.io/redirect/application_credentials/)

1. Click above button to access application credentials
1. Click "ADD APPLICATION CREDENTIALS" in the bottom right corner of the screen
1. Set "Google Drive" as the "Integration"
1. Provide a name (this can be anything you like)
1. Enter the OAuth Client ID copied from the Google Developers Console
1. Enter the OAuth Client Secret copied from the Google Developers Console
1. Click "ADD"

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=google_drive)

1. Use the above link to create a new Google Drive integration configuration, it will automatically redirect you to the Google sign in screen, select / login with your account and grant the required permissions.
1. Click the "Link account" button.
1. Integration is now setup

## Configure backups

1. The integration will appear as a backup provider under Settings > System > Backup. You will need to update your existing configuration or create a new backup configuration if you have not already done so. Simply enable the "Google Drive" provider in your settings.

## Restore a backup to a new instance

!YOU CANNOT RESTORE TO A NEW INSTANCE WITHOUT YOUR OAUTH CREDENTIALS AND ENCRYPTION KEY!

[![Open your Home Assistant instance and start setting up a new integration.](https://my.home-assistant.io/badges/config_flow_start.svg)](https://my.home-assistant.io/redirect/config_flow_start/?domain=google_drive)

1. Setup integration in your new instance as above, using your OAuth credentials you have saved to a secure location.

[![Open your Home Assistant instance and Back up your Home Assistant installation.](https://my.home-assistant.io/badges/backup.svg)](https://my.home-assistant.io/redirect/backup/)

1. Locate the backup you wish to restore, and restore following the prompts on screen.

## FAQs

- How can I download my files from Google Drive?
    This integration uses a special hidden folder in Google Drive for app data storage. This is done for security purposes, it means the integration does not need full access to your Google Drive and scopes can be limited. This is following Google's own recommendations.

- I've lost my OAuth and/or encryption keys, can I restore?
    No, you have been warned many times in this readme to ensure these are saved somewhere safe and secure. Issues relating to this will be closed.

If you have any issues with backups in general, report to the Home Assistant core repository, this integration only handles downloading and uploading files to Google Drive, nothing more, nothing less. Unrelated issues will be closed.

## Known issues

- Log can be spammed with `[googleapiclient.discovery_cache] file_cache is only supported with oauth2client<4.0.0`
- Currently can appear slow to respond, this is purely cosmetic, please don't spam the backup button or download buttons.

## Contributions are welcome!

If you want to contribute to this please read the [Contribution guidelines](CONTRIBUTING.md)

---

[ha-googledrive-backup]: https://github.com/pantherale0/ha-googledrive-backup
[commits-shield]: https://img.shields.io/github/commit-activity/y/pantherale0/ha-googledrive-backup.svg?style=for-the-badge
[commits]: https://github.com/pantherale0/ha-googledrive-backup/commits/main
[hacs]: https://github.com/hacs/integration
[hacsbadge]: https://img.shields.io/badge/HACS-Default-green.svg?style=for-the-badge
[license-shield]: https://img.shields.io/github/license/pantherale0/ha-googledrive-backup.svg?style=for-the-badge
[releases-shield]: https://img.shields.io/github/release/pantherale0/ha-googledrive-backup.svg?style=for-the-badge
[releases]: https://github.com/pantherale0/ha-googledrive-backup/releases
