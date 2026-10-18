# VoiceOS Floating Chat History Panel Specification

## 1. Overview
The Floating Chat History Panel (`HistoryDrawer`) provides an accessible, non-intrusive drawer of previous voice and text conversations. Positioned on the left side of the screen, it offers real-time search filtering, chronological grouping, persistent SQLite backing, and single-click conversation restoration.

---

## 2. Technical Characteristics

- **Component:** `ui.history_drawer.HistoryDrawer`
- **Parent Window:** Top-level frameless tool window (`FramelessWindowHint | WindowStaysOnTopHint | Tool`).
- **Transparency:** `Qt.WidgetAttribute.WA_TranslucentBackground`.
- **Dimensions:** 232px width $\times$ 516px height.
- **Screen Offset:** $x = 0$, $y = 58$px from primary monitor top.
- **Corner Radius:** 26px rounded corners.

---

## 3. Key Capabilities

### 3.1 Real-Time Search Filtering
- Integrated search pill with magnifying glass vector icon.
- Filters conversations instantly as the user types across:
  - User query / speech transcript.
  - Assistant generated response.
  - Generated conversation title.
- Displays a clean "No conversations found" label when filters yield zero results.

### 3.2 Pin / Lock Mechanism
- The circular lock button toggles the panel's dismissal behavior:
  - **Unpinned (Default):** Outside mouse clicks detected via Win32 `GetAsyncKeyState` smoothly collapse the panel.
  - **Pinned (Locked):** Outside clicks are ignored; the panel remains persistent on screen above all windows.
- The button dynamically renders an open or closed padlock vector based on state.

### 3.3 Dynamic Date & Time Grouping
Rather than displaying arbitrary dates or unorganized lists, timestamps are parsed from SQLite ISO 8601 strings into human-friendly buckets:
- `Today, 6:05 PM`
- `Today, 2:56 PM`
- `Yesterday, 4:10 PM`
- `Oct 16, 11:30 AM`

### 3.4 Smart Title Generation
Titles are generated automatically using heuristic synthesis:
1. Weather inquiries $\rightarrow$ `"{City} Weather Forecast"` / `"{City} Weather Fore..."`.
2. Language switches $\rightarrow$ `"Malayalam Language Swi..."`.
3. Greetings $\rightarrow$ `"Initial User Greeting"` / `"Greeting and Introduction"`.
4. Name confirmations $\rightarrow$ `"Nived Name Confirmation"`.
5. Long general prompts $\rightarrow$ Clean capitalization, word boundary clipping, and single-line ellipsis (`...`) truncation.

### 3.5 Conversation Restoration
When a conversation item is clicked:
1. Row highlights with `#1a1a24` background.
2. Emits `session_selected(session_data)` signal.
3. Restores prompt and answer into the Top Notch dynamic island (or weather card if meteorological).
4. Copies response text to the system clipboard for immediate pasting.

---

## 4. Integration with Main Application
- **Toggle Triggers:**
  - Clicking the globe icon in the Top Notch.
  - Pressing global hotkey `Alt + ` ` (VK_OEM_3).
  - Clicking "History" in the Dashboard.
- **Lifecycle:** Opening or closing the history panel never interrupts active audio capture, speech synthesis, or ongoing Gemini queries.
