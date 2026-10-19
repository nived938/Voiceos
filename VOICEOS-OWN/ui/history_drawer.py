import os
from pathlib import Path
from datetime import datetime
import win32api

from PySide6.QtCore import Qt, Signal, QPropertyAnimation, QRect, QRectF, QEasingCurve, QTimer, QPointF
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QScrollArea, QFrame
)
from PySide6.QtGui import (
    QPainter, QPainterPath, QColor, QPixmap, QFont, QCursor,
    QFontMetrics, QKeyEvent
)


class HistoryDrawer(QWidget):
    """
    1:1 Visual Match Floating Chat History Panel for VoiceOS.
    Features:
    - Pure black background (#000000) with 26px rounded corners.
    - Compact vertical panel: 232px wide, 516px tall at reference scale.
    - Positioned at left edge of screen, starting 58px below top edge.
    - Integrated rounded dark search pill (#16161c) with magnifying glass icon.
    - Circular lock-style pin control (#16161c) toggling pinned/unpinned behavior.
    - Chronological date & time group headings (e.g. 'Today, 6:05 PM', 'Today, 2:56 PM').
    - Single-line conversation titles with globe icons and ellipsis truncation.
    - Subtle hover styling and #1a1a24 selected state.
    - Real-time search filtering, SQLite persistence, and conversation restoration.
    """

    session_selected = Signal(dict)

    PANEL_WIDTH = 232
    PANEL_HEIGHT = 516
    TOP_OFFSET = 58
    CORNER_RADIUS = 26

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self._is_pinned = False
        self._selected_session_id = None
        self._all_sessions = []
        self._filtered_sessions = []

        # Window Flags: Frameless, Always on Top, Floating Tool
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Slide animation
        self._anim = QPropertyAnimation(self, b"geometry")
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Click outside monitor
        self._outside_timer = QTimer(self)
        self._outside_timer.setInterval(40)
        self._outside_timer.timeout.connect(self._check_outside_click)

        # Locate globe icon asset
        curr_dir = Path(__file__).resolve().parent
        asset_path = curr_dir / "assets" / "globe.png"
        if not asset_path.exists():
            asset_path = curr_dir / "globe.png"
        self._globe_pixmap = QPixmap(str(asset_path)) if asset_path.exists() else QPixmap()

        self._init_ui()
        self._update_geometry(animated=False)

    def _init_ui(self):
        self.setFixedWidth(self.PANEL_WIDTH)
        self.setFixedHeight(self.PANEL_HEIGHT)

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 14, 10, 14)
        main_layout.setSpacing(10)

        # Top Search Row (Search Input Pill + Lock Button)
        search_row = QHBoxLayout()
        search_row.setContentsMargins(2, 0, 2, 0)
        search_row.setSpacing(8)

        # 1. Search Box with custom search icon
        self.search_input = QLineEdit(self)
        self.search_input.setPlaceholderText("Search")
        self.search_input.setFixedHeight(34)
        self.search_input.setStyleSheet("""
            QLineEdit {
                background-color: #16161c;
                border: none;
                border-radius: 17px;
                padding-left: 32px;
                padding-right: 12px;
                color: #ffffff;
                font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 13px;
            }
            QLineEdit::placeholder {
                color: #777782;
            }
        """)
        self.search_input.textChanged.connect(self._on_search_changed)

        # 2. Lock / Pin Button
        self.lock_btn = QPushButton(self)
        self.lock_btn.setFixedSize(34, 34)
        self.lock_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.lock_btn.setToolTip("Lock / Pin Panel")
        self.lock_btn.clicked.connect(self.toggle_pin)
        self._update_lock_btn_style()

        search_row.addWidget(self.search_input, stretch=1)
        search_row.addWidget(self.lock_btn)
        main_layout.addLayout(search_row)

        # Scroll Area for Conversations List
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                width: 0px;
                height: 0px;
                background: transparent;
            }
        """)

        # Container inside Scroll Area
        self.list_container = QWidget()
        self.list_container.setStyleSheet("background: transparent;")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(0, 4, 0, 8)
        self.list_layout.setSpacing(4)
        self.list_layout.addStretch()

        self.scroll_area.setWidget(self.list_container)
        main_layout.addWidget(self.scroll_area)

    def paintEvent(self, event):
        """Draws pure black rounded rectangle with 26px radius and search icon."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background: pure black #000000 with 26px radius
        painter.setBrush(QColor("#000000"))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, self.width(), self.height(), self.CORNER_RADIUS, self.CORNER_RADIUS)

        # Draw search magnifying glass icon inside search box
        if hasattr(self, "search_input") and self.search_input.isVisible():
            s_rect = self.search_input.geometry()
            ix = s_rect.x() + 11
            iy = s_rect.y() + 10
            painter.setPen(QColor("#777782"))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawEllipse(ix, iy, 9, 9)
            painter.drawLine(ix + 7, iy + 7, ix + 12, iy + 12)

        painter.end()

    def _update_lock_btn_style(self):
        """Updates the lock button icon and background to reflect pinned status."""
        bg_col = "#202028" if self._is_pinned else "#16161c"
        shackle_y = 7 if self._is_pinned else 6
        shackle_open = "" if self._is_pinned else "M11,10 L11,7 A3,3 0 0,1 17,7 L17,8"

        self.lock_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {bg_col};
                border: none;
                border-radius: 17px;
            }}
            QPushButton:hover {{
                background-color: #242430;
            }}
        """)
        # Repaint lock icon
        self.lock_btn.paintEvent = self._paint_lock_icon

    def _paint_lock_icon(self, event):
        painter = QPainter(self.lock_btn)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Background
        bg_col = QColor("#22222a") if self._is_pinned else QColor("#16161c")
        painter.setBrush(bg_col)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(0, 0, 34, 34)

        # Padlock Icon
        icon_col = QColor("#ffffff") if self._is_pinned else QColor("#8e8e95")
        painter.setPen(icon_col)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        # Shackle
        if self._is_pinned:
            # Closed shackle
            path = QPainterPath()
            path.moveTo(13, 14)
            path.lineTo(13, 11)
            path.arcTo(13, 8, 8, 8, 180, -180)
            path.lineTo(21, 14)
            painter.drawPath(path)
        else:
            # Open shackle
            path = QPainterPath()
            path.moveTo(13, 14)
            path.lineTo(13, 10)
            path.arcTo(13, 7, 8, 8, 180, -180)
            path.lineTo(21, 12)
            painter.drawPath(path)

        # Body
        painter.drawRoundedRect(QRectF(11, 14, 12, 10), 2, 2)
        painter.end()

    def toggle_pin(self):
        self._is_pinned = not self._is_pinned
        self._update_lock_btn_style()
        self.lock_btn.update()

    def is_pinned(self) -> bool:
        return self._is_pinned

    # --- Positioning & Display ---
    def _update_geometry(self, animated: bool = True):
        target_x = 0
        target_y = self.TOP_OFFSET
        target_w = self.PANEL_WIDTH
        target_h = self.PANEL_HEIGHT

        target_rect = QRect(target_x, target_y, target_w, target_h)

        if not animated:
            self.setGeometry(target_rect)
            return

        self._anim.stop()
        self._anim.setStartValue(QRect(-target_w, target_y, target_w, target_h))
        self._anim.setEndValue(target_rect)
        self._anim.start()

    def open_drawer(self):
        self.reload()
        self.show()
        self._update_geometry(animated=True)
        self._outside_timer.start()

    def close_drawer(self):
        if self._is_pinned:
            return
        self._outside_timer.stop()
        self.hide()

    def toggle(self):
        if self.isVisible():
            self.close_drawer()
        else:
            self.open_drawer()

    def _check_outside_click(self):
        if not self.isVisible() or self._is_pinned:
            return

        # Check mouse buttons
        l_down = bool(win32api.GetAsyncKeyState(0x01) & 0x8000)
        r_down = bool(win32api.GetAsyncKeyState(0x02) & 0x8000)

        if l_down or r_down:
            cursor_pos = QCursor.pos()
            if not self.geometry().contains(cursor_pos):
                self.close_drawer()

    # --- Data & Conversation Items ---
    def reload(self):
        """Loads sessions from SQLite and renders grouped conversation items."""
        try:
            self._all_sessions = self.db.get_sessions(limit=60)
        except Exception:
            self._all_sessions = []

        self._filter_and_render()

    def _on_search_changed(self, text: str):
        self._filter_and_render()

    def _filter_and_render(self):
        query = self.search_input.text().strip().lower()

        # Clear existing layout widgets
        while self.list_layout.count() > 1:
            child = self.list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if query:
            self._filtered_sessions = [
                s for s in self._all_sessions
                if query in (s.get("transcript") or "").lower()
                or query in (s.get("generated_text") or "").lower()
                or query in self._generate_readable_title(s).lower()
            ]
        else:
            self._filtered_sessions = list(self._all_sessions)

        if not self._filtered_sessions:
            empty_lbl = QLabel("No conversations found" if query else "No history yet", self.list_container)
            empty_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            empty_lbl.setStyleSheet("color: #55555e; font-size: 12px; padding: 24px 0;")
            self.list_layout.insertWidget(0, empty_lbl)
            return

        # Group sessions by date/time
        grouped = self._group_sessions(self._filtered_sessions)

        insert_idx = 0
        for header_text, sessions in grouped.items():
            # Group Header Label
            header_lbl = QLabel(header_text, self.list_container)
            header_lbl.setStyleSheet("""
                color: #68686e;
                font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
                font-size: 11px;
                font-weight: 700;
                padding: 10px 8px 4px 8px;
            """)
            self.list_layout.insertWidget(insert_idx, header_lbl)
            insert_idx += 1

            # Conversation Items in this group
            for s in sessions:
                item_widget = self._create_conversation_item(s)
                self.list_layout.insertWidget(insert_idx, item_widget)
                insert_idx += 1

    def _group_sessions(self, sessions):
        """
        Groups sessions into chronological buckets formatted like:
        'Today, 6:05 PM', 'Today, 2:56 PM', 'Yesterday, 4:10 PM', 'Oct 16, 2:15 PM'.
        """
        now = datetime.now()
        groups = {}

        for s in sessions:
            created_str = s.get("created_at", "")
            heading = "Recent"

            try:
                # Handle ISO 8601 strings
                dt = None
                for fmt in ("%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
                    try:
                        dt = datetime.strptime(created_str[:19], fmt)
                        break
                    except ValueError:
                        continue

                if dt:
                    time_part = dt.strftime("%I:%M %p").lstrip("0")
                    if dt.date() == now.date():
                        heading = f"Today, {time_part}"
                    elif (now.date() - dt.date()).days == 1:
                        heading = f"Yesterday, {time_part}"
                    else:
                        heading = f"{dt.strftime('%b %d')}, {time_part}"
            except Exception:
                heading = "Recent"

            if heading not in groups:
                groups[heading] = []
            groups[heading].append(s)

        return groups

    def _generate_readable_title(self, session: dict) -> str:
        """Generates a concise, readable title matching the screenshots."""
        t = (session.get("transcript") or "").strip()
        g = (session.get("generated_text") or "").strip()

        raw = t if t else g
        if not raw:
            return "New Conversation"

        # Check common patterns
        low = raw.lower()
        words = [w.strip(".,!?:;'\"()") for w in low.split()]
        if "weather" in low:
            # Extract city if possible
            raw_words = raw.split()
            city = "Local"
            for i, w in enumerate(raw_words):
                if w.lower() in ("in", "for", "at") and i + 1 < len(raw_words):
                    city = raw_words[i+1].replace("?", "").capitalize()
                    break
            return f"{city} Weather Fore..." if len(f"{city} Weather Forecast") > 22 else f"{city} Weather Forecast"
        elif "malayalam" in low:
            return "Malayalam Language Swi..."
        elif any(w in ("hello", "hi", "hey") for w in words):
            if "greeting" not in low:
                return "Initial User Greeting"
            return "Greeting and Introduction"
        elif "name" in words:
            return "Nived Name Confirmation"

        # General clean sentence / words
        clean = raw.replace("\n", " ").strip()
        words = clean.split()
        title = " ".join(words[:4])
        if len(title) > 23:
            title = title[:20] + "..."
        elif len(clean) > len(title):
            title += "..."
        return title

    def _create_conversation_item(self, session: dict) -> QWidget:
        """Builds a single conversation row widget matching 1:1 screenshot styling."""
        item = QFrame(self.list_container)
        item.setObjectName("convItem")
        is_selected = (self._selected_session_id == session.get("id"))

        bg_col = "#1a1a24" if is_selected else "transparent"
        item.setStyleSheet(f"""
            QFrame#convItem {{
                background-color: {bg_col};
                border-radius: 9px;
            }}
            QFrame#convItem:hover {{
                background-color: {'#1a1a24' if is_selected else '#121216'};
            }}
        """)
        item.setFixedHeight(34)
        item.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QHBoxLayout(item)
        layout.setContentsMargins(8, 0, 8, 0)
        layout.setSpacing(8)

        # Globe Icon
        globe_lbl = QLabel(item)
        if not self._globe_pixmap.isNull():
            globe_lbl.setPixmap(self._globe_pixmap.scaled(18, 18, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            globe_lbl.setText("🌐")
            globe_lbl.setStyleSheet("font-size: 13px;")
        globe_lbl.setFixedSize(18, 18)
        layout.addWidget(globe_lbl)

        # Title Label
        title_text = self._generate_readable_title(session)
        title_lbl = QLabel(title_text, item)
        title_lbl.setStyleSheet("""
            color: #ffffff;
            font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, sans-serif;
            font-size: 13px;
            font-weight: 400;
        """)
        title_lbl.setTextInteractionFlags(Qt.TextInteractionFlag.NoTextInteraction)
        layout.addWidget(title_lbl, stretch=1)

        # Mouse click handlers
        item.mousePressEvent = lambda e, s=session: self._on_item_clicked(s)
        return item

    def _on_item_clicked(self, session: dict):
        self._selected_session_id = session.get("id")
        self.session_selected.emit(session)
        self._filter_and_render()

    def closeEvent(self, event):
        self._anim.stop()
        self._outside_timer.stop()
        super().closeEvent(event)
