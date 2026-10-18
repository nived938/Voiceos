import ctypes
from ctypes import wintypes
import threading
import time
import logging
from typing import Callable, Dict

logger = logging.getLogger("VoiceOS.Hotkeys")

user32 = ctypes.windll.user32

MOD_ALT = 0x0001
MOD_CONTROL = 0x0002
MOD_SHIFT = 0x0004
MOD_WIN = 0x0008
MOD_NOREPEAT = 0x4000
WM_HOTKEY = 0x0312

class GlobalHotkeyManager:
    """
    Manages global Windows hotkeys using RegisterHotKey in a background thread.
    Equivalent to VoiceOS keyboard-listener.exe.
    """
    def __init__(self):
        self._callbacks: Dict[int, Callable[[], None]] = {}
        self._thread: threading.Thread = None
        self._thread_id: int = 0
        self._running = False
        self._next_id = 1
        self._lock = threading.Lock()

    def register_hotkey(self, modifiers: int, vk: int, callback: Callable[[], None]) -> int:
        with self._lock:
            hk_id = self._next_id
            self._next_id += 1
            self._callbacks[hk_id] = (modifiers | MOD_NOREPEAT, vk, callback)
            return hk_id

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._msg_loop, daemon=True)
        self._thread.start()

    def _msg_loop(self):
        self._thread_id = ctypes.windll.kernel32.GetCurrentThreadId()
        
        # Register all hotkeys in this message loop thread
        active_callbacks = {}
        for hk_id, (mods, vk, cb) in self._callbacks.items():
            res = user32.RegisterHotKey(None, hk_id, mods, vk)
            if res:
                active_callbacks[hk_id] = cb
                logger.info(f"Registered hotkey ID {hk_id} (vk: {hex(vk)}, mods: {hex(mods)})")
            else:
                logger.warning(f"Failed to register hotkey ID {hk_id}")

        msg = wintypes.MSG()
        while self._running:
            # PeekMessage / GetMessage
            res = user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if res <= 0:
                break
            if msg.message == WM_HOTKEY:
                hk_id = msg.wParam
                if hk_id in active_callbacks:
                    try:
                        active_callbacks[hk_id]()
                    except Exception as e:
                        logger.error(f"Error in hotkey callback {hk_id}: {e}")
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))

        # Unregister hotkeys
        for hk_id in active_callbacks:
            user32.UnregisterHotKey(None, hk_id)

    def stop(self):
        self._running = False
        if self._thread_id:
            user32.PostThreadMessageW(self._thread_id, 0x0012, 0, 0) # WM_QUIT
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=1.0)
