"""
key_mapper.py - F1-F8 tuşlarını multimedya kontrol tuşlarına dönüştürür.

Windows keybd_event API ile medya tuşlarını simüle eder.
"""

import ctypes
import keyboard
import threading
import time

# --- Windows API Tanımları ---
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002

# Virtual Key Codes - Multimedya Tuşları
VK_MEDIA_CODES = {
    "mute":          0xAD,  # VK_VOLUME_MUTE
    "volume_down":   0xAE,  # VK_VOLUME_DOWN
    "volume_up":     0xAF,  # VK_VOLUME_UP
    "next_track":    0xB0,  # VK_MEDIA_NEXT_TRACK
    "prev_track":    0xB1,  # VK_MEDIA_PREV_TRACK
    "stop":          0xB2,  # VK_MEDIA_STOP
    "play_pause":    0xB3,  # VK_MEDIA_PLAY_PAUSE
    "launch_media":  0xB5,  # VK_LAUNCH_MEDIA_SELECT
}

# Kullanıcı dostu isimler (GUI için)
MEDIA_ACTION_NAMES = {
    "mute":          "🔇 Sessiz (Mute)",
    "volume_down":   "🔉 Ses Azalt",
    "volume_up":     "🔊 Ses Artır",
    "next_track":    "⏭ Sonraki Parça",
    "prev_track":    "⏮ Önceki Parça",
    "stop":          "⏹ Durdur",
    "play_pause":    "⏯ Oynat/Duraklat",
    "launch_media":  "🎵 Medya Oynatıcı Aç",
}

# Ters eşleme: GUI isimlerinden action key'e
NAME_TO_ACTION = {v: k for k, v in MEDIA_ACTION_NAMES.items()}

# F tuşları listesi
F_KEYS = ["f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8"]


def send_media_key(vk_code: int):
    """Windows keybd_event API ile bir medya tuşu simüle eder (basma + bırakma)."""
    # Key Down
    ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY, 0)
    time.sleep(0.05)
    # Key Up
    ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP, 0)


class KeyMapper:
    """F1-F8 tuşlarını dinleyip multimedya fonksiyonlarına yönlendiren sınıf."""

    # Tuş tekrarı arasındaki minimum süre (saniye)
    DEBOUNCE_TIME = 0.15

    def __init__(self, mappings: dict):
        """
        Args:
            mappings: {"f1": "mute", "f2": "volume_down", ...} şeklinde eşleme sözlüğü
        """
        self.mappings = mappings
        self._hooks = []
        self._running = False
        self._lock = threading.Lock()
        self._last_press = {}  # Her tuşun son basılma zamanı

    def _handle_key(self, f_key: str):
        """Bir F tuşuna basıldığında çağrılır (debounce ile)."""
        now = time.monotonic()
        last = self._last_press.get(f_key, 0)

        # Çok hızlı tekrarları yoksay
        if now - last < self.DEBOUNCE_TIME:
            return

        self._last_press[f_key] = now

        action = self.mappings.get(f_key)
        if action and action in VK_MEDIA_CODES:
            vk = VK_MEDIA_CODES[action]
            send_media_key(vk)

    def start(self):
        """Tuş dinlemeyi başlatır."""
        with self._lock:
            if self._running:
                return
            self._running = True
            self._last_press.clear()
            self._hooks.clear()

            for f_key in F_KEYS:
                if f_key in self.mappings:
                    hook = keyboard.on_press_key(
                        f_key,
                        lambda e, fk=f_key: self._handle_key(fk),
                        suppress=True,
                    )
                    self._hooks.append(hook)

    def stop(self):
        """Bu uygulamaya ait tüm hook'ları kaldırır."""
        with self._lock:
            if not self._running:
                return
            self._running = False
            for hook in self._hooks:
                keyboard.unhook(hook)
            self._hooks.clear()

    def reload(self, new_mappings: dict):
        """Yeni eşlemelerle yeniden başlatır."""
        self.stop()
        self.mappings = new_mappings
        self.start()
