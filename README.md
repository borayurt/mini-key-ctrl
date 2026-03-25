# MiniKeyCtrl

MiniKeyCtrl is a small Windows tray app that remaps `F1` through `F8` from a specific keyboard to media controls like mute, volume, play/pause, and track navigation.

It is designed for setups where you want device-specific remapping instead of changing the behavior of every keyboard connected to the system.

## What It Does

- Runs in the system tray
- Lets you assign media actions to `F1`-`F8`
- Targets a specific keyboard device through the Interception driver
- Opens a simple configuration window for changing mappings
- Supports Windows autostart
- Sends media key events without blocking the UI

## Requirements

- Windows
- Python 3.8+
- Administrator rights when launching the app
- Interception driver for device-specific keyboard capture

Python dependencies are listed in [`requirements.txt`](/c:/workspace/mini-key-ctrl/requirements.txt):

- `pystray`
- `Pillow`

## Installation

### 1. Install Python dependencies

```powershell
pip install -r requirements.txt
```

Or run the included setup script:

```powershell
.\setup.bat
```

### 2. Install the Interception driver

This project uses the Interception driver to detect input from a specific keyboard.

1. Download Interception from the official repository:
   `https://github.com/oblitum/Interception`
2. Open an elevated Command Prompt
3. Run:

```powershell
install-interception.exe /install
```

4. Restart Windows

Without the driver, the tray app may still open, but device-specific remapping will not work correctly.

## Running the App

Start the app with:

```powershell
python main.py
```

If you want to launch it without a console window:

```powershell
pythonw run.pyw
```

On startup, the app may request administrator permission. That is expected for the keyboard interception flow used here.

## Configuration

Settings are stored in [`config.json`](/c:/workspace/mini-key-ctrl/config.json).

Default mappings:

- `F1` -> `mute`
- `F2` -> `volume_down`
- `F3` -> `volume_up`
- `F4` -> `prev_track`
- `F5` -> `play_pause`
- `F6` -> `next_track`
- `F7` -> `stop`
- `F8` -> `launch_media`

The configuration window allows you to:

- Change the media action assigned to each key
- Pick the target keyboard device
- Save settings used by the tray app

## Main Files

- [`main.py`](/c:/workspace/mini-key-ctrl/main.py): app entry point and admin elevation flow
- [`tray_app.py`](/c:/workspace/mini-key-ctrl/tray_app.py): system tray UI
- [`config_gui.py`](/c:/workspace/mini-key-ctrl/config_gui.py): settings window
- [`device_backend.py`](/c:/workspace/mini-key-ctrl/device_backend.py): Interception-based keyboard backend
- [`key_mapper.py`](/c:/workspace/mini-key-ctrl/key_mapper.py): media key dispatch and debounce logic
- [`autostart.py`](/c:/workspace/mini-key-ctrl/autostart.py): Windows autostart integration

## Notes

- This project is Windows-only.
- The current UI text is primarily in Turkish.
- If line ending warnings appear in Git on Windows, they are usually related to `LF`/`CRLF` conversion and not app behavior.

## Additional Docs

- [`OPTIMIZATION_SUMMARY.md`](/c:/workspace/mini-key-ctrl/OPTIMIZATION_SUMMARY.md)
- [`ADDITIONAL_RECOMMENDATIONS.md`](/c:/workspace/mini-key-ctrl/ADDITIONAL_RECOMMENDATIONS.md)
