"""
MiniKeyCtrl main entry point.
"""

import ctypes
import os
import sys

from autostart import is_autostart_enabled, set_autostart
from config_gui import load_config
from device_backend import DeviceInputBackend
from key_mapper import KeyMapper
from tray_app import TrayApp


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False


def request_admin():
    if is_admin():
        return

    try:
        script = os.path.abspath(sys.argv[0])
        params = " ".join(sys.argv[1:])
        ctypes.windll.shell32.ShellExecuteW(
            None,
            "runas",
            sys.executable,
            f'"{script}" {params}',
            None,
            1,
        )
        sys.exit(0)
    except Exception:
        pass


def main():
    if not is_admin():
        request_admin()

    config = load_config()
    autostart_enabled = config.get("autostart", True)
    if is_autostart_enabled() != autostart_enabled:
        set_autostart(autostart_enabled)

    mapper = KeyMapper(config.get("mappings", {}))
    backend = DeviceInputBackend(mapper)
    backend.start(config)

    tray = TrayApp(mapper, backend)
    try:
        tray.run()
    except KeyboardInterrupt:
        pass
    finally:
        backend.stop()


if __name__ == "__main__":
    main()
