# VoiceOS Audio & Speech Pipeline Specification

## 1. Overview
The VoiceOS audio pipeline provides broadcast-quality audio capture, low-latency Speech-to-Text (STT) transcription, neural Text-to-Speech (TTS) synthesis, background audio ducking, and synthetic keystroke injection.

---

## 2. Audio Capture Service (`AudioCaptureService`)
- **Technology:** Python `sounddevice` / PyAudio with WASAPI high-resolution loopback & microphone stream.
- **Sample Rate:** 48,000 Hz.
- **Channels:** 1 (Mono) or 2 (Stereo).
- **Format:** 32-bit floating point PCM audio.
- **RMS Energy Metering:** Continuously calculates root-mean-square energy:
  $$\text{RMS} = \sqrt{\frac{1}{N} \sum_{i=1}^N x[i]^2}$$
  Broadcasts normalized volume levels ($0.0 - 1.0$) to drive dynamic waveform visualizers in the Top Notch.

---

## 3. Speech-to-Text Engine (`STTEngine`)
- **Technology:** Pluggable local Whisper / SpeechRecognition engine with custom dictionary term boosting.
- **Custom Vocabulary:** Intersects transcription hypotheses with user-defined terms stored in `dictionary` table to ensure technical acronyms, personal names, and specialized domain terms transcribe with 100% precision.

---

## 4. Text-to-Speech Engine (`TTSEngine`)
- **Technology:** Neural speech synthesis engine supporting real-time streaming cadence.
- **Speed Multiplier:** Configurable from 0.8x to 2.0x (Default: 1.2x).
- **Personas:** Jarvis (British Male), Friday (Warm Female), Edith (Tactical Female), Ultron (Commanding Male).
- **Instant Interruption:** Immediate cancellation on new input, keypress, or stop button click.

---

## 5. Background Audio Ducking (`AudioDucker`)
- **Technology:** Windows Core Audio APIs (`IAudioEndpointVolume` and `ISimpleAudioVolume`).
- **Behavior:**
  - When speech capture begins, attenuates Spotify, YouTube, games, and background audio to 20% of original volume.
  - When speech ends or times out, restores audio volume smoothly without clicks or pops.

---

## 6. Text Injection (`TextInjector`)
- **Technology:** Windows `SendInput` API and synthetic `Ctrl+V` key sequence.
- **Preservation:** Preserves existing clipboard contents by capturing prior data, setting synthesized text, dispatching paste keystrokes, and restoring original clipboard data within 50ms.
