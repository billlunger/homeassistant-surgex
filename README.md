# SurgeX for Home Assistant

Custom Home Assistant integration for SurgeX local REST API devices, including the DisplayPak+ SX-DPP-104.

## Features

- Local polling over HTTP or HTTPS
- Basic authentication
- Outlet and outlet-group switches
- Outlet reboot buttons
- Device command buttons for shutdown state and energy reset
- Electrical monitoring sensors:
  - Power
  - Current
  - Voltage
  - Neutral-ground voltage
  - Frequency
  - Energy usage
  - Temperature
  - Power factor
  - Crest factor
- Device health binary sensors:
  - Connected
  - Running
  - Shutdown
  - Alarm
  - Surge protection
  - Wiring fault

## Tested Device

- SurgeX DisplayPak+ `SX-DPP-104`

The integration is written against the shared SurgeX v1 REST API shape used by DisplayPak+, Axess+, Squid, and Vertical Series API documentation.

## HACS Installation

1. Open HACS.
2. Go to **Integrations**.
3. Open the menu and choose **Custom repositories**.
4. Add this repository URL.
5. Select category **Integration**.
6. Install **SurgeX**.
7. Restart Home Assistant.
8. Go to **Settings > Devices & services > Add integration** and search for **SurgeX**.

## Manual Installation

Copy `custom_components/surgex` into your Home Assistant config directory:

```text
/config/custom_components/surgex
```

Restart Home Assistant, then add the **SurgeX** integration from **Settings > Devices & services**.

## Configuration

The config flow asks for:

- Host, for example `192.168.4.241`
- Port, usually `80`
- HTTPS enabled or disabled
- Username
- Password

The integration uses the device endpoint:

```text
/api/v1/currentStatus
```

and documented outlet commands such as:

```text
/api/v1/1/1/PowerOn
/api/v1/1/1/PowerOff
/api/v1/1/1/Reboot
```

## Notes

This is an unofficial integration and is not affiliated with AMETEK or SurgeX.
