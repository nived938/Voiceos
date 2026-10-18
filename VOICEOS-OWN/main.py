import sys
import os
import logging
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt

from core.config import ConfigManager
from core.database import DatabaseManager
from core.hotkeys import GlobalHotkeyManager, MOD_CONTROL, MOD_SHIFT, MOD_ALT
from ai.gemini_provider import GeminiProvider
from audio.audio_capture import AudioCaptureService
from audio.stt_engine import STTEngine
from audio.tts_engine import TTSEngine
from audio.audio_duck import AudioDucker
from ui.main_window import MainWindow
from ui.tray_icon import SystemTrayManager

logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s"
)
logger = logging.getLogger("VoiceOS.Main")

def main():
    logger.info("Initializing VoiceOS-Own Desktop Application...")
    app = QApplication(sys.argv)
    app.setApplicationName("VoiceOS")
    app.setOrganizationName("VoiceOS-Own")
    app.setQuitOnLastWindowClosed(False)

    # 1. Core Config & Database
    config = ConfigManager()
    db = DatabaseManager(config.database_path)

    # 2. AI Provider with Omniroute Failover
    gemini_key = config.get_gemini_api_key()
    gemini_model = config.get("gemini.model", "gemini-2.5-flash")
    omniroute = config.get("gemini.omniroute", True)
    ai = GeminiProvider(api_key=gemini_key, model_name=gemini_model, omniroute=omniroute)

    # 3. Audio & Speech Pipeline
    audio = AudioCaptureService(
        sample_rate=config.get("audio.sample_rate", 48000),
        channels=config.get("audio.channels", 1)
    )
    stt = STTEngine(language=config.get("profile.default_language", "en-US"))
    persona = config.get("audio.voice_persona", "Jarvis")
    tts = TTSEngine(speed_multiplier=config.get("audio.tts_speed", 1.2), persona=persona)
    ducker = AudioDucker()

    # 4. Main Window & UI
    main_window = MainWindow(
        config_manager=config,
        db_manager=db,
        ai_provider=ai,
        audio_capture=audio,
        stt_engine=stt,
        tts_engine=tts,
        ducker=ducker
    )

    # 5. System Tray
    tray = SystemTrayManager(main_window)
    tray.show()

    # 6. Global Hotkeys
    hotkeys = GlobalHotkeyManager()
    # Hotkey 1: Dictation (Ctrl + Shift + D / VK_D = 0x44)
    hotkeys.register_hotkey(MOD_CONTROL | MOD_SHIFT, 0x44, main_window.toggle_dictation)
    # Hotkey 2: Agent Mode (Ctrl + Alt + A / VK_A = 0x41)
    hotkeys.register_hotkey(MOD_CONTROL | MOD_ALT, 0x41, main_window.toggle_agent)
    # Hotkey 3: Notch toggle (Alt + ` / VK_OEM_3 = 0xC0)
    hotkeys.register_hotkey(MOD_ALT, 0xC0, main_window.toggle_notch)
    hotkeys.start()

    main_window.show()

    logger.info("VoiceOS-Own successfully launched.")
    exit_code = app.exec()

    # Cleanup
    hotkeys.stop()
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
