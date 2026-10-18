import threading
import queue
import pyttsx3
import logging
from typing import Optional, Callable, List, Dict, Any

logger = logging.getLogger("VoiceOS.TTS")

class TTSEngine:
    """
    Text-to-Speech synthesis with non-blocking playback, selectable voice personas
    (Jarvis, Friday, Edith, Ultron), speed multiplier control, and instant interruption support.
    """

    PERSONAS: Dict[str, Dict[str, Any]] = {
        "Jarvis": {
            "gender": "male",
            "base_rate": 175,
            "description": "Calm, precise, sophisticated male AI assistant"
        },
        "Friday": {
            "gender": "female",
            "base_rate": 195,
            "description": "Quick, warm, and highly efficient female assistant"
        },
        "Edith": {
            "gender": "female",
            "base_rate": 170,
            "description": "Gentle, articulate tactical intelligence"
        },
        "Ultron": {
            "gender": "male",
            "base_rate": 140,
            "description": "Deep, commanding, and deliberate presence"
        }
    }

    def __init__(self, speed_multiplier: float = 1.0, persona: str = "Jarvis"):
        self.speed_multiplier = speed_multiplier
        self.persona = persona if persona in self.PERSONAS else "Jarvis"
        self.is_speaking = False
        self._thread: Optional[threading.Thread] = None
        self._queue = queue.Queue()
        self._stop_event = threading.Event()
        self._on_start_cb: Optional[Callable[[], None]] = None
        self._on_finish_cb: Optional[Callable[[], None]] = None

    def set_callbacks(self, on_start: Optional[Callable[[], None]] = None,
                      on_finish: Optional[Callable[[], None]] = None):
        self._on_start_cb = on_start
        self._on_finish_cb = on_finish

    def set_persona(self, persona: str):
        if persona in self.PERSONAS:
            self.persona = persona
            logger.info(f"TTS persona updated to: {persona}")

    @staticmethod
    def get_available_voices() -> List[Dict[str, str]]:
        voices = []
        try:
            engine = pyttsx3.init()
            for v in engine.getProperty("voices"):
                voices.append({
                    "id": v.id,
                    "name": v.name,
                    "languages": v.languages
                })
        except Exception as e:
            logger.error(f"Error listing TTS voices: {e}")
        return voices

    def _resolve_voice_for_persona(self, persona_name: str, engine) -> Optional[str]:
        """Finds the best matching installed voice for the persona gender."""
        persona_info = self.PERSONAS.get(persona_name, self.PERSONAS["Jarvis"])
        desired_gender = persona_info["gender"]

        try:
            voices = engine.getProperty("voices")
            if not voices:
                return None

            female_keywords = ["zira", "hazel", "catherine", "susan", "eva", "female", "cortana"]
            male_keywords = ["david", "mark", "george", "male", "richard", "james"]

            for v in voices:
                v_name = v.name.lower()
                if desired_gender == "female":
                    if any(kw in v_name for kw in female_keywords):
                        return v.id
                else: # male
                    if any(kw in v_name for kw in male_keywords):
                        return v.id

            # Fallback if specific gender name match not found
            for v in voices:
                v_gender = getattr(v, "gender", None)
                if v_gender and str(v_gender).lower() == desired_gender:
                    return v.id

            return voices[0].id
        except Exception as e:
            logger.warning(f"Voice resolution warning: {e}")
            return None

    def speak(self, text: str, persona: Optional[str] = None, voice_id: Optional[str] = None):
        """
        Asynchronously speaks the provided text.
        Interrupts any currently playing speech.
        """
        if not text or not text.strip():
            return

        self.stop() # Interrupt existing speech
        self._stop_event.clear()
        self.is_speaking = True

        target_persona = persona or self.persona
        persona_info = self.PERSONAS.get(target_persona, self.PERSONAS["Jarvis"])

        def _worker():
            try:
                if self._on_start_cb:
                    self._on_start_cb()

                engine = pyttsx3.init()

                # Calculate rate: base rate for persona * speed multiplier
                target_rate = int(persona_info["base_rate"] * self.speed_multiplier)
                engine.setProperty("rate", max(80, min(350, target_rate)))

                # Resolve voice
                selected_voice = voice_id or self._resolve_voice_for_persona(target_persona, engine)
                if selected_voice and selected_voice != "default":
                    engine.setProperty("voice", selected_voice)

                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                logger.error(f"TTS playback error: {e}")
            finally:
                self.is_speaking = False
                if self._on_finish_cb:
                    self._on_finish_cb()

        self._thread = threading.Thread(target=_worker, daemon=True)
        self._thread.start()

    def stop(self):
        """Interrupts and stops speech playback."""
        self._stop_event.set()
        self.is_speaking = False
        try:
            engine = pyttsx3.init()
            engine.stop()
        except Exception:
            pass
