# VoiceOS Top Notch Dynamic Island Architecture

## 1. Overview
The **Top Notch Dynamic Island** (`NotchWidget`) is the primary interactive surface of VoiceOS. Docked at the top center of the screen ($y = 0$), it provides an elegant, button-free OLED experience inspired by modern hardware notches and macOS Dynamic Island.

---

## 2. Geometry & Smooth Silhouette

The notch is rendered on a frameless, transparent canvas using a custom `QPainterPath` that creates seamless inverse curvature ("ears") at the top screen boundary:

```
(0,0) ─────── ear_flare ─────── (ear_w, ear_h)
                                      │
                                  left_edge
                                      │
                                 rounded_corner (r=30px)
                                      │
(ear_w + r, h) ────── bottom_edge ────── (w - ear_w - r, h)
```

- **Width:** 480px (Idle) / 520px (Expanded).
- **Height:** 82px (Idle) / 270px (Expanded).
- **Top Inverse Curves:** 34px wide $\times$ 24px high cubic bezier curves blending into $y = 0$.
- **Bottom Corners:** 30px radius.
- **Color:** Solid pure black `#000000`.

---

## 3. Interaction States & Transitions

### State 0: Idle / Peeking View
- Displayed when the assistant is dormant or waiting for input.
- Displays the top-left globe icon and the keyboard shortcut hint:
  `Type or hold [alt] [control] to speak`
- Keycaps `alt` and `control` are styled as dark rounded keys (`#222226` background, `#d1d1d6` bold text, 5px radius).

### State 1: Active Typing View
- Triggered by clicking the hint row or pressing `Enter`.
- Seamlessly reveals a full-width input pill (`#16161c`, 34px height) with placeholder text.
- Supports slash commands (`/weather`, `/calc`, `/time`, `/sys`, `/persona`, `/mode`).
- `Tab` toggles between `[DICTATE]` and `[AGENT]` modes.
- `Esc` dismisses the typing view.

### State 2: Active Listening View
- Triggered by pressing `Ctrl + Shift + D` / `Ctrl + Alt + A` or holding `Alt + Ctrl`.
- Emits soft audio cue (900 Hz tone) and activates audio ducking.
- Animates real-time soundwave volume bars responsive to microphone RMS energy.

### State 3: Expanded Card View (AI Output & Weather)
- Features a top bar with the globe icon (left) and circular stop button (right).
- Displays the user query pill (`#16161c`) and a slate result card (`#252830`):
  - **Weather Card:** City name (bold 14px), large temperature (`25°C`), cloud icon, condition (`Overcast`), high/low range (`H:32° L:24°`).
  - **AI Card:** Streaming response text with neural speech playback.
- Automatically dismisses after 7–8 seconds or when clicking outside.

---

## 4. Signal Integration
| Signal | Signature | Purpose |
|---|---|---|
| `text_submitted` | `(str, int)` | Emits typed query text and mode (0: Dictate, 3: Agent) |
| `toggle_dictation_requested`| `()` | Requests toggling dictation audio capture |
| `toggle_agent_requested` | `()` | Requests toggling agent conversational audio capture |
| `toggle_history_requested` | `()` | Emitted when user clicks the globe icon to open History Drawer |
| `paste_requested` | `()` | Triggers synthetic clipboard injection |
| `mode_changed` | `(int)` | Notifies mode change (0: Dictate, 3: Agent) |
