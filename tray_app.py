"""
tray_app.py - Sistem tepsisinde (system tray) çalışan uygulama.

pystray + Pillow kullanarak Windows system tray'de ikon gösterir.
Sağ tık menüsü ile ayarlar, otomatik başlatma ve çıkış seçenekleri sunar.
"""

import pystray
from PIL import Image, ImageDraw, ImageFont
import threading
import sys
import os

from autostart import set_autostart, is_autostart_enabled
from config_gui import ConfigWindow, load_config, save_config


def create_tray_icon_image() -> Image.Image:
    """Sistem tepsisi için 64x64 ikon oluşturur."""
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Arka plan - yuvarlatılmış dikdörtgen (daire)
    draw.ellipse([2, 2, size - 2, size - 2], fill="#89b4fa")

    # Ortaya müzik notası sembolü çiz
    # Not gövdesi (daire)
    draw.ellipse([16, 34, 30, 48], fill="#1e1e2e")
    draw.ellipse([34, 30, 48, 44], fill="#1e1e2e")

    # Not çubukları
    draw.rectangle([28, 14, 31, 38], fill="#1e1e2e")
    draw.rectangle([46, 10, 49, 34], fill="#1e1e2e")

    # Bağlantı çubuğu (üst)
    draw.rectangle([28, 12, 49, 16], fill="#1e1e2e")

    return img


class TrayApp:
    """Sistem tepsisi uygulaması."""

    def __init__(self, key_mapper):
        self.key_mapper = key_mapper
        self.icon = None
        self._config_window = None
        # Cache autostart state to avoid reading config.json from disk on every menu hover
        config = load_config()
        self._autostart_cached = config.get("autostart", False)

    def _on_settings(self, icon, item):
        """Ayarlar menüsü tıklandığında."""
        def open_gui():
            window = ConfigWindow(on_save_callback=self._on_config_saved)
            window.show()
        threading.Thread(target=open_gui, daemon=True).start()

    def _on_config_saved(self, new_mappings: dict):
        """Config kaydedildiğinde key mapper'ı yeniden yükler."""
        self.key_mapper.reload(new_mappings)

    def _on_autostart_toggle(self, icon, item):
        """Otomatik başlatma açma/kapatma."""
        new_val = not self._autostart_cached
        self._autostart_cached = new_val
        config = load_config()
        config["autostart"] = new_val
        save_config(config)
        set_autostart(new_val)
        # Menüyü güncelle
        icon.update_menu()

    def _is_autostart_checked(self, item) -> bool:
        """Otomatik başlatma durumunu döndürür (bellekteki cache'den)."""
        return self._autostart_cached

    def _on_quit(self, icon, item):
        """Uygulamadan çıkış."""
        self.key_mapper.stop()
        icon.stop()

    def run(self):
        """Sistem tepsisi uygulamasını başlatır."""
        image = create_tray_icon_image()

        menu = pystray.Menu(
            pystray.MenuItem("⚙️ Ayarlar", self._on_settings),
            pystray.MenuItem(
                "🚀 Otomatik Başlat",
                self._on_autostart_toggle,
                checked=self._is_autostart_checked,
            ),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("❌ Çıkış", self._on_quit),
        )

        self.icon = pystray.Icon(
            name="MiniKeyCtrl",
            icon=image,
            title="MiniKeyCtrl - Aktif",
            menu=menu,
        )

        self.icon.run()
