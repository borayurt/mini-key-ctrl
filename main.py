"""
MiniKeyCtrl - 8 Tuşlu Mini Klavye Kontrol Programı
====================================================

8 tuşlu mini klavyeden gelen F1-F8 tuşlarını yakalayıp
multimedya kontrol fonksiyonlarına dönüştürür.

Kullanım:
    python main.py

Not: Global tuş yakalama için yönetici (admin) hakları gerekebilir.
"""

import ctypes
import os
import sys

from key_mapper import KeyMapper
from tray_app import TrayApp
from autostart import is_autostart_enabled, set_autostart
from config_gui import load_config


def is_admin() -> bool:
    """Yönetici haklarıyla çalışıp çalışmadığını kontrol eder."""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin()
    except Exception:
        return False


def request_admin():
    """Programı yönetici olarak yeniden başlatır."""
    if not is_admin():
        try:
            script = os.path.abspath(sys.argv[0])
            params = " ".join(sys.argv[1:])
            ctypes.windll.shell32.ShellExecuteW(
                None, "runas", sys.executable, f'"{script}" {params}', None, 1
            )
            sys.exit(0)
        except Exception:
            pass  # Kullanıcı UAC isteğini reddetti, normal olarak devam et


def main():
    """Ana giriş noktası."""
    # Yönetici hakları iste (keyboard kütüphanesi için gerekli olabilir)
    if not is_admin():
        request_admin()

    # Config yükle
    config = load_config()
    mappings = config.get("mappings", {})
    autostart_enabled = config.get("autostart", True)

    # Otomatik başlatma ayarını uygula
    if is_autostart_enabled() != autostart_enabled:
        set_autostart(autostart_enabled)

    # Key mapper başlat
    mapper = KeyMapper(mappings)
    mapper.start()

    # Sistem tepsisi uygulamasını başlat (ana thread'de çalışır)
    tray = TrayApp(mapper)
    try:
        tray.run()
    except KeyboardInterrupt:
        pass
    finally:
        mapper.stop()


if __name__ == "__main__":
    main()
