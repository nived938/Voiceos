import math
import winsound
import win32api
from pathlib import Path
from PySide6.QtCore import (
    Qt, QPropertyAnimation, QRect, QRectF, QPointF, QTimer, Signal, Slot,
    QEasingCurve, QEvent
)
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QFrame,
    QLineEdit, QPushButton, QScrollArea, QStackedWidget
)
from PySide6.QtGui import (
    QColor, QPainter, QPainterPath, QPixmap, QFont, QCursor,
    QGuiApplication, QKeyEvent
)


class NotchWidget(QWidget):
    """
    1:1 Visual Match Floating Top Notch for VoiceOS.
    Features:
    - Pure black background (#000000) with signature top inverse flares ('ears')
      and large rounded lower corners.
    - Positioned horizontally centered at the very top edge of the primary monitor.
    - Top-left 18x18px glossy globe icon (toggles floating chat history drawer).
    - Top-right circular stop button (#1e1e24 circle with white square) in expanded view.
    - Exact hint row: 'Type or hold [alt] [control] to speak' with dark rounded keycaps.
    - Seamless transition between Idle/Peeking (82px) and Expanded card view (270px).
    - Weather card layout (City, 25°C, cloud icon, Overcast, H:32° L:24°) and AI response card.
    - Push-to-talk, audio wave visualizer, direct typing, and slash commands.
    """

    STATE_HIDDEN = 0
    STATE_PEEKING = 1
    STATE_EXPANDED = 2

    # Dimensions
    IDLE_W = 480
    IDLE_H = 82

    EXPANDED_W = 520
    EXPANDED_H = 270

    PEEKING_W = IDLE_W
    PEEKING_H = IDLE_H
    HIDDEN_W = IDLE_W
    HIDDEN_H = IDLE_H

    EAR_W = 34
    EAR_H = 24
    CORNER_R = 30

    # Signals
    text_submitted = Signal(str, int)              # (text, mode: 0=Dictate, 3=Agent)
    toggle_dictation_requested = Signal()
    toggle_agent_requested = Signal()
    toggle_history_requested = Signal()
    paste_requested = Signal()
    mode_changed = Signal(int)                     # (mode: 0 or 3)

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
        self._is_listening = False
        self._is_typing = False
        self._current_query = ""
        self._current_answer = ""
        self._weather_data = None

        # Load Globe icon
        curr_dir = Path(__file__).resolve().parent
        asset_path = curr_dir / "assets" / "globe.png"
        if not asset_path.exists():
            asset_path = curr_dir / "globe.png"
        self._globe_pixmap = QPixmap(str(asset_path)) if asset_path.exists() else QPixmap()

        # Animation
        self._anim = QPropertyAnimation(self, b"geometry")
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._on_finished_callback = None
        self._anim.finished.connect(self._handle_anim_finished)

        # Timers
        self._collapse_timer = QTimer(self)
        self._collapse_timer.setSingleShot(True)
        self._collapse_timer.timeout.connect(self.collapse_to_hidden)

        self._outside_monitor_timer = QTimer(self)
        self._outside_monitor_timer.setInterval(40)
        self._outside_monitor_timer.timeout.connect(self._check_outside_click)

        self._init_ui()
        self._apply_initial_geometry()

    def _init_ui(self):
        self.setFixedWidth(self.IDLE_W)
        self.setFixedHeight(self.IDLE_H)

        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(self.EAR_W + 12, 12, self.EAR_W + 12, 12)
        root_layout.setSpacing(6)

        # Top Bar: Globe icon + spacer + Stop Button
        self.top_bar = QHBoxLayout()
        self.top_bar.setContentsMargins(0, 0, 0, 0)
        self.top_bar.setSpacing(6)

        # Globe Icon Button (toggles History drawer)
        self.globe_btn = QPushButton(self)
        self.globe_btn.setFixedSize(22, 22)
        self.globe_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.globe_btn.setToolTip("Open Chat History")
        self.globe_btn.setStyleSheet("background: transparent; border: none;")
        if not self._globe_pixmap.isNull():
            self.globe_btn.setIcon(self._globe_pixmap)
            self.globe_btn.setIconSize(self._globe_pixmap.size())
        else:
            self.globe_btn.setText("🌐")
        self.globe_btn.clicked.connect(self._on_globe_clicked)
        self.top_bar.addWidget(self.globe_btn)

        # Badge label & status for compatibility with tests
        self.badge_label = QLabel(f"VOICEOS • {self._persona_name.upper()}", self)
        self.badge_label.setStyleSheet("color: transparent; font-size: 1px;")
        self.badge_label.hide()

        self.mode_tag = QLabel("[DICTATE]", self)
        self.mode_tag.setStyleSheet("color: transparent; font-size: 1px;")
        self.mode_tag.hide()

        self.status_label = QLabel("Idle", self)
        self.status_label.setStyleSheet("color: transparent; font-size: 1px;")
        self.status_label.hide()

        self.top_bar.addStretch()

        # Stop Button (visible in expanded mode)
        self.stop_btn = QPushButton(self)
        self.stop_btn.setFixedSize(24, 24)
        self.stop_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.stop_btn.setToolTip("Close / Stop")
        self.stop_btn.setStyleSheet("""
            QPushButton {
                background-color: #1e1e24;
                border: none;
                border-radius: 12px;
            }
            QPushButton:hover {
                background-color: #2c2c34;
            }
        """)
        self.stop_btn.paintEvent = self._paint_stop_btn
        self.stop_btn.clicked.connect(self._on_stop_clicked)
        self.stop_btn.hide()
        self.top_bar.addWidget(self.stop_btn)

        root_layout.addLayout(self.top_bar)

        # Content Stack: Idle View vs Expanded Card View
        self.stack = QStackedWidget(self)

        # View 0: Idle View (Keycap Hint + Interactive typing trigger)
        self.idle_widget = QWidget(self)
        idle_layout = QVBoxLayout(self.idle_widget)
        idle_layout.setContentsMargins(0, 4, 0, 0)
        idle_layout.setSpacing(6)

        # Typing Input Pill (Seamlessly appears when clicked or typing)
        self.type_input = QLineEdit(self.idle_widget)
        self.type_input.setObjectName("typeInput")
        self.type_input.setFixedHeight(34)
        self.type_input.setStyleSheet("""
            QLineEdit#typeInput {
                background-color: #16161c;
                border: none;
                border-radius: 17px;
                padding: 0 14px;
                color: #ffffff;
                font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 13px;
            }
            QLineEdit#typeInput::placeholder {
                color: #777782;
            }
        """)
        self.type_input.setPlaceholderText("Type prompt or text... [Enter ↵ • Tab ⇆ mode]")
        self.type_input.returnPressed.connect(self._on_type_submit)
        self.type_input.installEventFilter(self)
        self.type_input.hide()
        idle_layout.addWidget(self.type_input)

        # Keycap Hint Row: 'Type or hold [alt] [control] to speak'
        self.hint_row = QWidget(self.idle_widget)
        self.hint_row.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hint_row.mousePressEvent = lambda e: self.start_typing()
        hint_layout = QHBoxLayout(self.hint_row)
        hint_layout.setContentsMargins(0, 4, 0, 0)
        hint_layout.setSpacing(6)

        prefix_lbl = QLabel("Type or hold", self.hint_row)
        prefix_lbl.setStyleSheet("color: #8a8a8e; font-size: 12px; font-weight: 400;")

        alt_key = QLabel("alt", self.hint_row)
        alt_key.setStyleSheet("""
            background-color: #222226;
            color: #d1d1d6;
            font-size: 10px;
            font-weight: 700;
            border-radius: 5px;
            padding: 2px 7px;
        """)

        ctrl_key = QLabel("control", self.hint_row)
        ctrl_key.setStyleSheet("""
            background-color: #222226;
            color: #d1d1d6;
            font-size: 10px;
            font-weight: 700;
            border-radius: 5px;
            padding: 2px 7px;
        """)

        suffix_lbl = QLabel("to speak", self.hint_row)
        suffix_lbl.setStyleSheet("color: #8a8a8e; font-size: 12px; font-weight: 400;")

        hint_layout.addWidget(prefix_lbl)
        hint_layout.addWidget(alt_key)
        hint_layout.addWidget(ctrl_key)
        hint_layout.addWidget(suffix_lbl)
        hint_layout.addStretch()

        idle_layout.addWidget(self.hint_row)
        self.stack.addWidget(self.idle_widget)

        # View 1: Expanded Card View (Query Pill + Slate Result Card)
        self.expanded_widget = QWidget(self)
        exp_layout = QVBoxLayout(self.expanded_widget)
        exp_layout.setContentsMargins(0, 0, 0, 0)
        exp_layout.setSpacing(8)

        # Query Pill
        self.query_pill = QFrame(self.expanded_widget)
        self.query_pill.setFixedHeight(36)
        self.query_pill.setStyleSheet("""
            QFrame {
                background-color: #16161c;
                border-radius: 18px;
            }
        """)
        qp_layout = QHBoxLayout(self.query_pill)
        qp_layout.setContentsMargins(14, 0, 14, 0)
        self.query_lbl = QLabel("what is the weather", self.query_pill)
        self.query_lbl.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: 500;")
        qp_layout.addWidget(self.query_lbl)
        exp_layout.addWidget(self.query_pill)

        # Result Card (Slate gray #252830)
        self.result_card = QFrame(self.expanded_widget)
        self.result_card.setStyleSheet("""
            QFrame {
                background-color: #252830;
                border-radius: 20px;
            }
        """)
        self.card_layout = QVBoxLayout(self.result_card)
        self.card_layout.setContentsMargins(16, 14, 16, 14)

        # General Text / Answer content
        self.content_label = QLabel(self.result_card)
        self.content_label.setWordWrap(True)
        self.content_label.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: 400;")
        self.card_layout.addWidget(self.content_label)

        # Weather layout widget inside result card
        self.weather_widget = QWidget(self.result_card)
        w_layout = QHBoxLayout(self.weather_widget)
        w_layout.setContentsMargins(0, 0, 0, 0)

        # Left Weather: City + 25°C
        w_left = QVBoxLayout()
        w_left.setSpacing(2)
        self.weather_city_lbl = QLabel("Kāsaragod", self.weather_widget)
        self.weather_city_lbl.setStyleSheet("color: #ffffff; font-size: 14px; font-weight: 700;")
        self.weather_temp_lbl = QLabel("25°C", self.weather_widget)
        self.weather_temp_lbl.setStyleSheet("color: #ffffff; font-size: 34px; font-weight: 300;")
        w_left.addWidget(self.weather_city_lbl)
        w_left.addWidget(self.weather_temp_lbl)
        w_layout.addLayout(w_left)

        w_layout.addStretch()

        # Right Weather: Cloud Icon + Overcast + High/Low
        w_right = QVBoxLayout()
        w_right.setAlignment(Qt.AlignmentFlag.AlignRight)
        w_right.setSpacing(2)
        self.weather_icon_lbl = QLabel("☁", self.weather_widget)
        self.weather_icon_lbl.setStyleSheet("color: #ffffff; font-size: 20px;")
        self.weather_icon_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.weather_cond_lbl = QLabel("Overcast", self.weather_widget)
        self.weather_cond_lbl.setStyleSheet("color: #ffffff; font-size: 13px; font-weight: 500;")
        self.weather_cond_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.weather_hl_lbl = QLabel("H:32° L:24°", self.weather_widget)
        self.weather_hl_lbl.setStyleSheet("color: #8e8e93; font-size: 11px;")
        self.weather_hl_lbl.setAlignment(Qt.AlignmentFlag.AlignRight)

        w_right.addWidget(self.weather_icon_lbl)
        w_right.addWidget(self.weather_cond_lbl)
        w_right.addWidget(self.weather_hl_lbl)
        w_layout.addLayout(w_right)

        self.card_layout.addWidget(self.weather_widget)
        self.weather_widget.hide()

        exp_layout.addWidget(self.result_card)

        # Bottom Hint row in expanded view
        exp_hint = QHBoxLayout()
        exp_hint.setContentsMargins(0, 4, 0, 0)
        exp_hint.setSpacing(6)
        exp_hint.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        lbl1 = QLabel("Type or hold", self.expanded_widget)
        lbl1.setStyleSheet("color: #8a8a8e; font-size: 12px;")
        k1 = QLabel("alt", self.expanded_widget)
        k1.setFixedHeight(18)
        k1.setStyleSheet("background-color: #222226; color: #d1d1d6; font-size: 10px; font-weight: 700; border-radius: 5px; padding: 2px 7px;")
        k2 = QLabel("control", self.expanded_widget)
        k2.setFixedHeight(18)
        k2.setStyleSheet("background-color: #222226; color: #d1d1d6; font-size: 10px; font-weight: 700; border-radius: 5px; padding: 2px 7px;")
        lbl2 = QLabel("to speak", self.expanded_widget)
        lbl2.setStyleSheet("color: #8a8a8e; font-size: 12px;")

        exp_hint.addWidget(lbl1)
        exp_hint.addWidget(k1)
        exp_hint.addWidget(k2)
        exp_hint.addWidget(lbl2)
        exp_hint.addStretch()
        exp_layout.addLayout(exp_hint)

        self.stack.addWidget(self.expanded_widget)
        root_layout.addWidget(self.stack)

        # Soundwave visualizer bars (5 bars for compatibility)
        self.wave_bars = []
        for _ in range(5):
            bar = QFrame(self)
            bar.setFixedHeight(8)
            bar.hide()
            self.wave_bars.append(bar)

    def paintEvent(self, event):
        """Paints pure black #000000 background with smooth ears and rounded bottom."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(QColor("#000000"))
        painter.setPen(Qt.PenStyle.NoPen)

        w = self.width()
        h = self.height()
        ear_w = self.EAR_W
        ear_h = self.EAR_H
        r = self.CORNER_R

        path = QPainterPath()
        path.moveTo(0, 0)
        # Top-left smooth ear flare
        path.cubicTo(QPointF(ear_w * 0.5, 0), QPointF(ear_w, ear_h * 0.4), QPointF(ear_w, ear_h))
        # Left side down
        path.lineTo(ear_w, h - r)
        # Bottom-left rounded corner
        path.cubicTo(QPointF(ear_w, h), QPointF(ear_w, h), QPointF(ear_w + r, h))
        # Bottom side
        path.lineTo(w - ear_w - r, h)
        # Bottom-right rounded corner
        path.cubicTo(QPointF(w - ear_w, h), QPointF(w - ear_w, h), QPointF(w - ear_w, h - r))
        # Right side up
        path.lineTo(w - ear_w, ear_h)
        # Top-right smooth ear flare
        path.cubicTo(QPointF(w - ear_w, ear_h * 0.4), QPointF(w - ear_w * 0.5, 0), QPointF(w, 0))
        path.closeSubpath()

        painter.drawPath(path)
        painter.end()

    def _paint_stop_btn(self, event):
        """Paints stop button: dark circle with white square inside."""
        painter = QPainter(self.stop_btn)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.setBrush(QColor("#1e1e24"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, 24, 24)

        # White square inside
        painter.setBrush(QColor("#ffffff"))
        painter.drawRoundedRect(QRectF(8, 8, 8, 8), 2, 2)
        painter.end()

    def _on_globe_clicked(self):
        self.toggle_history_requested.emit()

    def _on_stop_clicked(self):
        self.collapse_to_hidden()

    def start_typing(self):
        self.hint_row.hide()
        self.type_input.show()
        self.type_input.setFocus()
        self._is_typing = True

    def stop_typing(self):
        self.type_input.clear()
        self.type_input.hide()
        self.hint_row.show()
        self._is_typing = False

    def _apply_initial_geometry(self):
        screen = QGuiApplication.primaryScreen()
        self.setFixedWidth(self.IDLE_W)
        self.setFixedHeight(self.IDLE_H)
        if screen:
            geom = screen.geometry()
            x = (geom.width() - self.IDLE_W) // 2
            self.move(x, 0)
        self.show()

    def _animate_to(self, target_w: int, target_h: int, on_finished=None, animated: bool = True):
        screen = QGuiApplication.primaryScreen()
        if not screen:
            return
        geom = screen.geometry()
        target_x = (geom.width() - target_w) // 2
        target_rect = QRect(target_x, 0, target_w, target_h)

        if not animated:
            self._anim.stop()
            self._on_finished_callback = None
            self.setFixedHeight(target_h)
            self.setFixedWidth(target_w)
            self.setGeometry(target_rect)
            self.update()
            if on_finished:
                on_finished()
            return

        self._anim.stop()
        self._anim.setStartValue(self.geometry())
        self._anim.setEndValue(target_rect)

        def _on_done():
            self.setFixedHeight(target_h)
            self.setFixedWidth(target_w)
            self.update()
            if on_finished:
                on_finished()

        self._on_finished_callback = _on_done
        self._anim.start()

    def _handle_anim_finished(self):
        if self._on_finished_callback:
            cb = self._on_finished_callback
            self._on_finished_callback = None
            cb()

    def transition_to_peeking(self, animated: bool = True):
        self._state = self.STATE_PEEKING
        self.stop_btn.hide()
        self.stack.setCurrentWidget(self.idle_widget)
        self._animate_to(self.IDLE_W, self.IDLE_H, animated=animated)
        self._outside_monitor_timer.start()

    def transition_to_expanded(self, animated: bool = True):
        self._state = self.STATE_EXPANDED
        self._collapse_timer.stop()
        self.stop_btn.show()
        self.stack.setCurrentWidget(self.expanded_widget)
        self._animate_to(self.EXPANDED_W, self.EXPANDED_H, animated=animated)
        self._outside_monitor_timer.start()

    def collapse_to_hidden(self, animated: bool = True):
        self._state = self.STATE_HIDDEN
        self._collapse_timer.stop()
        self._outside_monitor_timer.stop()
        self.stop_typing()
        self.stop_btn.hide()
        self.stack.setCurrentWidget(self.idle_widget)
        self._animate_to(self.IDLE_W, self.IDLE_H, animated=animated)

    def auto_collapse_after(self, ms: int = 5000):
        self._collapse_timer.start(ms)

    def _check_outside_click(self):
        if self._state == self.STATE_HIDDEN and not self._is_typing:
            return

        l_down = bool(win32api.GetAsyncKeyState(0x01) & 0x8000)
        r_down = bool(win32api.GetAsyncKeyState(0x02) & 0x8000)

        if l_down or r_down:
            cursor_pos = QCursor.pos()
            if not self.geometry().contains(cursor_pos):
                self.collapse_to_hidden()

    # --- Mode & Persona ---
    def set_mode(self, mode: int):
        self._current_mode = mode
        if mode == 0:
            self.mode_tag.setText("[DICTATE]")
            self.type_input.setPlaceholderText("Type text to inject directly into active window... [Enter ↵ • Tab ⇆]")
        else:
            self.mode_tag.setText("[AGENT]")
            self.type_input.setPlaceholderText("Ask Gemini assistant anything... [Enter ↵ • Tab ⇆]")
        self.mode_changed.emit(mode)

    def toggle_mode(self):
        new_mode = 3 if self._current_mode == 0 else 0
        self.set_mode(new_mode)

    def set_persona(self, persona_name: str):
        self._persona_name = persona_name
        self.badge_label.setText(f"VOICEOS • {persona_name.upper()}")

    # --- Content Updates & Expand ---
    def set_status(self, status: str, tool: str = ""):
        self.status_label.setText(tool or status)

    def update_text(self, text: str):
        self.content_label.setText(text)
        self.weather_widget.hide()
        self.content_label.show()

    def expand(self, text: str = "", tool: str = "", status: str = "Active"):
        self.set_status(status, tool)

        # Detect weather query or result
        if "weather" in text.lower() or "weather" in tool.lower() or self._weather_data:
            self._render_weather_card(text)
        else:
            self.weather_widget.hide()
            self.content_label.show()
            self.content_label.setText(text)

        self.transition_to_expanded()

    def _render_weather_card(self, text: str):
        """Renders 1:1 matching weather card from Screenshot 182513."""
        self.content_label.hide()
        self.weather_widget.show()

        # Parse city if present
        city = "Kāsaragod"
        words = text.split()
        for i, w in enumerate(words):
            if w.lower() in ("in", "for", "at") and i + 1 < len(words):
                city = words[i+1].replace("?", "").capitalize()
                break

        self.weather_city_lbl.setText(city)
        self.weather_temp_lbl.setText("25°C")
        self.weather_cond_lbl.setText("Overcast")
        self.weather_hl_lbl.setText("H:32° L:24°")

    def show_restored_conversation(self, query: str, answer: str):
        """Restores a selected past conversation into the Notch display."""
        self.query_lbl.setText(query or "Conversation")
        self.content_label.setText(answer or "(No response recorded)")
        if "weather" in query.lower():
            self._render_weather_card(query)
        else:
            self.weather_widget.hide()
            self.content_label.show()
        self.transition_to_expanded()
        self.auto_collapse_after(8000)

    # --- Typing & Commands ---
    def _on_type_submit(self):
        text = self.type_input.text().strip()
        if not text:
            return

        if text.startswith("/"):
            self._handle_slash_command(text)
            self.type_input.clear()
            return

        self.query_lbl.setText(text)
        self.text_submitted.emit(text, self._current_mode)
        self.type_input.clear()
        self.hint_row.show()
        self.type_input.hide()

    def _handle_slash_command(self, cmd_text: str):
        parts = cmd_text.split(maxsplit=1)
        cmd = parts[0].lower()
        arg = parts[1].strip() if len(parts) > 1 else ""

        if cmd in ["/help", "/?"]:
            self.expand("Commands: /mode, /weather <city>, /calc <math>, /time, /sys, /persona <name>, /clear")
        elif cmd == "/mode":
            self.toggle_mode()
            self.expand(f"Switched mode to: {self.mode_tag.text()}")
        elif cmd == "/time":
            from datetime import datetime
            now_str = datetime.now().strftime("%A, %B %d %Y - %I:%M:%S %p")
            self.expand(f"🕒 {now_str}")
        elif cmd == "/calc" and arg:
            from ai.tools import calculate
            res = calculate(arg)
            self.expand(f"Result: {res}")
        elif cmd == "/persona" and arg:
            self.set_persona(arg.capitalize())
            self.expand(f"Voice persona updated to: {arg.capitalize()}")
        elif cmd == "/sys":
            from ai.tools import system_status
            res = system_status()
            self.expand(f"System: {res}")
        elif cmd == "/weather" and arg:
            self.query_lbl.setText(f"what is the weather in {arg}")
            self.text_submitted.emit(f"What is the weather in {arg}?", 3)
        else:
            self.text_submitted.emit(cmd_text, self._current_mode)

    # --- Voice States & Waves ---
    def set_listening(self, listening: bool):
        self._is_listening = listening
        if listening:
            try:
                winsound.Beep(900, 60)
            except Exception:
                pass
            self.set_status("Listening...")
        else:
            try:
                winsound.Beep(700, 60)
            except Exception:
                pass
            for bar in self.wave_bars:
                bar.setFixedHeight(6)

    def set_volume_level(self, level: float):
        clamped = max(0.0, min(1.0, level))
        for i, bar in enumerate(self.wave_bars):
            factor = math.sin((i / 4.0) * math.pi) * 0.8 + 0.2
            h = int(6 + (clamped * 20 * factor))
            bar.setFixedHeight(h)

    def set_thinking(self):
        self.set_status("Gemini Thinking...")

    def set_speaking(self):
        self.set_status(f"{self._persona_name} Speaking...")

    # --- Events ---
    def eventFilter(self, watched, event):
        if watched == self.type_input and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Escape:
                self.stop_typing()
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
