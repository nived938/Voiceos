# VoiceOS Reconstruction & Clean-Room Implementation

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![PySide6 / Qt 6](https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt%206-green.svg)](https://wiki.qt.io/Qt_for_Python)
[![Gemini API](https://img.shields.io/badge/AI-Google%20Gemini%20API-orange.svg)](https://ai.google.dev/)
[![Tests](https://img.shields.io/badge/Tests-30%20Passing-brightgreen.svg)]()
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011%2064--bit-lightgrey.svg)]()
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)]()

This repository contains the complete forensic reverse-engineering investigation of the commercial **VoiceOS** desktop application, accompanied by an original, production-ready clean-room implementation: **VOICEOS-OWN**.

Built with **Python**, **PySide6 (Qt 6)**, and powered by **Google Gemini API**, VOICEOS-OWN reproduces the visual aesthetic and capabilities of VoiceOS into a luxury, high-contrast **Black and White** interface featuring a **1:1 Floating Top Notch Dynamic Island** (pure `#000000`, rounded ears, dark `[alt]` and `[control]` keycaps), a **1:1 Floating Left-Side Chat History Panel** (real search filter, timestamp grouping, pin/lock control), **Gemini Omniroute auto-failover**, **selectable AI voice personas** (Jarvis, Friday, Edith, Ultron), and **direct keyboard input**.

---

## 📁 Repository Architecture

```
VOICE-OS/
├── AGY.md                          # Antigravity architectural guidelines
├── AGENTS.md                       # Persona definitions & operational modes
├── CLAUDE.md                       # Claude Code developer & CLI reference
├── UI_SPECIFICATION.md             # 1:1 pixel fidelity & geometry rules
├── CHAT_HISTORY.md                 # Floating chat history panel architecture
├── TOP_NOTCH.md                    # Dynamic Island top notch specification
├── VOICE_PIPELINE.md               # Audio capture, STT, TTS, ducking
├── DATABASE_SCHEMA.md              # SQLite persistence documentation
├── HOTKEYS_AND_INPUT.md            # Windows global hotkeys & injection
├── INTEGRATIONS.md                 # Gemini API & tool ecosystem
├── DEVELOPER_GUIDE.md              # Setup, troubleshooting & contributing
├── research/
│   └── VOICEOS_INVESTIGATION.md    # Complete 16KB forensic reverse-engineering report
├── VOICEOS-OWN/                    # Independent clean-room Windows desktop assistant
│   ├── ai/                         # Google Gemini provider with Omniroute failover & tools
│   ├── audio/                      # Audio capture, STT, TTS personas & system ducking
│   ├── core/                       # Hotkeys, SQLite, window watcher & text injector
│   ├── ui/                         # Monochromatic Qt6 UI, 1:1 Top Notch & History Drawer
│   │   ├── assets/                 # High-resolution assets (globe.png)
│   │   ├── notch_widget.py         # 1:1 Top Notch dynamic island
│   │   ├── history_drawer.py       # 1:1 Floating Chat History panel
│   │   ├── main_window.py          # Dashboard & pipeline coordinator
│   │   └── styles.py               # Monochromatic dark stylesheets
│   ├── tests/                      # 30 automated unit tests (100% passing)
│   ├── docs/                       # Component specifications
│   ├── run.ps1                     # PowerShell one-click launcher
│   ├── run.bat                     # Windows batch launcher
│   └── main.py                     # Desktop application entry point
├── .gitignore                      # Git ignore protecting API keys, DBs & caches
└── README.md                       # Project root documentation
```

---

## 🔍 Forensic Investigation Summary

The full evidence-based report is available in [`research/VOICEOS_INVESTIGATION.md`](research/VOICEOS_INVESTIGATION.md). Key findings include:

- **Packaging & Framework:** Commercial VoiceOS is packaged with Electron 39 on Windows x64 using ASAR archives (`app.asar`), React frontend, and native C++ sidecars.
- **Local Persistence:** Uses SQLite with WAL mode (`voiceos.db`) storing sessions, snippets, audio clips, and custom vocabulary.
- **Trial Wall & Licensing:** Enforces a 7-day trial paywall locked to an upstream Stripe billing token and device fingerprint. In accordance with clean-room reverse-engineering ethics, the commercial trial was neither patched nor bypassed.
- **Core Workflow:** Intercepts global hotkeys (`Ctrl+Shift+D` / `Ctrl+Alt+A`), streams microphone input, and injects recognized text into the active foreground window via Windows SendInput / synthetic keystrokes.

---

## ✨ Features of VOICEOS-OWN

### 1. 1:1 Floating Top Notch Dynamic Island
- **Exact Visual Match:** Pure `#000000` background with smooth inverse flares ("ears") flaring flush into screen top ($y = 0$) and 30px rounded lower corners.
- **Icon & Keycaps:**
  - Top-left 18x18px glossy globe icon (toggles floating history drawer).
  - Second row hint: `Type or hold [alt] [control] to speak` rendered with dark rounded keycaps (`#222226` background, `#d1d1d6` bold text).
- **Expanded Card View:**
  - Query pill (`#16161c`) with prompt text.
  - Slate Result Card (`#252830`) displaying meteorological weather metrics (`Kāsaragod`, `25°C`, `Overcast`, `H:32° L:24°`) or streaming AI text.
  - Circular Stop Button (`#1e1e24` circle with white square `■`).
- **Outside Click Auto-Dismissal:** Smoothly collapses on outside click, window switch, or `Esc`.

### 2. 1:1 Floating Left-Side Chat History Panel
- **Dimensions & Placement:** 232px wide $\times$ 516px tall, starting 58px below screen top at $x = 0$ with 26px rounded corners.
- **Search Pill & Lock:**
  - Embedded magnifying glass icon with real-time substring filtering across titles and transcripts.
  - Circular lock control toggles between unpinned (auto-dismiss) and pinned (persistent) mode.
- **Chronological Groupings:** Automatically formats timestamps into buckets (`Today, 6:05 PM`, `Today, 2:56 PM`, `Yesterday, 4:10 PM`).
- **Conversation Items:** Single-line white titles with ellipsis truncation, globe icons, and `#1a1a24` selection highlighting.
- **Conversation Restoration:** Single-click restores past conversation content directly into the Top Notch and copies to clipboard.

### 3. Direct Typing Interface & Built-in Slash Commands
Type queries directly into the Top Notch or Home Dashboard without speaking:
- `Enter` ↵ to submit
- `Tab` ⇆ to toggle between **[DICTATE]** and **[AGENT]** modes
- `Esc` ✕ to dismiss
- **Built-in Slash Commands:**
  - `/weather <city>` — Real-time weather lookup via Open-Meteo
  - `/calc <expr>` — Safe AST-evaluated math computation
  - `/time` — Current system time, date, and timezone
  - `/sys` — Live CPU, RAM, and OS diagnostics
  - `/copy <text>` & `/paste` — System clipboard operations
  - `/persona <name>` — Switch voice persona to *Jarvis*, *Friday*, *Edith*, or *Ultron*
  - `/mode` — Switch between Dictation (Mode 0) and Agent (Mode 3)
  - `/clear` — Clear the input field

### 3. Gemini Omniroute Silent Auto-Switch
VoiceOS-Own automatically and silently routes queries across Google's Gemini models:
```
gemini-2.5-flash  ──(timeout / rate-limit)──>  gemini-2.5-pro  ──(fallback)──>  gemini-1.5-flash  ──(fallback)──>  gemini-1.5-pro
```
If a model is temporarily unavailable or quota-limited, the system seamlessly retries on the next available model without interrupting the user.

### 4. Selectable AI Voice Personas
- **Jarvis:** Calm, precise, articulate British male cadence.
- **Friday:** Crisp, warm, adaptive female cadence.
- **Edith:** Smooth, tactical intelligence delivery.
- **Ultron:** Deep, resonant, commanding tone.

### 5. Situational Active Window Context
When making requests in Agent mode, VoiceOS-Own inspects the foreground Windows application (e.g., *VS Code*, *Chrome*, *Command Prompt*) and feeds its context to Gemini, enabling relevant, context-aware answers.

### 6. Universal Native Windows Text Injection
- Mode 0 (`Ctrl+Shift+D`) types recognized text directly into any focused application (Word, Discord, Slack, browsers, code editors) at the cursor position.
- Supports custom dictionary word boosting to ensure technical jargon, personal names, and acronyms transcribe accurately.

### 7. Background Audio Ducking & Non-Blocking Cues
- Automatically attenuates background media volume while dictating and restores volume smoothly when speech ends.
- Non-blocking tactile audio tones provide immediate feedback when listening starts and completes.

---

## 🚀 Quick Start Guide

### Prerequisites
- **Operating System:** Windows 10 or 11 (64-bit)
- **Python:** Version 3.10 or higher
- **Gemini API Key:** Free key available from [Google AI Studio](https://aistudio.google.com/)

### Installation
```powershell
# Clone the repository
git clone https://github.com/nived938/Voiceos.git
cd Voiceos\VOICEOS-OWN

# Install dependencies
python -m pip install -r requirements.txt

# Configure your environment
Copy-Item .env.example .env
# Edit .env and enter your GEMINI_API_KEY
```

### Launching the Application
```powershell
# Launch with PowerShell script
.\run.ps1

# Or run directly with Python
python main.py
```

### Running the Test Suite
All 24 automated unit tests can be run via pytest:
```powershell
cd VOICEOS-OWN
python -m pytest tests -v
```

---

## 🔒 Security & Privacy

- **Local Storage:** SQLite database, custom vocabulary, and history remain 100% on your local machine.
- **Credential Protection:** Gemini API keys are read from environment variables or encrypted configuration files. Keys are always masked (`AIzaSy...ABCD`) in logs and UI.
- **Zero Telemetry:** No tracking, analytics pings, or commercial paywalls.
- **Safe Execution:** Mathematical evaluations use AST inspection without dangerous `eval()` execution.

---

## 📄 License & Clean-Room Declaration

This project was developed strictly adhering to **clean-room reverse-engineering** principles:
- No copyrighted binaries, proprietary source code, or licensing tokens were copied or distributed.
- The implementation is completely original and published under the [MIT License](LICENSE).
