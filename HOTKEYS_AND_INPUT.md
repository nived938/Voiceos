# VoiceOS Global Hotkeys & Native Input Management

## 1. Overview
VoiceOS interfaces directly with the Windows API to capture keystrokes globally—regardless of which application is focused—and inject synthesized speech text back into target apps seamlessly.

---

## 2. Global Hotkey Mappings

| Hotkey Combination | Target Action | Default Mode |
|---|---|---|
| `Ctrl + Shift + D` | Toggle Dictation Mode | Mode 0 (`DICTATE`) |
| `Ctrl + Alt + A` | Toggle Autonomous Agent | Mode 3 (`AGENT`) |
| `Alt + ` ` (Backtick) | Toggle Floating Top Notch / History Drawer | Navigation |
| `Alt + Ctrl` (Hold) | Push-to-Talk speech capture | Active Mode |

---

## 3. Windows Native Implementation

### 3.1 `GlobalHotkeyManager`
Implemented in `core/hotkeys.py` using Win32 API functions:
- `RegisterHotKey`: Registers global shortcut combinations with the Windows desktop shell.
- `UnregisterHotKey`: Safely unhooks shortcuts upon application exit.
- `GetMessageW` / `DispatchMessageW`: Non-blocking message loop executing on a dedicated background thread.

### 3.2 Foreground Window Tracking (`WindowWatcher`)
- Registers Windows event hooks via `SetWinEventHook` monitoring `EVENT_SYSTEM_FOREGROUND`.
- Retrieves target process name via `GetWindowThreadProcessId` and window title via `GetWindowTextW`.
- Attaches the active application name (e.g. `Code.exe`, `WINWORD.EXE`, `chrome.exe`) to AI queries for situational awareness.

### 3.3 Synthetic Keystroke Injection (`TextInjector`)
- Calls `SendInput` with `KEYEVENTF_KEYUP` flags to simulate `Ctrl+V`.
- Automatically restores previously stored clipboard data within 50ms, ensuring zero clipboard pollution.
