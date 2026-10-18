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

- **Width:** 320px (Hidden) / 340px (Peek) / 480px (Expanded).
- **Height:** 4px (Hidden trigger) / 30px (Peek) / 125px (Expanded Idle) / 270px (Expanded Card).
- **Top Inverse Curves:** 34px wide $\times$ 24px high cubic bezier curves blending into $y = 0$.
- **Bottom Corners:** 30px radius.
- **Color:** Solid pure black `#000000`.

---

## 3. Three-State Interaction Lifecycle & Outside-Click Handling

### State A: Hidden (`STATE_HIDDEN` = 0)
- Dormant 320px $\times$ 4px hover-sensitive trigger bar docked at the primary monitor's top-center edge ($y = 0$).
- Child inputs and labels are hidden.
- Moving the cursor across the top center triggers an immediate, smooth transition to State B.

### State B: Peek (`STATE_PEEKING` = 1)
- Sleek 340px $\times$ 30px rounded notch silhouette with a subtle centered peek indicator.
- Allows hovering without revealing the full input interface.
- Includes a 600ms grace period on mouse leave before smoothly collapsing back to Hidden.
- Clicking anywhere on the peeked notch smoothly expands it into State C.

### State C: Expanded (`STATE_EXPANDED` = 2)
- Fully interactive Dynamic Island:
  - **Idle / Typing View (125px):** Features the glossy globe icon, hint row with dark keycaps `[alt]` and `[control]`, and full-height text input pill with zero vertical clipping.
  - **Expanded Card View (270px):** Features user query pill, slate result card (`#252830`), weather details or live streaming response chunks, and circular stop button.
- **Reliable Outside-Click Dismissal:**
  - Active in Expanded state with a 250ms expansion grace period.
  - Monitors global screen cursor position across multi-monitor setups.
  - Edge-triggered: clicking desktop, File Explorer, VS Code, browsers, or other applications collapses the notch back to Hidden.
  - Clicking inside the notch or typing inside the input field never triggers dismissal.

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
