"""
key_mapper.py - Media key mapping core.
"""

import ctypes
import queue
import threading
import time

# Windows key event flags
KEYEVENTF_EXTENDEDKEY = 0x0001
KEYEVENTF_KEYUP = 0x0002

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

F_KEYS = ["f1", "f2", "f3", "f4", "f5", "f6", "f7", "f8"]


def send_media_key(vk_code: int):
    """Simulate a media key press using the Windows API."""
    ctypes.windll.user32.keybd_event(vk_code, 0, KEYEVENTF_EXTENDEDKEY, 0)
    time.sleep(0.05)
    ctypes.windll.user32.keybd_event(
        vk_code,
        0,
        KEYEVENTF_EXTENDEDKEY | KEYEVENTF_KEYUP,
        0,
    )


class KeyMapper:
    """Maps logical F-key names to media actions."""

    DEBOUNCE_TIME = 0.15

    def __init__(self, mappings: dict):
        self.mappings = dict(mappings)
        self._last_press = {}
        self._media_queue = queue.SimpleQueue()
        self._worker_stop = threading.Event()
        self._worker_thread = None
        self._lock = threading.Lock()

    def _media_worker(self):
        while not self._worker_stop.is_set():
            try:
                vk_code = self._media_queue.get(timeout=0.1)
            except queue.Empty:
                continue

            if vk_code is None:
                break
            send_media_key(vk_code)

    def start(self):
        with self._lock:
            if self._worker_thread and self._worker_thread.is_alive():
                return

            self._worker_stop.clear()
            self._worker_thread = threading.Thread(
                target=self._media_worker,
                name="MiniKeyCtrlMediaWorker",
                daemon=True,
            )
            self._worker_thread.start()
            self._last_press.clear()

    def stop(self):
        with self._lock:
            worker = self._worker_thread
            if worker is None:
                return

            self._worker_thread = None
            self._worker_stop.set()
            self._media_queue.put(None)

        if worker.is_alive():
            worker.join(timeout=0.2)

    def reload(self, new_mappings: dict):
        with self._lock:
            self.mappings = dict(new_mappings)
            self._last_press.clear()

    def trigger(self, f_key: str, pressed: bool = True) -> bool:
        """Queue the mapped media action for a logical F-key."""
        if not pressed:
            return False

        now = time.monotonic()
        last = self._last_press.get(f_key, 0.0)
        if now - last < self.DEBOUNCE_TIME:
            return False

        action = self.mappings.get(f_key)
        vk_code = VK_MEDIA_CODES.get(action)
        if vk_code is None:
            return False

        self._last_press[f_key] = now
        self._media_queue.put(vk_code)
        return True
