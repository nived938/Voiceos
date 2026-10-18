import os
import shutil
import tempfile
from pathlib import Path
import pytest
from core.config import ConfigManager

@pytest.fixture
def temp_config_dir():
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir, ignore_errors=True)

def test_config_defaults(temp_config_dir):
    cfg = ConfigManager(config_dir=temp_config_dir)
    assert cfg.get("gemini.model") == "gemini-3.8-flash"
    assert cfg.get("gemini.omniroute") is True
    assert cfg.get("audio.sample_rate") == 48000
    assert cfg.get("audio.voice_persona") == "Jarvis"
    assert cfg.get("ui.theme") == "black_and_white"
    assert not cfg.is_onboarding_completed

def test_config_set_and_save(temp_config_dir):
    cfg = ConfigManager(config_dir=temp_config_dir)
    cfg.set("profile.first_name", "TestUser")
    cfg.set("audio.voice_persona", "Friday")
    cfg.set_onboarding_completed(True)

    # Re-read
    cfg2 = ConfigManager(config_dir=temp_config_dir)
    assert cfg2.get("profile.first_name") == "TestUser"
    assert cfg2.get("audio.voice_persona") == "Friday"
    assert cfg2.is_onboarding_completed is True

def test_api_key_masking(temp_config_dir):
    cfg = ConfigManager(config_dir=temp_config_dir)
    cfg.set_gemini_api_key("AIzaSyDummySecretKey1234567890")
    masked = cfg.mask_api_key()
    assert masked.startswith("AIza")
    assert masked.endswith("7890")
    assert "Secret" not in masked
