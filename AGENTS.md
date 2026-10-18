# VoiceOS Autonomous Agent Personas & Operational Modes

## 1. Overview
VoiceOS features a dual-engine architecture separating fast, deterministic system dictation from conversational multimodal intelligence. This document specifies the operational modes, voice personas, and AI orchestration behavior.

---

## 2. Operational Modes

### Mode 0: Dictation (`DICTATE`)
- **Hotkey:** `Ctrl + Shift + D` (or holding `Alt + Ctrl`)
- **Purpose:** Pure, low-latency speech-to-text.
- **Workflow:**
  1. Activates audio ducking to reduce background music/video volume.
  2. Captures user speech via WASAPI high-resolution audio buffer.
  3. Transcribes speech using local Speech-to-Text with custom vocabulary term boosting.
  4. Automatically injects the transcribed text directly into the active foreground window (VS Code, Word, Slack, Chrome, terminal) using synthetic keystrokes (`SendInput`) and restores previous clipboard contents.
  5. Records session metadata, word counts, and estimated typing time saved in SQLite.

### Mode 1: Dictation with Style (`WRITE`)
- **Purpose:** Guided voice writing with real-time text polishing.
- **Workflow:** Dictated speech is transformed into polished prose (e.g. formal email, bulleted meeting notes, technical documentation) before injection.

### Mode 2: Selection-Based Editing (`EDIT`)
- **Purpose:** In-place modification of highlighted desktop text.
- **Workflow:** Reads highlighted text using Windows UI Automation (`IUIAutomation`) or clipboard fallback (`Ctrl+C`), takes verbal instructions ("make this concise", "translate to Spanish"), and replaces the highlighted selection with the edited text.

### Mode 3: Autonomous Agent Assistant (`AGENT`)
- **Hotkey:** `Ctrl + Alt + A` (or Tab toggle in the Top Notch)
- **Purpose:** Conversational reasoning, multimodal assistance, and tool execution.
- **Workflow:**
  1. Feeds query along with active foreground window context (`app_name`, `window_title`) to the Gemini model.
  2. Streams response chunks into the Top Notch dynamic island.
  3. Executes registered tools (weather lookups, calculations, diagnostics) when requested by Gemini.
  4. Synthesizes voice reply using the configured neural speech persona.
  5. Saves the conversation turn into SQLite for chronological history tracking.

---

## 3. Selectable Voice Personas

VoiceOS includes four neural voice personas with tailored speech cadence and personality profiles:

| Persona | Voice Pitch & Speed | Accent / Style | Personality Profile |
|---|---|---|---|
| **Jarvis** | Balanced, 1.2x | British Male | Calm, articulate, precise, and polite. Ideal for productivity and coding. |
| **Friday** | Higher pitch, 1.25x | Warm Female | Crisp, adaptive, empathetic, and rapid. Great for dictation and quick queries. |
| **Edith** | Neutral, 1.15x | Tactical Female | Focused, concise, tactical intelligence delivery. Minimal filler words. |
| **Ultron** | Deep, resonant, 1.05x | Commanding Male | Deep, authoritative, commanding, and decisive. |

---

## 4. Omniroute Failover Pipeline

To ensure 99.99% availability without interrupting the user during rate-limiting or network stalls, VoiceOS implements **Gemini Omniroute**:

```
Primary: gemini-2.5-flash
    │
    ▼ (Rate limit / 404 / 429)
Fallback 1: gemini-2.5-pro
    │
    ▼ (Quota exhaustion)
Fallback 2: gemini-1.5-flash
    │
    ▼ (Fallback)
Fallback 3: gemini-1.5-pro
```

Omniroute operates silently in the background: errors from candidate models are trapped and retried immediately on the next model without spitting raw stack traces or JSON errors to the user.
