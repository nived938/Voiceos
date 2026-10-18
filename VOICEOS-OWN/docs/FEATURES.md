# VoiceOS-Own Feature Catalog & Operational Guide

## Core Modes of Operation

### 1. Mode 0: Dictation (`Ctrl+Shift+D` or Notch Toggle)
- **Purpose:** Converts spoken speech into text and types it directly into your currently active application.
- **Workflow:**
  1. Click inside any text field (Notepad, Word, Chrome, Slack, Discord, VS Code).
  2. Press `Ctrl+Shift+D` (or click "🎙️ Dictate" on the Top Notch).
  3. Speak naturally. The Top Notch expands showing live waveform bars and "Listening...".
  4. Press the hotkey again or pause.
  5. Your words are instantly typed into the active window at the cursor position.
- **Vocabulary Injection:** Words added to your **Custom Dictionary** (e.g. personal names, product names) are automatically recognized and capitalized.

### 2. Mode 3: Agent Mode (`Ctrl+Alt+A` or Notch Toggle)
- **Purpose:** Conversational voice AI powered by Google Gemini with Omniroute silent model failover and tool calling capabilities.
- **Workflow:**
  1. Press `Ctrl+Alt+A` (or switch mode to "🧠 Agent" in the Top Notch).
  2. Ask a question or command:
     - *"What is the weather in Kasaragod today?"*
     - *"Calculate 145 times 32."*
     - *"What time is it right now?"*
     - *"Check system status."*
  3. The Top Notch displays streaming Gemini thought output while tools are executed.
  4. The assistant speaks the synthesized answer out loud using your chosen **Voice Persona** (Jarvis, Friday, Edith, or Ultron).
  5. The interaction is recorded in your local SQLite History.

---

## Desktop Overlays & Dynamic Controls

### 3. Advanced Top Notch Dynamic Island (`ui/notch_widget.py`)
- **Aesthetic:** Stark, luxury OLED Black and White monochrome theme with smooth drop shadow.
- **3-Tier Interactive Lifecycle:**
  1. **Hidden / Dormant:** Nearly invisible 4px touch trigger sliver at the top-center edge of the screen. Does not obstruct normal work.
  2. **Hover Peeking:** Moving the mouse cursor to the top center of the monitor smoothly animates a sleek 28px rounded pill displaying `✨ VoiceOS` and ready indicator.
  3. **Click to Expand:** Clicking the peeking bar (or pressing `Alt + \``) smoothly animates the full 160px interactive dynamic island.
- **Integrated Typing Interface ("Typre thing"):**
  - Direct keyboard input field (`QLineEdit`) embedded in the Notch.
  - Type prompts or commands and press `Enter` to get answers or inject text without speaking.
- **Interactive Controls inside Notch:**
  - `🎙️ Dictate` / `🧠 Agent` clickable mode pills.
  - 5-bar live soundwave visualizer that moves dynamically with audio energy.
  - `↵ Send` button, `🎙️ Speak` mic toggle, and `📋 Paste` last output button.
  - Collapses smoothly on `▲` or auto-collapses after completion.

### 4. Direct Dashboard Typing Bar
- Built right into the **Home** dashboard for immediate keyboard prompting.
- Supports instant switching between Agent queries and Text injection without using a microphone.

### 5. Gemini AI Omniroute Auto-Failover
- **Intelligent Silent Route:**
  `gemini-2.5-flash` → `gemini-2.5-pro` → `gemini-1.5-flash` → `gemini-1.5-pro`
- If your chosen model is unavailable, hits rate limits (429), or is slow, VoiceOS silently and automatically switches to the next best model.
- 100% transparent: never interrupts or pesters you with error popups.

### 6. Selectable Voice Personas
- **Jarvis:** Calm, precise, articulate British-style male AI presence (rate: 175 wpm).
- **Friday:** Warm, crisp, fast and efficient female assistant (rate: 195 wpm).
- **Edith:** Gentle, smooth, precision-tactical intelligence (rate: 170 wpm).
- **Ultron:** Deep, commanding, deliberate tone with authoritative cadence (rate: 140 wpm).
- Selectable and previewable anytime from **Settings**.

### 7. Custom Vocabulary Dictionary
- Located in Dashboard -> **Dictionary**.
- Add names, specialized medical/legal terms, programming identifiers, or acronyms.
- Stored permanently in SQLite and applied after transcription.

### 8. Background Audio Ducking
- Automatically attenuates Spotify, YouTube, games, or media player volume when dictating or when the assistant speaks, restoring full volume once speech ends.
