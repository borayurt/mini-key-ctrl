"""
tray_app.py - System tray application.
"""

import threading

import pystray
from PIL import Image, ImageDraw

from autostart import set_autostart
from config_gui import ConfigWindow, load_config, save_config


def create_tray_icon_image() -> Image.Image:
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse([2, 2, size - 2, size - 2], fill="#89b4fa")
    draw.ellipse([16, 34, 30, 48], fill="#1e1e2e")
    draw.ellipse([34, 30, 48, 44], fill="#1e1e2e")
    draw.rectangle([28, 14, 31, 38], fill="#1e1e2e")
    draw.rectangle([46, 10, 49, 34], fill="#1e1e2e")
    draw.rectangle([28, 12, 49, 16], fill="#1e1e2e")
    return img


class TrayApp:
    """System tray UI and settings launcher."""

    def __init__(self, key_mapper, backend):
        self.key_mapper = key_mapper
        self.backend = backend
        self.icon = None
        self._autostart_cached = load_config().get("autostart", False)
        self._device_status_text = self.backend.get_status()["message"] if self.backend else "Backend hazir degil"
        if self.backend:
            self.backend.status_callback = self._handle_backend_status

    def _handle_backend_status(self, status: dict):
        new_text = status["message"]
        if new_text == self._device_status_text:
            return
        self._device_status_text = new_text
        if self.icon:
            try:
                self.icon.title = f"MiniKeyCtrl - {self._device_status_text}"
                self.icon.update_menu()
            except Exception:
                pass

    def _on_settings(self, _icon, _item):
        def open_gui():
            window = ConfigWindow(backend=self.backend, on_save_callback=self._on_config_saved)
            window.show()

        threading.Thread(target=open_gui, daemon=True).start()

    def _on_config_saved(self, new_config: dict):
        self.key_mapper.reload(new_config.get("mappings", {}))
        if self.backend:
            self.backend.reload_config(new_config)
            self._handle_backend_status(self.backend.get_status())

    def _on_autostart_toggle(self, icon, _item):
        new_val = not self._autostart_cached
        self._autostart_cached = new_val
        config = load_config()
        config["autostart"] = new_val
        save_config(config)
        set_autostart(new_val)
        icon.update_menu()

    def _is_autostart_checked(self, _item) -> bool:
        return self._autostart_cached

    def _device_status_label(self, _item) -> str:
        return self._device_status_text

    def _on_quit(self, icon, _item):
        if self.backend:
            self.backend.stop()
        else:
            self.key_mapper.stop()
        icon.stop()

    def run(self):
        image = create_tray_icon_image()
        menu = pystray.Menu(
            pystray.MenuItem(self._device_status_label, None, enabled=False),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Ayarlar", self._on_settings),
            pystray.MenuItem(
                "Otomatik Baslat",
                self._on_autostart_toggle,
                checked=self._is_autostart_checked,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Cikis", self._on_quit),
        )

        self.icon = pystray.Icon(
            name="MiniKeyCtrl",
            icon=image,
            title=f"MiniKeyCtrl - {self._device_status_text}",
            menu=menu,
        )
        self.icon.run()
