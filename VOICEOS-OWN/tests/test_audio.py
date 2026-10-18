import pytest
from audio.stt_engine import STTEngine
from audio.tts_engine import TTSEngine
from audio.audio_capture import AudioCaptureService

def test_stt_custom_vocabulary_replacement():
    engine = STTEngine()
    raw_text = "hello nived how is kubernetes today"
    custom_words = ["Nived", "Kubernetes"]
    processed = engine._apply_custom_vocabulary(raw_text, custom_words)
    assert "Nived" in processed
    assert "Kubernetes" in processed

def test_tts_initialization_and_personas():
    tts = TTSEngine(speed_multiplier=1.2, persona="Jarvis")
    assert tts.speed_multiplier == 1.2
    assert tts.persona == "Jarvis"
    assert not tts.is_speaking

    # Test all 4 required personas
    for persona in ["Jarvis", "Friday", "Edith", "Ultron"]:
        tts.set_persona(persona)
        assert tts.persona == persona
        assert persona in TTSEngine.PERSONAS

    # Stop safety test
    tts.stop()
    assert not tts.is_speaking

def test_audio_capture_initialization():
    cap = AudioCaptureService(sample_rate=16000, channels=1)
    assert cap.sample_rate == 16000
    assert not cap.is_recording
    devices = cap.get_devices()
    assert isinstance(devices, list)
