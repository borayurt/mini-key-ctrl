"""
autostart.py - Windows baslangicinda otomatik calistirma yonetimi.

Windows Registry uzerinden HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run
anahtarini kullanir.
"""

import os
import sys
import winreg

APP_NAME = "MiniKeyCtrl"
REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _quote_command_part(path: str) -> str:
    """Wrap a command path in quotes for safe use in the Run registry."""
    return f'"{path}"'


def _get_executable_path() -> str:
    """Return the command that should be stored in the Run registry."""
    if getattr(sys, "frozen", False):
        return _quote_command_part(sys.executable)

    run_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "run.pyw"))
    python_dir = os.path.dirname(sys.executable)
    pythonw_exe = os.path.join(python_dir, "pythonw.exe")
    if not os.path.exists(pythonw_exe):
        pythonw_exe = sys.executable

    return f'{_quote_command_part(pythonw_exe)} {_quote_command_part(run_script)}'


def _get_autostart_value() -> str | None:
    """Return the current Run entry value, if present."""
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REG_PATH,
            0,
            winreg.KEY_READ,
        ) as key:
            value, _ = winreg.QueryValueEx(key, APP_NAME)
            return value
    except FileNotFoundError:
        return None
    except OSError:
        return None


def enable_autostart() -> bool:
    """Add the app to Windows startup."""
    try:
        command = _get_executable_path()
        if _get_autostart_value() == command:
            return True

        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REG_PATH,
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
        return True
    except OSError:
        return False


def disable_autostart() -> bool:
    """Remove the app from Windows startup."""
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REG_PATH,
            0,
            winreg.KEY_SET_VALUE,
        ) as key:
            winreg.DeleteValue(key, APP_NAME)
        return True
    except FileNotFoundError:
        return True
    except OSError:
        return False


def is_autostart_enabled() -> bool:
    """Return whether the current startup command matches this installation."""
    return _get_autostart_value() == _get_executable_path()


def set_autostart(enabled: bool) -> bool:
    """Enable or disable autostart."""
    if enabled:
        return enable_autostart()
    return disable_autostart()
