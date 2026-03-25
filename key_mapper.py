"""
key_mapper.py - F1-F8 tuslarini multimedya kontrol tuslarina donusturur.

Windows keybd_event API ile medya tuslarini simule eder.
"""

import ctypes
import queue
import threading
import time

import keyboard

# --- Windows API Tanimlari ---
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002

# Virtual Key Codes - Multimedya Tuslari
VK_MEDIA_CODES = {
    "mute": 0xAD,
    "volume_down": 0xAE,
    "volume_up": 0xAF,
    "next_track": 0xB0,
    "prev_track": 0xB1,
    "stop": 0xB2,
    "play_pause": 0xB3,
    "launch_media": 0xB5,
}

# Kullanicı dostu isimler (GUI icin)
MEDIA_ACTION_NAMES = {
    "mute": "Sessiz (Mute)",
    "volume_down": "Ses Azalt",
    "volume_up": "Ses Artir",
    "next_track": "Sonraki Parca",
    "prev_track": "Onceki Parca",
    "stop": "Durdur",
    "play_pause": "Oynat/Duraklat",
    "launch_media": "Medya Oynatici Ac",
}

# Ters esleme: GUI isimlerinden action key'e
NAME_TO_ACTION = {v: k for k, v in MEDIA_ACTION_NAMES.items()}

# F tuslari listesi
F_KEYS = ["f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8"]


def send_media_key(vk_code: int):
    """Windows keybd_event API ile bir medya tusu simule eder (basma + birakma)."""
    ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY, 0)
    time.sleep(0.05)
    ctypes.windll.user32.keybd_event(
        vk_code,
        0,
        KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP,
        0,
    )


class KeyMapper:
    """F1-F8 tuslarini dinleyip multimedya fonksiyonlarina yonlendiren sinif."""

    DEBOUNCE_TIME = 0.15

    def __init__(self, mappings: dict):
        self.mappings = mappings
        self._hooks = []
        self._running = False
        self._lock = threading.Lock()
        self._last_press = {}
        self._media_queue = queue.SimpleQueue()
        self._worker_stop = threading.Event()
        self._worker_thread = None

    def _media_worker(self):
        """Medya tusa basma islerini keyboard callback disinda calistirir."""
        while not self._worker_stop.is_set():
            try:
                vk_code = self._media_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if vk_code is None:
                break
            send_media_key(vk_code)

    def _ensure_worker(self):
        if self._worker_thread and self._worker_thread.is_alive():
            return

        self._worker_stop.clear()
        self._worker_thread = threading.Thread(
            target=self._media_worker,
            name="MiniKeyCtrlMediaWorker",
            daemon=True,
        )
        self._worker_thread.start()

    def _handle_key(self, f_key: str):
        """Bir F tusuna basildiginda cagrilir (debounce ile)."""
        now = time.monotonic()
        last = self._last_press.get(f_key, 0.0)

        if now - last < self.DEBOUNCE_TIME:
            return

        self._last_press[f_key] = now

        action = self.mappings.get(f_key)
        vk_code = VK_MEDIA_CODES.get(action)
        if vk_code is not None:
            self._media_queue.put(vk_code)

    def start(self):
        """Tus dinlemeyi baslatir."""
        with self._lock:
            if self._running:
                return

            self._running = True
            self._last_press.clear()
            self._ensure_worker()

            for f_key in F_KEYS:
                if f_key in self.mappings:
                    hook = keyboard.on_press_key(
                        f_key,
                        lambda e, fk=f_key: self._handle_key(fk),
                        suppress=True,
                    )
                    self._hooks.append(hook)

    def stop(self):
        """Bu sinifin kaydettigi tum hook'lari kaldirir."""
        with self._lock:
            if not self._running:
                return

            self._running = False

            for hook in self._hooks:
                keyboard.unhook(hook)
            self._hooks.clear()

            self._worker_stop.set()
            self._media_queue.put(None)
            worker = self._worker_thread
            self._worker_thread = None

        if worker and worker.is_alive():
            worker.join(timeout=0.2)

    def reload(self, new_mappings: dict):
        """Yeni eslemelerle yeniden baslatir."""
        self.stop()
        self.mappings = new_mappings
        self.start()
