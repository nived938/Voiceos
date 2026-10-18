# VoiceOS Reconstruction & Clean-Room Implementation

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![PySide6 / Qt 6](https://img.shields.io/badge/GUI-PySide6%20%2F%20Qt%206-green.svg)](https://wiki.qt.io/Qt_for_Python)
[![Gemini API](https://img.shields.io/badge/AI-Google%20Gemini%20API-orange.svg)](https://ai.google.dev/)
[![Tests](https://img.shields.io/badge/Tests-24%20Passing-brightgreen.svg)]()
[![Platform](https://img.shields.io/badge/Platform-Windows%2010%20%2F%2011%2064--bit-lightgrey.svg)]()
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)]()

This repository contains the complete forensic reverse-engineering investigation of the commercial **VoiceOS** desktop application, accompanied by an original, production-ready clean-room implementation: **VOICEOS-OWN**.

Built with **Python**, **PySide6 (Qt 6)**, and powered by **Google Gemini API**, VOICEOS-OWN reproduces and enhances the core capabilities of VoiceOS into a luxury, high-contrast **Black and White** interface featuring a **1:1 button-free Top Notch Dynamic Island**, **Gemini Omniroute auto-failover**, **selectable AI voice personas** (Jarvis, Friday, Edith, Ultron), and **direct keyboard input**.

---

## 📁 Repository Architecture

```
VOICE-OS/
├── research/
│   └── VOICEOS_INVESTIGATION.md    # Complete 16KB forensic reverse-engineering report
├── VOICEOS-OWN/                    # Independent clean-room Windows desktop assistant
│   ├── ai/                         # Google Gemini provider with Omniroute failover & tools
│   ├── audio/                      # Audio capture, STT, TTS personas & system ducking
│   ├── core/                       # Hotkeys, SQLite, window watcher & text injector
│   ├── ui/                         # Monochromatic Qt6 UI, button-free Top Notch & drawer
│   ├── tests/                      # 24 automated unit tests
│   ├── docs/                       # Specifications (Architecture, Security, Licensing)
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

### 1. 1:1 Button-Free Top Notch Dynamic Island
- **Clean Aesthetic:** Designed with a pure OLED black (`#000000`) and white (`#ffffff`) palette, free from distracting buttons.
- **State Transitions:**
  - *Hidden by default:* Discreet 4px trigger at the top-center edge of the screen.
  - *Hover to peek:* Slides down smoothly into a 28px rounded pill when hovering at the top of the monitor.
  - *Click to expand:* Expands into a 150px dynamic island featuring live visualizer bars, active voice persona, mode indicator, and typing bar.
- **Click-Outside Auto-Dismissal:** Global 35ms cursor monitoring auto-collapses the notch smoothly whenever the user clicks anywhere outside the island, switches applications, or presses `Esc`.

### 2. Direct Typing Interface ("Typre Thing") & Built-in Slash Commands
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
