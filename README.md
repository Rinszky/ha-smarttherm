# SmartTherm for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)

A custom integration for Home Assistant to control SmartTherm (OCStat) thermostats. This integration allows you to monitor and control your heating devices directly from Home Assistant, replacing complex YAML REST configurations with native climate entities.

## Features

- **Native Climate Entities**: Full support for Home Assistant climate platform.
- **Real-time Monitoring**: Track current room temperature and heating state (`th_work`).
- **Temperature Control**: Set target temperature with immediate feedback.
- **Preset Modes**: Switch between `Scheduled`, `Manual`, `Off`, and `Hold` modes.
- **Config Flow Support**: Easy setup via the Home Assistant UI (no YAML required).
- **Auto-Discovery**: Automatically adds all thermostats linked to your SmartTherm account (e.g., Ground Floor, Rooftop).
- **Optimized Updates**: Immediate state refresh after commands to ensure the UI stays in sync.

## Installation

### Method 1: HACS (Recommended)

1. Open **HACS** in your Home Assistant instance.
2. Click the three dots in the top right corner and select **Custom repositories**.
3. Paste the URL of this repository: `https://github.com/Rinszky/ha-smarttherm`
4. Select **Integration** as the category and click **Add**.
5. Once added, search for **SmartTherm** and click **Download**.
6. Restart Home Assistant.

### Method 2: Manual Installation

1. Download the latest release.
2. Copy the `smarttherm` directory from `custom_components/` into your Home Assistant's `custom_components/` directory.
3. Restart Home Assistant.

## Configuration

1. Go to **Settings** > **Devices & Services**.
2. Click **Add Integration** and search for **SmartTherm**.
3. Enter your SmartTherm app credentials:
   - **Email**: Your registered email address.
   - **Password**: Your account password.
4. The integration will automatically log in and discover your thermostats.

## State Attributes

The integration provides additional debugging information in the entity attributes:
- `hvac_action`: Shows if the device is currently `heating` or `idle`.
- `preset_mode`: Displays the active thermostat profile.
- `last_api_request_url`: Useful for troubleshooting API communication.

## Disclaimer

This integration is not affiliated with or endorsed by SmartTherm or OCStat. Use it at your own risk.

## Support

If you encounter any issues, please open an issue on the GitHub repository.
