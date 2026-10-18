import time
import ctypes
import pyperclip
import logging

logger = logging.getLogger("VoiceOS.SelectionReader")

user32 = ctypes.windll.user32
VK_CONTROL = 0x11
VK_C = 0x43
KEYEVENTF_KEYUP = 0x0002

class SelectionReader:
    """
    Reads currently selected text from active application.
    Equivalent to VoiceOS selection-reader.exe.
    """
    @staticmethod
    def get_selected_text(max_length: int = 10000) -> str:
        old_clipboard = None
        try:
            old_clipboard = pyperclip.paste()
        except Exception:
            pass

        try:
            # Clear clipboard temporarily
            pyperclip.copy("")
            time.sleep(0.02)

            # Send Ctrl+C
            user32.keybd_event(VK_CONTROL, 0, 0, 0)
            user32.keybd_event(VK_C, 0, 0, 0)
            time.sleep(0.02)
            user32.keybd_event(VK_C, 0, KEYEVENTF_KEYUP, 0)
            user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

            # Wait for text to arrive in clipboard
            time.sleep(0.1)
            selected_text = pyperclip.paste()
            if selected_text:
                return selected_text[:max_length]
        except Exception as e:
            logger.error(f"Error reading selection: {e}")
        finally:
            if old_clipboard is not None:
                try:
                    pyperclip.copy(old_clipboard)
                except Exception:
                    pass

        return ""
