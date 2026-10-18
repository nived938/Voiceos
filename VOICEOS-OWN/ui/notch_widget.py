import math
import winsound
import win32api
from PySide6.QtCore import Qt, QPropertyAnimation, QRect, QTimer, Signal, Slot, QEasingCurve, QEvent
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame,
    QLineEdit, QGraphicsDropShadowEffect, QStackedWidget
)
from PySide6.QtGui import QColor, QGuiApplication, QCursor, QKeyEvent

class NotchWidget(QWidget):
    """
    Advanced 1:1 VoiceOS Top Notch Dynamic Island Widget.
    Features:
    - Button-Free, ultra-minimal luxury OLED aesthetic.
    - 3-tier lifecycle: Hidden (dormant 4px trigger) -> Peeking (on hover) -> Expanded (on click).
    - Instant Click-Outside Auto-Dismissal: clicking anywhere outside the notch on any screen,
      window, or desktop instantly and smoothly collapses it.
    - Focus-loss & Escape key auto-dismiss.
    - Integrated direct typing interface with Tab mode switching and built-in slash commands.
    - Dynamic 5-bar soundwave visualizer responding to voice energy and speech synthesis.
    """

    STATE_HIDDEN = 0
    STATE_PEEKING = 1
    STATE_EXPANDED = 2

    # Dimensions
    HIDDEN_W = 280
    HIDDEN_H = 4

    PEEKING_W = 320
    PEEKING_H = 30

    EXPANDED_W = 620
    EXPANDED_H = 145

    # Signals for main application pipeline
    text_submitted = Signal(str, int)            # (text, mode: 0=Dictate, 3=Agent)
    toggle_dictation_requested = Signal()
    toggle_agent_requested = Signal()
    paste_requested = Signal()
    mode_changed = Signal(int)                   # (mode: 0 or 3)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self._state = self.STATE_HIDDEN
        self._current_mode = 0  # 0: Dictation, 3: Agent
        self._persona_name = "Jarvis"

        # Animations & Timers
        self._anim = QPropertyAnimation(self, b"geometry")
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._on_finished_callback = None
        self._anim.finished.connect(self._handle_anim_finished)

        self._collapse_timer = QTimer(self)
        self._collapse_timer.setSingleShot(True)
        self._collapse_timer.timeout.connect(self.collapse_to_hidden)

        self._peek_leave_timer = QTimer(self)
        self._peek_leave_timer.setSingleShot(True)
        self._peek_leave_timer.timeout.connect(self._on_peek_leave_timeout)

        # Global Click-Outside Monitor Timer (Runs at 35ms when notch is visible)
        self._outside_monitor_timer = QTimer(self)
        self._outside_monitor_timer.setInterval(35)
        self._outside_monitor_timer.timeout.connect(self._check_outside_click)

        self._init_ui()
        self._apply_initial_geometry()

    def _init_ui(self):
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        # Container Frame
        self.container = QFrame(self)
        self.container.setObjectName("notchRoot")
        self.container.setStyleSheet("""
            #notchRoot {
                background-color: #000000;
                border: 1px solid #2a2a2a;
                border-top: none;
                border-bottom-left-radius: 18px;
                border-bottom-right-radius: 18px;
            }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 240))
        shadow.setOffset(0, 8)
        self.container.setGraphicsEffect(shadow)

        self.stack = QStackedWidget(self.container)
        c_layout = QVBoxLayout(self.container)
        c_layout.setContentsMargins(0, 0, 0, 0)
        c_layout.addWidget(self.stack)

        # 1. Peeking View Widget
        self.peek_widget = self._build_peek_view()
        self.stack.addWidget(self.peek_widget)

        # 2. Expanded View Widget (Clean, Button-Free)
        self.expanded_widget = self._build_expanded_view()
        self.stack.addWidget(self.expanded_widget)

        root_layout.addWidget(self.container)

    def _build_peek_view(self) -> QWidget:
        w = QWidget()
        layout = QHBoxLayout(w)
        layout.setContentsMargins(14, 2, 14, 4)
        layout.setSpacing(8)

        # Indicator dot
        self.peek_dot = QLabel("●", w)
        self.peek_dot.setStyleSheet("color: #ffffff; font-size: 8px;")

        self.peek_title = QLabel("VOICEOS", w)
        self.peek_title.setStyleSheet("color: #ffffff; font-weight: 800; font-size: 11px; letter-spacing: 1px;")

        self.peek_status = QLabel("Click to open • Hover to peek", w)
        self.peek_status.setStyleSheet("color: #888888; font-size: 10px; font-weight: 500;")

        layout.addWidget(self.peek_dot)
        layout.addWidget(self.peek_title)
        layout.addStretch()
        layout.addWidget(self.peek_status)

        return w

    def _build_expanded_view(self) -> QWidget:
        w = QWidget()
        layout = QVBoxLayout(w)
        layout.setContentsMargins(16, 10, 16, 12)
        layout.setSpacing(6)

        # Top Bar: Brand + Mode Tag + Soundwave + Status (NO generic buttons!)
        top_bar = QHBoxLayout()
        top_bar.setSpacing(10)

        # Brand & Persona Label
        self.badge_label = QLabel(f"VOICEOS • {self._persona_name.upper()}", w)
        self.badge_label.setStyleSheet("""
            font-size: 11px; font-weight: 800; color: #ffffff;
            letter-spacing: 1px;
        """)

        # Minimalist Mode Tag (Clickable or Tab toggled)
        self.mode_tag = QLabel("[DICTATE]", w)
        self.mode_tag.setStyleSheet("""
            background-color: #1a1a1a; color: #ffffff;
            border: 1px solid #333333; border-radius: 4px;
            padding: 2px 8px; font-size: 10px; font-weight: 700;
        """)
        self.mode_tag.setCursor(Qt.CursorShape.PointingHandCursor)
        self.mode_tag.mousePressEvent = lambda e: self.toggle_mode()

        # Soundwave Bars (5 animated visualizer bars)
        self.wave_bars = []
        wave_container = QWidget(w)
        wave_layout = QHBoxLayout(wave_container)
        wave_layout.setContentsMargins(2, 0, 2, 0)
        wave_layout.setSpacing(3)
        for _ in range(5):
            bar = QFrame(wave_container)
            bar.setFixedWidth(3)
            bar.setFixedHeight(8)
            bar.setStyleSheet("background-color: #444444; border-radius: 1px;")
            wave_layout.addWidget(bar)
            self.wave_bars.append(bar)

        # Status Tag
        self.status_label = QLabel("Idle", w)
        self.status_label.setStyleSheet("color: #888888; font-size: 11px; font-weight: 500;")

        # Hint tag
        hint_label = QLabel("Esc to close", w)
        hint_label.setStyleSheet("color: #555555; font-size: 10px;")

        top_bar.addWidget(self.badge_label)
        top_bar.addWidget(self.mode_tag)
        top_bar.addWidget(wave_container)
        top_bar.addStretch()
        top_bar.addWidget(self.status_label)
        top_bar.addWidget(hint_label)
        layout.addLayout(top_bar)

        # Middle Row: Live Transcript & AI readout
        self.content_label = QLabel("Speak or type prompt below... [Tab to switch mode]", w)
        self.content_label.setWordWrap(True)
        self.content_label.setStyleSheet("color: #ffffff; font-size: 12px; font-weight: 500;")
        self.content_label.setFixedHeight(34)
        layout.addWidget(self.content_label)

        # Bottom Row: Full-width Seamless Input ("Typre Thing")
        self.type_input = QLineEdit(w)
        self.type_input.setObjectName("notchInput")
        self.type_input.setStyleSheet("""
            QLineEdit#notchInput {
                background-color: #0a0a0a;
                border: 1px solid #242424;
                border-radius: 8px;
                padding: 7px 12px;
                color: #ffffff;
                font-size: 12px;
            }
            QLineEdit#notchInput:focus {
                border: 1px solid #ffffff;
            }
        """)
        self.type_input.setPlaceholderText("Type prompt or text... [Enter ↵ submit • Tab ⇆ mode • Esc ✕ close]")
        self.type_input.returnPressed.connect(self._on_type_submit)
        self.type_input.installEventFilter(self)

        layout.addWidget(self.type_input)

        self._update_mode_style()
        return w

    def _update_mode_style(self):
        if hasattr(self, "mode_tag") and self.mode_tag:
            if self._current_mode == 0:
                self.mode_tag.setText("[DICTATE]")
                self.mode_tag.setStyleSheet("""
                    background-color: #ffffff; color: #000000;
                    border: 1px solid #ffffff; border-radius: 4px;
                    padding: 2px 8px; font-size: 10px; font-weight: 800;
                """)
                if hasattr(self, "type_input") and self.type_input:
                    self.type_input.setPlaceholderText("Type text to inject directly into active window... [Enter ↵ • Tab ⇆ • Esc ✕]")
            else:
                self.mode_tag.setText("[AGENT]")
                self.mode_tag.setStyleSheet("""
                    background-color: #1a1a1a; color: #ffffff;
                    border: 1px solid #444444; border-radius: 4px;
                    padding: 2px 8px; font-size: 10px; font-weight: 800;
                """)
                if hasattr(self, "type_input") and self.type_input:
                    self.type_input.setPlaceholderText("Ask Gemini assistant anything... [Enter ↵ • Tab ⇆ • Esc ✕]")

    def toggle_mode(self):
        new_mode = 3 if self._current_mode == 0 else 0
        self.set_mode(new_mode)

    def set_mode(self, mode: int):
        self._current_mode = mode
        self._update_mode_style()
        self.mode_changed.emit(mode)

    def set_persona(self, persona_name: str):
        self._persona_name = persona_name
        if hasattr(self, "badge_label") and self.badge_label:
            self.badge_label.setText(f"VOICEOS • {persona_name.upper()}")

    def _apply_initial_geometry(self):
        screen = QGuiApplication.primaryScreen()
        self.expanded_widget.hide()
        self.peek_widget.hide()
        self.setFixedHeight(self.HIDDEN_H)
        self.setFixedWidth(self.HIDDEN_W)
        if screen:
            screen_geom = screen.geometry()
            x = (screen_geom.width() - self.HIDDEN_W) // 2
            self.move(x, 0)
        self.show()

    def _handle_anim_finished(self):
        if self._on_finished_callback:
            cb = self._on_finished_callback
            self._on_finished_callback = None
            cb()

    # --- Geometry & Transitions ---
    def _animate_to(self, target_w: int, target_h: int, on_finished=None, animated: bool = True):
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return
        screen_geom = screen.geometry()
        target_x = (screen_geom.width() - target_w) // 2
        target_rect = QRect(target_x, 0, target_w, target_h)

        self.setMinimumSize(0, 0)
        self.setMaximumSize(16777215, 16777215)

        if not animated:
            self._anim.stop()
            self._on_finished_callback = None
            self.setFixedHeight(target_h)
            self.setFixedWidth(target_w)
            self.setGeometry(target_rect)
            if on_finished:
                on_finished()
            return

        self._anim.stop()
        self._anim.setStartValue(self.geometry())
        self._anim.setEndValue(target_rect)

        def _on_done():
            self.setFixedHeight(target_h)
            self.setFixedWidth(target_w)
            if on_finished:
                on_finished()

        self._on_finished_callback = _on_done
        self._anim.start()

    def transition_to_peeking(self, animated: bool = True):
        if self._state == self.STATE_EXPANDED:
            return
        self._state = self.STATE_PEEKING
        self.expanded_widget.hide()
        self.peek_widget.show()
        self.stack.setCurrentWidget(self.peek_widget)
        self._animate_to(self.PEEKING_W, self.PEEKING_H, animated=animated)
        self._outside_monitor_timer.start()

    def transition_to_expanded(self, animated: bool = True):
        self._state = self.STATE_EXPANDED
        self._collapse_timer.stop()
        self._peek_leave_timer.stop()
        self.peek_widget.hide()
        self.expanded_widget.show()
        self.stack.setCurrentWidget(self.expanded_widget)
        self._animate_to(self.EXPANDED_W, self.EXPANDED_H, on_finished=self._on_expanded_ready, animated=animated)
        self._outside_monitor_timer.start()

    def _on_expanded_ready(self):
        self.activateWindow()
        self.type_input.setFocus()

    def collapse_to_hidden(self, animated: bool = True):
        self._state = self.STATE_HIDDEN
        self._collapse_timer.stop()
        self._peek_leave_timer.stop()
        self._outside_monitor_timer.stop()
        self.type_input.clearFocus()
        self.expanded_widget.hide()
        self.peek_widget.hide()
        self._animate_to(self.HIDDEN_W, self.HIDDEN_H, animated=animated)

    def auto_collapse_after(self, ms: int = 5000):
        self._collapse_timer.start(ms)

    def closeEvent(self, event):
        self._outside_monitor_timer.stop()
        self._collapse_timer.stop()
        self._peek_leave_timer.stop()
        self._anim.stop()
        super().closeEvent(event)

    # --- Mouse & Event Handling ---
    def enterEvent(self, event):
        super().enterEvent(event)
        self._peek_leave_timer.stop()
        self._collapse_timer.stop()
        if self._state == self.STATE_HIDDEN:
            self.transition_to_peeking()

    def leaveEvent(self, event):
        super().leaveEvent(event)
        if self._state == self.STATE_PEEKING:
            self._peek_leave_timer.start(600)

    def _on_peek_leave_timeout(self):
        if self._state == self.STATE_PEEKING:
            self.collapse_to_hidden()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self._state == self.STATE_PEEKING:
                self.transition_to_expanded()
                event.accept()
                return
        super().mousePressEvent(event)

    def changeEvent(self, event):
        """Auto-collapse when the window loses active focus to another application."""
        super().changeEvent(event)
        if event.type() == QEvent.Type.ActivationChange:
            if not self.isActiveWindow() and self._state != self.STATE_HIDDEN:
                # User clicked outside or switched to another app
                self.collapse_to_hidden()

    def _check_outside_click(self):
        """
        Global check for mouse clicks outside the Notch bounding box.
        Runs while Notch is peeking or expanded.
        """
        if self._state == self.STATE_HIDDEN:
            self._outside_monitor_timer.stop()
            return

        cursor_pos = QCursor.pos()
        # 1. Detect if user clicked anywhere (Left or Right mouse button)
        l_down = bool(win32api.GetAsyncKeyState(0x01) & 0x8000)
        r_down = bool(win32api.GetAsyncKeyState(0x02) & 0x8000)

        if l_down or r_down:
            if not self.geometry().contains(cursor_pos):
                self.collapse_to_hidden()
                return

        # 2. If in PEEKING state and cursor moved far down, dismiss
        if self._state == self.STATE_PEEKING:
            if cursor_pos.y() > (self.PEEKING_H + 50):
                self.collapse_to_hidden()

    def eventFilter(self, watched, event):
        """Handles Tab and Escape inside the type_input field."""
        if hasattr(self, "type_input") and self.type_input and watched == self.type_input:
            if event.type() == QEvent.Type.KeyPress:
                if event.key() == Qt.Key.Key_Escape:
                    self.collapse_to_hidden()
                    return True
                elif event.key() == Qt.Key.Key_Tab:
                    self.toggle_mode()
                    return True
        return super().eventFilter(watched, event)

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key.Key_Escape:
            self.collapse_to_hidden()
            event.accept()
        elif event.key() == Qt.Key.Key_Tab:
            self.toggle_mode()
            event.accept()
        else:
            super().keyPressEvent(event)

    # --- Actions & Submissions ---
    def _on_type_submit(self):
        text = self.type_input.text().strip()
        if not text:
            return

        # Built-in Slash Commands Handling
        if text.startswith("/"):
            self._handle_slash_command(text)
            self.type_input.clear()
            return

        # Submit regular text or agent query
        self.text_submitted.emit(text, self._current_mode)
        self.type_input.clear()

    def _handle_slash_command(self, cmd_text: str):
        parts = cmd_text.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if cmd in ["/help", "/?"]:
            self.content_label.setText("Commands: /mode, /weather <city>, /calc <math>, /time, /sys, /copy, /paste, /clear, /persona <name>")
        elif cmd == "/mode":
            self.toggle_mode()
            self.content_label.setText(f"Mode switched to: {self.mode_tag.text()}")
        elif cmd == "/clear":
            self.content_label.setText("")
            self.status_label.setText("Cleared")
        elif cmd == "/paste":
            self.paste_requested.emit()
        elif cmd == "/copy":
            import pyperclip
            pyperclip.copy(self.content_label.text())
            self.status_label.setText("Copied!")
        elif cmd == "/persona" and arg:
            self.set_persona(arg.capitalize())
            self.content_label.setText(f"Voice persona updated to: {arg.capitalize()}")
        elif cmd == "/time":
            from datetime import datetime
            now_str = datetime.now().strftime("%A, %B %d %Y - %I:%M:%S %p")
            self.content_label.setText(f"🕒 {now_str}")
            self.status_label.setText("Local Time")
        elif cmd == "/calc" and arg:
            from ai.tools import calculate
            res = calculate(arg)
            self.content_label.setText(f"Result: {res}")
            self.status_label.setText("Calculator")
        elif cmd == "/sys":
            from ai.tools import system_status
            res = system_status()
            self.content_label.setText(f"System: {res}")
            self.status_label.setText("Diagnostics")
        elif cmd == "/weather" and arg:
            # Route to agent
            self.text_submitted.emit(f"What is the weather in {arg}?", 3)
        else:
            # Send unknown slash command to agent
            self.text_submitted.emit(cmd_text, self._current_mode)

    # --- Status Updates ---
    def set_status(self, status: str, tool: str = ""):
        self.status_label.setText(tool or status)
        self.peek_status.setText(status)

    def update_text(self, text: str):
        self.content_label.setText(text)

    def expand(self, text: str = "", tool: str = "", status: str = "Active"):
        self.set_status(status, tool)
        if text:
            self.content_label.setText(text)
        self.transition_to_expanded()

    def set_volume_level(self, level: float):
        """Animates 5 soundwave bars based on volume level (0.0 to 1.0)."""
        if self._state != self.STATE_EXPANDED:
            return

        clamped = max(0.0, min(1.0, level))
        for i, bar in enumerate(self.wave_bars):
            factor = math.sin((i / 4.0) * math.pi) * 0.8 + 0.2
            h = int(6 + (clamped * 20 * factor))
            bar.setFixedHeight(h)
            if clamped > 0.05:
                bar.setStyleSheet("background-color: #ffffff; border-radius: 1px;")
            else:
                bar.setStyleSheet("background-color: #444444; border-radius: 1px;")

    def set_listening(self, listening: bool):
        if listening:
            try:
                winsound.Beep(900, 60)
            except Exception:
                pass
            self.set_status("Listening...")
            self.peek_dot.setStyleSheet("color: #ffffff; font-size: 9px;")
        else:
            try:
                winsound.Beep(700, 60)
            except Exception:
                pass
            for bar in self.wave_bars:
                bar.setFixedHeight(6)
                bar.setStyleSheet("background-color: #444444; border-radius: 1px;")

    def set_thinking(self):
        self.set_status("Gemini Thinking...")
        for bar in self.wave_bars:
            bar.setFixedHeight(10)
            bar.setStyleSheet("background-color: #888888; border-radius: 1px;")

    def set_speaking(self):
        self.set_status(f"{self._persona_name} Speaking...")
        for bar in self.wave_bars:
            bar.setFixedHeight(14)
            bar.setStyleSheet("background-color: #ffffff; border-radius: 1px;")
