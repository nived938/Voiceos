# Claude Code & Engineering Guide for VoiceOS

## 1. Project Overview
VoiceOS is a clean-room, production-grade Windows desktop application reproducing the luxury voice assistant experience of VoiceOS without commercial paywalls or cloud lock-in. Powered by PySide6 (Qt 6), Python 3.12, and Google Gemini API.

---

## 2. Directory Layout
```
VOICE-OS/
├── AGY.md                          # Antigravity architectural guidelines
├── AGENTS.md                       # Persona definitions & operational modes
├── CLAUDE.md                       # This developer and CLI reference
├── UI_SPECIFICATION.md             # 1:1 pixel fidelity & geometry rules
├── CHAT_HISTORY.md                 # Floating chat history panel architecture
├── TOP_NOTCH.md                    # Dynamic Island top notch specification
├── VOICE_PIPELINE.md               # Audio capture, STT, TTS, ducking
├── DATABASE_SCHEMA.md              # SQLite persistence documentation
├── HOTKEYS_AND_INPUT.md            # Windows global hotkeys & injection
├── INTEGRATIONS.md                 # Gemini API & tool ecosystem
├── DEVELOPER_GUIDE.md              # Setup, troubleshooting & contributing
├── research/
│   └── VOICEOS_INVESTIGATION.md    # 16KB Forensic Reverse Engineering Report
└── VOICEOS-OWN/                    # Source application codebase
    ├── main.py                     # Entry point
    ├── requirements.txt            # Python dependencies
    ├── ai/                         # Gemini provider, Omniroute & tools
    ├── audio/                      # Audio capture, STT, TTS personas
    ├── core/                       # SQLite database, hotkeys, text injector
    ├── ui/                         # Qt widgets, styles, assets
    │   ├── assets/                 # Icons (globe.png, etc.)
    │   ├── notch_widget.py         # 1:1 Top Notch widget
    │   ├── history_drawer.py       # 1:1 Floating Chat History panel
    │   ├── main_window.py          # Dashboard window
    │   └── styles.py               # Monochromatic dark stylesheets
    └── tests/                      # Automated test suite (30 passing tests)
```

---

## 3. Essential Commands

### Environment Setup
```powershell
# Navigate to application folder
cd g:\Coding\VOICE-OS\VOICEOS-OWN

# Install dependencies
python -m pip install -r requirements.txt

# Run the desktop application
python main.py
```

### Running Tests
```powershell
# Run the complete test suite
python -m pytest

# Run only UI tests
python -m pytest tests/test_notch_widget.py tests/test_history_drawer.py
```

---

## 4. Key Engineering Guardrails
1. **Never Tamper with Tech Stack:** Maintain PySide6, Python 3.12, and SQLite.
2. **Never Mock Production Logic:** Gemini client, STT, TTS, and Win32 hooks must run real code.
3. **Preserve Monochromatic Luxury:** Strictly use `#000000`, `#16161c`, `#252830`, `#8a8a8e`, `#ffffff`. Avoid gradients, neon accents, or generic UI buttons.
4. **Maintain 1:1 Visual Match:** All UI elements must adhere to measured pixel coordinates and shapes defined in `UI_SPECIFICATION.md`.
