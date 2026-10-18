# VoiceOS 1:1 Visual Specification & Design System

## 1. Design Overview
The VoiceOS interface is designed with a pure monochromatic OLED palette (`#000000`), subtle slate containers, and minimal white/gray typography. Distracting window chrome, headers, and standard buttons are replaced by two primary floating surfaces:
1. **The Floating Top Notch Dynamic Island** (centered at screen top, $y = 0$).
2. **The Floating Left-Side Chat History Panel** (docked at screen left edge, $x = 0, y = 58$).

---

## 2. Color System & Palette

| Token | Hex Code | Purpose |
|---|---|---|
| `Black Surface` | `#000000` | Primary backdrop for Top Notch and History Drawer |
| `Dark Pill` | `#16161c` | Search input, lock button, query pill background |
| `Card Slate` | `#252830` | Weather and AI response cards |
| `Keycap Dark` | `#222226` | Background for `alt` and `control` keyboard keycaps |
| `Selected Row` | `#1a1a24` | Active conversation selection in History Drawer |
| `Hover Row` | `#121216` | Hover state for history drawer items |
| `Text Primary` | `#ffffff` | Headings, conversation titles, temperature numbers |
| `Text Keycap` | `#d1d1d6` | Bold keycap labels (`alt`, `control`) |
| `Text Secondary`| `#8a8a8e` | Hint labels ("Type or hold", "to speak", "H:32° L:24°") |
| `Text Muted` | `#68686e` | Date/time group headings ("Today, 6:05 PM") |
| `Search Placeholder` | `#777782` | Input field placeholder text |

---

## 3. Top Notch Dynamic Island

### 3.1 Dimensions & Silhouette
- **Idle / Peeking Width:** 480px (with 34px inverse ears extending to top edge).
- **Idle Height:** 82px.
- **Expanded Width:** 520px.
- **Expanded Height:** 270px.
- **Bottom Corner Radius:** 30px.
- **Top Inverse Flare ('Ears'):**
  - Ear Width: 34px.
  - Ear Height: 24px.
  - Smooth cubic bezier transitions flush with $y = 0$.

### 3.2 Keycap Hint Row
- Positioned directly below the globe icon in idle mode:
  `Type or hold [alt] [control] to speak`
- `Type or hold` & `to speak`: `#8a8a8e`, 12px Segoe UI.
- `alt` & `control` Keycaps:
  - Background: `#222226`
  - Text: `#d1d1d6`, 10px bold
  - Border radius: 5px
  - Height: 18px
  - Padding: 2px 7px

### 3.3 Expanded Card Hierarchy
- **Row 1:** 18x18px glossy globe icon (left) + 24x24px `#1e1e24` circular stop button with white square (right).
- **Row 2:** `#16161c` 36px query pill with white prompt text (e.g., `what is the weather`).
- **Row 3:** `#252830` Slate Result Card (weather metrics or streaming assistant text).
- **Row 4:** Hint row with `[alt]` and `[control]` keycaps.

---

## 4. Floating Left-Side Chat History Panel

### 4.1 Dimensions & Geometry
- **Width:** 232px.
- **Height:** 516px at reference scale (responsive to display scaling).
- **Position:** Docked at $x = 0$, starting $y = 58$px below monitor top edge.
- **Corner Radius:** 26px on outer edges.
- **Background:** `#000000`.

### 4.2 Search & Pin Row
- **Search Pill:** `#16161c`, height 34px, radius 17px, embedded magnifying glass icon (`#777782`), placeholder "Search".
- **Lock Button:** 34x34px circular control (`#16161c`), vector padlock icon.
  - *Unlocked (Open Shackle):* Auto-dismisses when clicking outside.
  - *Locked (Closed Shackle):* Pinned in place, ignores outside clicks.

### 4.3 Group Headings & Conversation Items
- **Group Heading:** `#68686e`, 11px bold, formatted from conversation timestamps (e.g. `Today, 6:05 PM`, `Today, 2:56 PM`).
- **Row Height:** 34px.
- **Icon:** 18x18px glossy globe icon, vertically centered.
- **Title:** `#ffffff`, 13px, single line with ellipsis truncation.
- **Selected State:** `#1a1a24` rounded background (radius 9px).
- **Scrollbar:** Hidden (`ScrollBarAlwaysOff`), full wheel-scrolling support.
