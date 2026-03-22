"""
autostart.py - Windows başlangıcında otomatik çalıştırma yönetimi.

Windows Registry üzerinden HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run
anahtarını kullanır.
"""

import sys
import os
import winreg

APP_NAME = "MiniKeyCtrl"
REG_PATH = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _get_executable_path() -> str:
    """Çalışan script/exe'nin tam yolunu döndürür."""
    if getattr(sys, "frozen", False):
        # PyInstaller ile paketlenmiş exe
        return sys.executable
    else:
        # Python script olarak çalışıyor - pythonw.exe ile konsol penceresi olmadan
        run_script = os.path.abspath(os.path.join(os.path.dirname(__file__), "run.pyw"))
        python_dir = os.path.dirname(sys.executable)
        pythonw_exe = os.path.join(python_dir, "pythonw.exe")
        if not os.path.exists(pythonw_exe):
            pythonw_exe = sys.executable  # fallback
        return f'"{pythonw_exe}" "{run_script}"'


def enable_autostart():
    """Windows başlangıcına programı ekler."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REG_PATH,
            0,
            winreg.KEY_SET_VALUE,
        )
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, _get_executable_path())
        winreg.CloseKey(key)
        return True
    except WindowsError:
        return False


def disable_autostart():
    """Windows başlangıcından programı kaldırır."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REG_PATH,
            0,
            winreg.KEY_SET_VALUE,
        )
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return True  # Zaten kayıtlı değil
    except WindowsError:
        return False


def is_autostart_enabled() -> bool:
    """Otomatik başlatmanın aktif olup olmadığını kontrol eder."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REG_PATH,
            0,
            winreg.KEY_READ,
        )
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False
    except WindowsError:
        return False


def set_autostart(enabled: bool) -> bool:
    """Otomatik başlatmayı açar veya kapatır."""
    if enabled:
        return enable_autostart()
    else:
        return disable_autostart()
