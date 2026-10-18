import ctypes
from ctypes import wintypes
import os
from typing import Tuple

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

class WindowWatcher:
    """
    Tracks foreground window changes and resolves the active process name and window title.
    Equivalent to VoiceOS active-window-listener.exe.
    """
    @staticmethod
    def get_active_window_info() -> Tuple[str, str]:
        """
        Returns (app_name, window_title).
        """
        hwnd = user32.GetForegroundWindow()
        if not hwnd:
            return ("Desktop", "")

        # Get window title
        length = user32.GetWindowTextLengthW(hwnd)
        title = ""
        if length > 0:
            buff = ctypes.create_unicode_buffer(length + 1)
            user32.GetWindowTextW(hwnd, buff, length + 1)
            title = buff.value

        # Get process executable name
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        
        app_name = "Unknown"
        # PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
        h_process = kernel32.OpenProcess(0x1000, False, pid.value)
        if h_process:
            try:
                # QueryFullProcessImageNameW
                buff_size = wintypes.DWORD(1024)
                exe_buff = ctypes.create_unicode_buffer(1024)
                if kernel32.QueryFullProcessImageNameW(h_process, 0, exe_buff, ctypes.byref(buff_size)):
                    app_name = os.path.basename(exe_buff.value)
            finally:
                kernel32.CloseHandle(h_process)

        return (app_name, title)
