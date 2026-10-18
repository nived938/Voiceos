# VoiceOS-Own — Universal AI Voice Interface for Windows

VoiceOS-Own is an independent, clean-room desktop assistant inspired by the forensic reverse-engineering of the commercial VoiceOS application. Powered directly by your personal **Google Gemini API** key and built on **PySide6 (Qt 6)**, VoiceOS-Own provides a luxury **Black and White** high-contrast interface, an advanced **1:1 Top Notch Dynamic Island**, direct **keyboard typing** integration, **voice personas** (Jarvis, Friday, Edith, Ultron), and **Gemini Omniroute** silent failover.

---

## Key Features

- **🎙️ Mode 0: Universal Dictation (`Ctrl+Shift+D`):** Speak into any Windows application (Word, Chrome, Slack, VS Code). Completed speech is automatically typed directly into the active window at the cursor.
- **🧠 Mode 3: Conversational Agent (`Ctrl+Alt+A`):** Ask questions, request calculations, check real-time weather via Open-Meteo, and query system diagnostics with Google Gemini.
- **✨ 1:1 Button-Free Top Notch Dynamic Island:**
  - *Hidden by default:* Discreet 4px trigger at the top-center edge of your primary monitor.
  - *Hover to peek:* Slides down smoothly into a sleek 28px rounded pill when hovering near the top-center.
  - *Click to expand:* Animates into the full 150px interactive dynamic island with direct typing input, live soundwave visualizer bars, and persona indicator.
  - *Click-outside auto-dismiss:* Global mouse listener immediately and smoothly collapses the notch whenever clicking anywhere outside its bounds, switching windows, or pressing `Esc`.
- **⌨️ Direct Typing Interface ("Typre thing"):** Type queries or dictation commands directly inside the Top Notch or on the Home dashboard without speaking. Supports `Enter` to submit, `Tab` to toggle Dictate/Agent mode, and `Esc` to dismiss.
- **⚡ Built-in Slash Commands:** Instant actions straight from the Notch typing bar:
  - `/weather <city>` — Instant live weather lookup
  - `/calc <expr>` — Safe mathematical evaluation
  - `/time` — Current date, time, and timezone
  - `/sys` — CPU, RAM, and platform telemetry
  - `/copy <text>` & `/paste` — Clipboard utilities
  - `/persona <Jarvis|Friday|Edith|Ultron>` — Instant voice persona switching
  - `/mode` — Toggle between Dictate and Agent modes
- **🪟 Situational Active Window Context:** VoiceOS-Own captures the active foreground application name and window title (e.g., *VS Code*, *Chrome*, *Terminal*) to provide contextual, relevant answers when querying Gemini.
- **🔊 Tactile Audio Cues:** Non-blocking frequency beeps on voice activation and completion via Windows audio.
- **🔄 Gemini Omniroute Silent Auto-Switch:** Automatically and silently falls back (`gemini-2.5-flash` → `gemini-2.5-pro` → `gemini-1.5-flash` → `gemini-1.5-pro`) if a model is unavailable, rate-limited, or timing out. Zero interruption to the user.
- **🎭 Selectable Voice Personas:** Choose between **Jarvis** (calm, precise male tone), **Friday** (crisp, warm female tone), **Edith** (smooth tactical intelligence), or **Ultron** (deep, commanding male tone) with customized speech rates.
- **🖤 Monochromatic Black & White Theme:** Pure OLED black (`#000000`) and crisp white typography with subtle borders and shadows.
- **📖 Personal Custom Vocabulary:** Boost recognition accuracy for personal names, technical terms, and acronyms with a local custom dictionary.
- **🔉 Background Audio Ducking:** Automatically lowers media/browser audio volume during active speech and restores it seamlessly.
- **📊 Analytics & Productivity Insights:** Local SQLite tracking of words dictated, time saved, and tool executions.

---

## Quick Start

### 1. Requirements
- Windows 10/11 64-bit
- Python 3.10+
- A Google Gemini API key from [Google AI Studio](https://aistudio.google.com/)

### 2. Installation
```powershell
cd G:\Coding\VOICE-OS\VOICEOS-OWN
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

### 3. Launching
```powershell
# Using PowerShell launcher
.\run.ps1

# Or standard Python command
python main.py
```

### 4. Running the Automated Tests
```powershell
python -m pytest tests -v
```

---

## Project Structure

```
VOICEOS-OWN/
├── ai/
│   ├── base.py                 # Abstract AI provider contract
│   ├── gemini_provider.py      # Google Gemini provider with Omniroute failover
│   └── tools.py                # Agent tools (weather, system, calculate, time)
├── audio/
│   ├── audio_capture.py        # 48kHz audio capture & RMS volume calculation
│   ├── stt_engine.py           # Speech-to-text with custom dictionary boosting
│   ├── tts_engine.py           # Text-to-speech with Jarvis/Friday/Edith/Ultron personas
│   └── audio_duck.py           # System audio ducking controller
├── core/
│   ├── config.py               # JSON settings manager & credential masking
│   ├── database.py             # SQLite persistence (voice_sessions, dictionary, insights)
│   ├── hotkeys.py              # Windows global hotkey manager
│   ├── text_injector.py        # Native keystroke & clipboard injection
│   ├── window_watcher.py       # Active foreground window tracker
│   └── selection_reader.py     # Highlighted text reader
├── ui/
│   ├── main_window.py          # Dashboard (Home, Insights, History, Dictionary, Settings)
│   ├── notch_widget.py         # Advanced 1:1 Top Notch dynamic island with typing input
│   ├── history_drawer.py       # Slide-out history drawer
│   ├── onboarding_dialog.py    # 4-step first-run wizard
│   ├── tray_icon.py            # Windows taskbar system tray icon
│   └── styles.py               # Monochromatic Black and White stylesheet
├── tests/                      # Automated test suite (24 unit tests)
├── docs/                       # Complete architectural and security specifications
├── run.ps1                     # PowerShell launch script
├── run.bat                     # Windows batch launch script
└── main.py                     # Application entrypoint
```

---

## Documentation

- [Investigation Report](file:///G:/Coding/VOICE-OS/research/VOICEOS_INVESTIGATION.md)
- [Architecture & Design](file:///G:/Coding/VOICE-OS/VOICEOS-OWN/docs/ARCHITECTURE.md)
- [Installation Guide](file:///G:/Coding/VOICE-OS/VOICEOS-OWN/docs/INSTALLATION.md)
- [Feature Details](file:///G:/Coding/VOICE-OS/VOICEOS-OWN/docs/FEATURES.md)
- [Security & Privacy](file:///G:/Coding/VOICE-OS/VOICEOS-OWN/docs/SECURITY.md)
- [Troubleshooting](file:///G:/Coding/VOICE-OS/VOICEOS-OWN/docs/TROUBLESHOOTING.md)
- [Clean-Room Licensing](file:///G:/Coding/VOICE-OS/VOICEOS-OWN/docs/LICENSING.md)
