"""
device_backend.py - Device-specific keyboard remapping via the Interception driver.
"""

from __future__ import annotations

import ctypes
import re
import threading
import time
from ctypes import wintypes

from key_mapper import F_KEYS, KeyMapper

GENERIC_READ = 0x80000000
OPEN_EXISTING = 3
WAIT_TIMEOUT = 0x00000102
INFINITE = 0xFFFFFFFF

IOCTL_SET_EVENT = 0x222040
IOCTL_SET_FILTER = 0x222010
IOCTL_READ = 0x222100
IOCTL_WRITE = 0x222080
IOCTL_GET_HARDWARE_ID = 0x222200

INTERCEPTION_MAX_KEYBOARD = 10
INTERCEPTION_FILTER_KEY_ALL = 0xFFFF
INTERCEPTION_FILTER_KEY_NONE = 0x0000
INTERCEPTION_FILTER_KEY_DOWN = 0x0001
INTERCEPTION_FILTER_KEY_DOWN_UP = 0x0003
INTERCEPTION_KEY_UP = 0x01
MAPVK_VSC_TO_VK = 1

VK_TO_F_KEY = {
    0x70: "f1",
    0x71: "f2",
    0x72: "f3",
    0x73: "f4",
    0x74: "f5",
    0x75: "f6",
    0x76: "f7",
    0x77: "f8",
}

INVALID_HANDLE_VALUE = ctypes.c_void_p(-1).value

kernel32 = ctypes.windll.kernel32
user32 = ctypes.windll.user32

kernel32.CreateFileW.argtypes = [
    wintypes.LPCWSTR,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.DWORD,
    wintypes.DWORD,
    wintypes.HANDLE,
]
kernel32.CreateFileW.restype = wintypes.HANDLE
kernel32.CreateEventW.argtypes = [wintypes.LPVOID, wintypes.BOOL, wintypes.BOOL, wintypes.LPCWSTR]
kernel32.CreateEventW.restype = wintypes.HANDLE
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]
kernel32.CloseHandle.restype = wintypes.BOOL
kernel32.DeviceIoControl.argtypes = [
    wintypes.HANDLE,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.DWORD,
    wintypes.LPVOID,
    wintypes.DWORD,
    ctypes.POINTER(wintypes.DWORD),
    wintypes.LPVOID,
]
kernel32.DeviceIoControl.restype = wintypes.BOOL
kernel32.WaitForMultipleObjects.argtypes = [
    wintypes.DWORD,
    ctypes.POINTER(wintypes.HANDLE),
    wintypes.BOOL,
    wintypes.DWORD,
]
kernel32.WaitForMultipleObjects.restype = wintypes.DWORD
user32.MapVirtualKeyW.argtypes = [wintypes.UINT, wintypes.UINT]
user32.MapVirtualKeyW.restype = wintypes.UINT


class InterceptionError(RuntimeError):
    """Raised when the Interception driver cannot be accessed."""


class InterceptionKeyStroke(ctypes.Structure):
    _fields_ = [
        ("unit_id", wintypes.USHORT),
        ("code", wintypes.USHORT),
        ("state", wintypes.USHORT),
        ("reserved", wintypes.USHORT),
        ("information", wintypes.ULONG),
    ]


class Handle:
    def __init__(self, value):
        self.value = value

    def close(self):
        if self.value:
            kernel32.CloseHandle(self.value)
            self.value = 0


def format_device_name(hardware_id: str) -> str:
    match = re.search(r"VID_([0-9A-F]{4}).*PID_([0-9A-F]{4})", hardware_id, re.IGNORECASE)
    if match:
        return f"Klavye VID_{match.group(1).upper()} PID_{match.group(2).upper()}"
    tail = hardware_id.split("#")[-1].strip()
    if tail:
        return f"Klavye {tail}"
    return "Tanitilan Klavye"


def default_config() -> dict:
    return {
        "mappings": {
            "f1": "mute",
            "f2": "volume_down",
            "f3": "volume_up",
            "f4": "prev_track",
            "f5": "play_pause",
            "f6": "next_track",
            "f7": "stop",
            "f8": "launch_media",
        },
        "autostart": True,
        "target_device": None,
    }


class InterceptionDevice:
    """Represents one keyboard device handle exposed by the Interception driver."""

    def __init__(self, device_number: int):
        path = f"\\\\.\\interception{device_number - 1:02}"
        file_handle = kernel32.CreateFileW(
            path,
            GENERIC_READ,
            0,
            None,
            OPEN_EXISTING,
            0,
            None,
        )
        if file_handle in (0, INVALID_HANDLE_VALUE):
            raise ctypes.WinError()

        event_handle = kernel32.CreateEventW(None, False, False, None)
        if not event_handle:
            kernel32.CloseHandle(file_handle)
            raise ctypes.WinError()

        self.device_number = device_number
        self.device = Handle(file_handle)
        self.event = Handle(event_handle)
        self.stroke = InterceptionKeyStroke()
        self.hardware_id = None

        event_buffer = (wintypes.HANDLE * 2)(self.event.value)
        self._device_io_control(IOCTL_SET_EVENT, in_buffer=event_buffer)
        self.set_filter(INTERCEPTION_FILTER_KEY_NONE)

    def close(self):
        self.device.close()
        self.event.close()

    def receive(self) -> bool:
        return self._device_io_control(IOCTL_READ, out_buffer=self.stroke) > 0

    def send(self, stroke: InterceptionKeyStroke | None = None) -> bool:
        return self._device_io_control(IOCTL_WRITE, in_buffer=stroke or self.stroke) > 0

    def set_filter(self, keyboard_filter: int):
        filter_value = wintypes.USHORT(keyboard_filter)
        self._device_io_control(IOCTL_SET_FILTER, in_buffer=filter_value)

    def get_hardware_id(self, refresh: bool = False) -> str | None:
        if self.hardware_id and not refresh:
            return self.hardware_id

        hardware_id = ctypes.create_unicode_buffer(512)
        if self._device_io_control(IOCTL_GET_HARDWARE_ID, out_buffer=hardware_id) > 0:
            self.hardware_id = hardware_id.value
            return self.hardware_id
        self.hardware_id = None
        return None

    def _device_io_control(self, ioctl_code: int, in_buffer=None, out_buffer=None) -> int:
        bytes_returned = wintypes.DWORD()

        in_ptr = None
        in_size = 0
        if in_buffer is not None:
            in_ptr = ctypes.byref(in_buffer)
            in_size = ctypes.sizeof(in_buffer)

        out_ptr = None
        out_size = 0
        if out_buffer is not None:
            out_ptr = ctypes.byref(out_buffer)
            out_size = ctypes.sizeof(out_buffer)

        ok = kernel32.DeviceIoControl(
            self.device.value,
            ioctl_code,
            in_ptr,
            in_size,
            out_ptr,
            out_size,
            ctypes.byref(bytes_returned),
            None,
        )
        if not ok:
            return 0
        return bytes_returned.value


class InterceptionContext:
    """Manages all keyboard handles and waits for the next event."""

    def __init__(self):
        self.devices = []
        try:
            for index in range(1, INTERCEPTION_MAX_KEYBOARD + 1):
                self.devices.append(InterceptionDevice(index))
        except Exception:
            for device in self.devices:
                device.close()
            raise
        self._events = (wintypes.HANDLE * INTERCEPTION_MAX_KEYBOARD)(*[device.event.value for device in self.devices])

    def close(self):
        for device in self.devices:
            device.close()

    def enumerate_keyboards(self) -> list[dict]:
        result = []
        for device in self.devices:
            hardware_id = device.get_hardware_id(refresh=True)
            if hardware_id:
                result.append(
                    {
                        "device": device.device_number,
                        "id": hardware_id,
                        "display_name": format_device_name(hardware_id),
                        "backend": "interception",
                    }
                )
        return result

    def wait_for_device(self, timeout_ms: int) -> InterceptionDevice | None:
        wait_result = kernel32.WaitForMultipleObjects(
            len(self.devices),
            self._events,
            False,
            timeout_ms,
        )
        if wait_result == WAIT_TIMEOUT:
            return None
        if wait_result < 0 or wait_result >= len(self.devices):
            return None
        return self.devices[wait_result]


class DeviceInputBackend:
    """Interception-backed device filter and remapper."""

    def __init__(self, key_mapper: KeyMapper, status_callback=None):
        self.key_mapper = key_mapper
        self.status_callback = status_callback
        self.context = None
        self.target_device = None
        self._devices_by_hardware_id = {}
        self._thread = None
        self._stop_event = threading.Event()
        self._capture_lock = threading.Lock()
        self._capture_active = False
        self._capture_deadline = 0.0
        self._captured_device = None
        self._last_status = None
        self._driver_error = None
        self._map_virtual_key = user32.MapVirtualKeyW
        self._filter_mode = "normal"

    def start(self, config: dict):
        self.key_mapper.reload(config.get("mappings", {}))
        self.target_device = config.get("target_device")
        self.key_mapper.start()

        try:
            self.context = InterceptionContext()
        except OSError as exc:
            self._driver_error = f"Interception driver hazir degil: {exc}"
            self._publish_status()
            return
        except Exception as exc:
            self._driver_error = f"Interception driver hazir degil: {exc}"
            self._publish_status()
            return

        self._driver_error = None
        self._refresh_devices()
        self._apply_normal_filters()
        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._event_loop,
            name="MiniKeyCtrlInterception",
            daemon=True,
        )
        self._thread.start()
        self._publish_status()

    def stop(self):
        self._stop_event.set()
        thread = self._thread
        self._thread = None
        if thread and thread.is_alive():
            thread.join(timeout=0.5)
        if self.context:
            self.context.close()
            self.context = None
        self.key_mapper.stop()

    def reload_config(self, config: dict):
        self.target_device = config.get("target_device")
        self.key_mapper.reload(config.get("mappings", {}))
        if self.context:
            self._refresh_devices()
            if self._filter_mode == "capture":
                self._apply_capture_filters()
            else:
                self._apply_normal_filters()
        self._publish_status()

    def begin_device_capture(self, timeout_seconds: int = 10) -> bool:
        if not self.context:
            return False

        with self._capture_lock:
            self._captured_device = None
            self._capture_active = True
            self._capture_deadline = time.monotonic() + timeout_seconds
        self._apply_capture_filters()
        return True

    def get_capture_snapshot(self) -> dict:
        timeout_reached = False
        with self._capture_lock:
            if self._capture_active and time.monotonic() >= self._capture_deadline:
                self._capture_active = False
                timeout_reached = True

            snapshot = {
                "active": self._capture_active,
                "captured_device": self._captured_device,
                "remaining_seconds": max(0, int(self._capture_deadline - time.monotonic())) if self._capture_active else 0,
            }
        if timeout_reached:
            self._apply_normal_filters()
        return snapshot

    def consume_captured_device(self) -> dict | None:
        with self._capture_lock:
            device = self._captured_device
            self._captured_device = None
            return device

    def get_status(self) -> dict:
        return self._build_status()

    def get_driver_error(self) -> str | None:
        return self._driver_error

    def _event_loop(self):
        refresh_at = 0.0
        while not self._stop_event.is_set():
            if not self.context:
                break

            device = self.context.wait_for_device(timeout_ms=250)
            now = time.monotonic()
            if device is None:
                if now >= refresh_at:
                    self._refresh_devices()
                    self._publish_status()
                    refresh_at = now + 2.0
                continue

            if not device.receive():
                continue

            hardware_id = device.get_hardware_id()
            if hardware_id:
                self._devices_by_hardware_id[hardware_id] = {
                    "device": device.device_number,
                    "id": hardware_id,
                    "display_name": format_device_name(hardware_id),
                    "backend": "interception",
                }

            self._capture_device_if_needed(hardware_id)

            if self._should_remap_event(hardware_id, device.stroke):
                continue

            device.send()

    def _refresh_devices(self):
        if not self.context:
            self._devices_by_hardware_id = {}
            return
        self._devices_by_hardware_id = {
            device["id"]: device for device in self.context.enumerate_keyboards()
        }

    def _capture_device_if_needed(self, hardware_id: str | None):
        if not hardware_id:
            return

        with self._capture_lock:
            if not self._capture_active:
                return
            self._captured_device = {
                "id": hardware_id,
                "display_name": format_device_name(hardware_id),
                "backend": "interception",
            }
            self._capture_active = False
        self._apply_normal_filters()

    def _should_remap_event(self, hardware_id: str | None, stroke: InterceptionKeyStroke) -> bool:
        target_device_id = (self.target_device or {}).get("id")
        if not target_device_id or hardware_id != target_device_id:
            return False

        f_key = self._stroke_to_f_key(stroke)
        if f_key not in F_KEYS:
            return False

        if f_key not in self.key_mapper.mappings:
            return False

        if not bool(stroke.state & INTERCEPTION_KEY_UP):
            self.key_mapper.trigger(f_key, pressed=True)
        return True

    def _stroke_to_f_key(self, stroke: InterceptionKeyStroke) -> str | None:
        vk_code = self._map_virtual_key(stroke.code, MAPVK_VSC_TO_VK)
        return VK_TO_F_KEY.get(vk_code)

    def _build_status(self) -> dict:
        target = self.target_device
        if self._driver_error:
            return {
                "driver_ready": False,
                "configured": bool(target),
                "available": False,
                "message": self._driver_error,
                "device": target,
            }

        if not target:
            return {
                "driver_ready": True,
                "configured": False,
                "available": False,
                "message": "Tanitilan cihaz yok",
                "device": None,
            }

        available = target["id"] in self._devices_by_hardware_id
        if available:
            return {
                "driver_ready": True,
                "configured": True,
                "available": True,
                "message": f"Aktif cihaz: {target['display_name']}",
                "device": self._devices_by_hardware_id[target["id"]],
            }

        return {
            "driver_ready": True,
            "configured": True,
            "available": False,
            "message": f"Cihaz bulunamadi: {target['display_name']}",
            "device": target,
        }

    def _apply_capture_filters(self):
        if not self.context:
            return
        self._filter_mode = "capture"
        for device in self.context.devices:
            device.set_filter(INTERCEPTION_FILTER_KEY_DOWN)

    def _apply_normal_filters(self):
        if not self.context:
            return

        self._filter_mode = "normal"
        target_id = (self.target_device or {}).get("id")
        for device in self.context.devices:
            hardware_id = device.get_hardware_id()
            if target_id and hardware_id == target_id:
                device.set_filter(INTERCEPTION_FILTER_KEY_DOWN_UP)
            else:
                device.set_filter(INTERCEPTION_FILTER_KEY_NONE)

    def _publish_status(self):
        status = self._build_status()
        if status == self._last_status:
            return
        self._last_status = status
        if self.status_callback:
            try:
                self.status_callback(status)
            except Exception:
                pass
