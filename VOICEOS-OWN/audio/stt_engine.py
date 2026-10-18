import os
import re
import logging
import speech_recognition as sr
from typing import List, Optional

logger = logging.getLogger("VoiceOS.STT")

class STTEngine:
    """
    Speech-to-Text transcription engine with custom vocabulary injection.
    """
    def __init__(self, language: str = "en-US"):
        self.language = language
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True

    def transcribe_file(self, wav_path: str, custom_words: Optional[List[str]] = None) -> str:
        """
        Transcribes a WAV file into text, applying custom dictionary vocabulary boosting.
        """
        if not wav_path or not os.path.exists(wav_path):
            return ""

        text = ""
        try:
            with sr.AudioFile(wav_path) as source:
                audio = self.recognizer.record(source)

            # Recognize using Google Speech Recognition
            text = self.recognizer.recognize_google(audio, language=self.language)
            logger.info(f"Raw transcription: '{text}'")

            # Apply custom dictionary post-processing
            if custom_words and text:
                text = self._apply_custom_vocabulary(text, custom_words)

        except sr.UnknownValueError:
            logger.info("Speech was unintelligible or empty.")
            text = ""
        except sr.RequestError as e:
            logger.error(f"Speech recognition service error: {e}")
            text = ""
        except Exception as e:
            logger.error(f"Unexpected STT error: {e}")
            text = ""
        finally:
            # Clean up temp file
            try:
                if os.path.exists(wav_path):
                    os.remove(wav_path)
            except Exception:
                pass

        return text.strip()

    def _apply_custom_vocabulary(self, text: str, custom_words: List[str]) -> str:
        """
        Replaces case-insensitive matches with user-defined capitalization from custom dictionary.
        """
        result = text
        for word in custom_words:
            if not word:
                continue
            # Regex pattern for whole-word replacement with proper case
            pattern = re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
            result = pattern.sub(word, result)
        return result
