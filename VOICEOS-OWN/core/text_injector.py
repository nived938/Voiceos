import time
import ctypes
import pyperclip
import logging

logger = logging.getLogger("VoiceOS.TextInjector")

user32 = ctypes.windll.user32

# Key constants
VK_CONTROL = 0x11
VK_V = 0x56
KEYEVENTF_KEYUP = 0x0002

class TextInjector:
    """
    Injects transcribed text directly into the focused application window.
    Equivalent to VoiceOS text-injector.exe.
    """
    @staticmethod
    def inject_text(text: str, restore_clipboard: bool = True):
        if not text:
            return

        old_clipboard = None
        if restore_clipboard:
            try:
                old_clipboard = pyperclip.paste()
            except Exception:
                old_clipboard = None

        try:
            # Place new text in clipboard
            pyperclip.copy(text)
            time.sleep(0.05)

            # Simulate Ctrl + V
            # Press Ctrl
            user32.keybd_event(VK_CONTROL, 0, 0, 0)
            # Press V
            user32.keybd_event(VK_V, 0, 0, 0)
            time.sleep(0.02)
            # Release V
            user32.keybd_event(VK_V, 0, KEYEVENTF_KEYUP, 0)
            # Release Ctrl
            user32.keybd_event(VK_CONTROL, 0, KEYEVENTF_KEYUP, 0)

            time.sleep(0.1)
        except Exception as e:
            logger.error(f"Failed to inject text: {e}")
        finally:
            # Restore previous clipboard after a brief delay
            if restore_clipboard and old_clipboard is not None:
                def _restore():
                    time.sleep(0.3)
                    try:
                        pyperclip.copy(old_clipboard)
                    except Exception:
                        pass
                import threading
                threading.Thread(target=_restore, daemon=True).start()
