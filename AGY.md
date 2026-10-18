# Antigravity (AGY) Architecture & Autonomous Agent Guide for VoiceOS

## 1. Overview
VoiceOS is developed and orchestrated under the **Google Antigravity (AGY)** framework. Antigravity combines deep system introspection, clean-room reverse-engineering, proactive background sidecars, and advanced agentic workflows to build high-performance native desktop AI applications.

This document outlines the Antigravity design philosophy, development conventions, multi-process architecture, and customization protocols used in VoiceOS.

---

## 2. Core Antigravity Principles

### 2.1 Clean-Room Independence
- **Zero Proprietary Lock-In:** Rather than depending on proprietary cloud infrastructure or commercial trial paywalls, the application is reconstructed from first principles using open protocols and direct client libraries.
- **Local-First Reliability:** Critical audio capture, global hotkey interception, text injection, and SQLite session history operate 100% locally on the host OS.
- **Direct AI Integration:** Connects directly to Google Gemini models via user-provided API keys, bypassing third-party intermediaries and rate-limiting proxies.

### 2.2 1:1 Pixel Fidelity & Monochromatic Luxury
- Strict visual match with reference designs down to exact pixel metrics, border radii, typography weights, and color values (`#000000`, `#16161c`, `#252830`, `#8a8a8e`).
- Button-free aesthetic: Eliminates cluttered header bars, generic buttons, and standard window chrome in favor of fluid Dynamic Island interactions.

### 2.3 Proactive Situational Awareness
- Antigravity agents monitor the active foreground window (`EVENT_SYSTEM_FOREGROUND`) and inject relevant context into reasoning loops.
- Instant, non-destructive text injection via Windows `SendInput` and clipboard preservation.

---

## 3. System Architecture

```mermaid
flowchart TD
    subgraph Antigravity Orchestrator
        AGY_CORE[Antigravity Core / main.py]
        HOTKEYS[GlobalHotkeyManager (ctypes Win32)]
        WATCHER[WindowWatcher (WinEventHook)]
        INJECTOR[TextInjector (SendInput / Clipboard)]
    end

    subgraph Audio Pipeline
        AUDIO_SRV[AudioCaptureService (WASAPI 48kHz)]
        STT_ENG[STTEngine (Whisper / SpeechRecog)]
        TTS_ENG[TTSEngine (Neural Speech Personas)]
        DUCKER[AudioDucker (IAudioEndpointVolume)]
    end

    subgraph UI Layer
        NOTCH[NotchWidget (1:1 Top Dynamic Island)]
        HISTORY[HistoryDrawer (1:1 Floating Chat Panel)]
        DASHBOARD[MainWindow (Full Control Center)]
        TRAY[SystemTrayManager]
    end

    subgraph Intelligence & Storage
        GEMINI[GeminiProvider (Omniroute Failover)]
        SQLITE[(SQLite WAL Database: voiceos.db)]
    end

    HOTKEYS -->|Dictation / Agent Hotkeys| AGY_CORE
    AGY_CORE --> AUDIO_SRV
    AUDIO_SRV --> DUCKER
    AUDIO_SRV --> STT_ENG
    STT_ENG -->|Transcribed Text| AGY_CORE
    AGY_CORE -->|Mode 0: Dictation| INJECTOR
    AGY_CORE -->|Mode 3: Agent Query| GEMINI
    GEMINI -->|Streaming Chunks| NOTCH
    GEMINI -->|Tool Invocations| AGY_CORE
    AGY_CORE --> TTS_ENG
    AGY_CORE --> SQLITE
    NOTCH <-->|Toggle / Select| HISTORY
    HISTORY -->|Restore Session| NOTCH
```

---

## 4. Antigravity Customizations & Tooling

### 4.1 Built-in Slash Commands
The Top Notch and Dashboard provide instant execution for built-in diagnostic and productivity commands:
- `/mode` — Toggle between Dictation (Mode 0) and Agent (Mode 3).
- `/weather <city>` — Instant real-time meteorological conditions and temperature.
- `/calc <expr>` — Safe AST-evaluated arithmetic computation.
- `/time` — Precise local system time, date, and timezone.
- `/sys` — Host hardware status (CPU, RAM utilization, OS platform).
- `/persona <name>` — Live voice persona switch (*Jarvis*, *Friday*, *Edith*, *Ultron*).
- `/clear` — Clear input and content buffers.

### 4.2 Extensibility & Skills
Antigravity supports pluggable skills and tools configured in `ai/tools.py`. Each tool defines:
1. `name`: Unique string identifier (e.g., `weather_forecast`).
2. `description`: Model-facing prompt instruction explaining when and how to call the function.
3. `parameters`: JSON Schema specification of accepted arguments.
4. `callable`: Synchronous or asynchronous Python implementation.

---

## 5. Verification & Testing Standards
- All Antigravity components are covered by automated unit and integration tests under `tests/`.
- Test suites must be executed with offscreen Qt applications using `pytest`.
- Visual regression checks are performed against reference screenshots to guarantee pixel-level accuracy.
