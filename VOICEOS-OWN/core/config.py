import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger("VoiceOS.Config")

class ConfigManager:
    """
    Manages persistent configuration and secure API key storage for VoiceOS-Own.
    """
    DEFAULT_CONFIG = {
        "gemini": {
            "model": "gemini-2.5-flash",
            "temperature": 0.7,
            "max_output_tokens": 2048,
            "streaming": True,
            "timeout_seconds": 30,
            "omniroute": True,
            "fallback_models": [
                "gemini-2.5-flash",
                "gemini-2.5-pro",
                "gemini-1.5-flash",
                "gemini-1.5-pro"
            ]
        },
        "audio": {
            "mic_device": "default",
            "sample_rate": 48000,
            "channels": 1,
            "tts_voice": "default",
            "tts_speed": 1.2,
            "voice_persona": "Jarvis",
            "auto_mute_when_dictating": True,
            "audio_ducking_enabled": True
        },
        "shortcuts": {
            "dictation_hotkey": "Ctrl+Shift",
            "agent_hotkey": "Ctrl+Alt",
            "handsfree_hotkey": "Ctrl+Shift+Space",
            "toggle_notch_hotkey": "Alt+`"
        },
        "ui": {
            "theme": "black_and_white",
            "notch_enabled": True,
            "notch_hover_peek": True,
            "close_to_tray": True,
            "onboarding_completed": False
        },
        "profile": {
            "first_name": "User",
            "last_name": "",
            "default_language": "en"
        }
    }

    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            appdata = os.getenv("APPDATA")
            if appdata:
                self.config_dir = Path(appdata) / "VoiceOS-Own"
            else:
                self.config_dir = Path.home() / ".voiceos-own"
        else:
            self.config_dir = Path(config_dir)

        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.config_file = self.config_dir / "config.json"
        self._config: Dict[str, Any] = {}
        self._load_env()
        self.load()

    def _load_env(self):
        """Loads environment variables from .env if present."""
        env_paths = [
            Path.cwd() / ".env",
            Path(__file__).resolve().parent.parent / ".env",
            self.config_dir / ".env"
        ]
        for p in env_paths:
            if p.exists():
                try:
                    from dotenv import load_dotenv
                    load_dotenv(p)
                    break
                except ImportError:
                    pass

    def load(self):
        """Loads configuration from disk, falling back to defaults."""
        if self.config_file.exists():
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._config = self._deep_merge(self.DEFAULT_CONFIG.copy(), data)
            except Exception as e:
                logger.error(f"Error loading config file: {e}")
                self._config = self.DEFAULT_CONFIG.copy()
        else:
            self._config = self.DEFAULT_CONFIG.copy()
            self.save()

    def save(self):
        """Saves current configuration to disk."""
        try:
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving config file: {e}")

    def _deep_merge(self, base: dict, override: dict) -> dict:
        for k, v in override.items():
            if isinstance(v, dict) and k in base and isinstance(base[k], dict):
                base[k] = self._deep_merge(base[k], v)
            else:
                base[k] = v
        return base

    def get(self, key_path: str, default: Any = None) -> Any:
        """Retrieves a nested setting using dot notation, e.g. 'gemini.model'."""
        keys = key_path.split(".")
        val = self._config
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return default
        return val

    def set(self, key_path: str, value: Any, auto_save: bool = True):
        """Sets a nested setting using dot notation, e.g. 'ui.theme'."""
        keys = key_path.split(".")
        curr = self._config
        for k in keys[:-1]:
            if k not in curr or not isinstance(curr[k], dict):
                curr[k] = {}
            curr = curr[k]
        curr[keys[-1]] = value
        if auto_save:
            self.save()

    def get_gemini_api_key(self) -> str:
        """
        Retrieves the Gemini API key from environment or local secure config.
        Priority:
        1. GEMINI_API_KEY environment variable
        2. Config stored key
        """
        env_key = os.getenv("GEMINI_API_KEY", "").strip()
        if env_key:
            return env_key
        return self.get("gemini.api_key", "").strip()

    def set_gemini_api_key(self, api_key: str):
        """Stores the Gemini API key in configuration."""
        clean_key = api_key.strip()
        self.set("gemini.api_key", clean_key)
        os.environ["GEMINI_API_KEY"] = clean_key

    def mask_api_key(self, key: Optional[str] = None) -> str:
        """Returns a masked version of the key for safe UI display (e.g. AIza...4fG9)."""
        actual_key = key if key is not None else self.get_gemini_api_key()
        if not actual_key:
            return "No key configured"
        if len(actual_key) <= 8:
            return "••••••••"
        return f"{actual_key[:4]}••••••••{actual_key[-4:]}"

    @property
    def is_onboarding_completed(self) -> bool:
        return self.get("ui.onboarding_completed", False)

    def set_onboarding_completed(self, completed: bool = True):
        self.set("ui.onboarding_completed", completed)

    @property
    def database_path(self) -> Path:
        return self.config_dir / "voiceos_own.db"
