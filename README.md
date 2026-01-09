# Click Counter Tray App

A small Windows system tray app that counts left and right mouse clicks all day.
The counter persists to disk and can be reset from the tray menu with a confirmation
dialog.

## Features

- Tray-only UI with tooltip and menu count display
- Tracks left and right clicks separately
- Confirmation dialog before reset
- Saves counts to `clicks.json` in the project folder

## Requirements

- Windows
- Python 3.9+
- `pynput`, `pystray`, `Pillow`

## Install

```bash
python -m pip install pynput pystray pillow
```

## Run

```bash
python main.py
```

## Notes

- The tray tooltip shows counts and the start time for the current session.
- The reset dialog uses a Tk message box.
