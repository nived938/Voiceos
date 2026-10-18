from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QListWidget, QListWidgetItem, QPushButton, QFrame
)
import pyperclip

class HistoryDrawer(QWidget):
    """
    Slide-out side drawer for quick access to past voice & agent sessions.
    Monochrome Black and White theme.
    """
    session_selected = Signal(dict)

    def __init__(self, db_manager, parent=None):
        super().__init__(parent)
        self.db = db_manager
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setFixedWidth(340)
        self.setStyleSheet("""
            QWidget {
                background-color: #000000;
                color: #ffffff;
                font-family: 'Segoe UI', sans-serif;
            }
            QLineEdit {
                background-color: #0d0d0d;
                border: 1px solid #2a2a2a;
                border-radius: 6px;
                padding: 6px 10px;
                color: #ffffff;
            }
            QLineEdit:focus {
                border-color: #ffffff;
            }
            QPushButton {
                background-color: #141414;
                color: #ffffff;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 11px;
                font-weight: 600;
            }
            QPushButton:hover {
                background-color: #222222;
                border-color: #ffffff;
            }
        """)
        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(14, 16, 14, 16)
        main_layout.setSpacing(10)

        # Header
        header = QHBoxLayout()
        title = QLabel("Recent Activity", self)
        title.setStyleSheet("font-size: 15px; font-weight: bold; color: #ffffff;")

        close_btn = QPushButton("✕", self)
        close_btn.setFixedSize(24, 24)
        close_btn.setStyleSheet("border-radius: 12px; font-size: 11px; background: transparent; border: 1px solid #333333;")
        close_btn.clicked.connect(self.hide)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(close_btn)
        main_layout.addLayout(header)

        # Search bar
        self.search_box = QLineEdit(self)
        self.search_box.setPlaceholderText("Filter history...")
        self.search_box.textChanged.connect(self.reload)
        main_layout.addWidget(self.search_box)

        # Session List
        self.list_widget = QListWidget(self)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: #0a0a0a;
                border: 1px solid #222222;
                border-radius: 8px;
            }
            QListWidget::item {
                padding: 10px;
                border-bottom: 1px solid #1a1a1a;
                color: #dddddd;
            }
            QListWidget::item:hover {
                background-color: #181818;
                color: #ffffff;
            }
            QListWidget::item:selected {
                background-color: #252525;
                color: #ffffff;
            }
        """)
        self.list_widget.itemDoubleClicked.connect(self._on_item_double_clicked)
        main_layout.addWidget(self.list_widget)

        # Bottom Actions
        bottom_row = QHBoxLayout()
        copy_btn = QPushButton("Copy Text", self)
        copy_btn.clicked.connect(self._copy_selected)

        refresh_btn = QPushButton("Refresh", self)
        refresh_btn.clicked.connect(self.reload)

        bottom_row.addWidget(copy_btn)
        bottom_row.addWidget(refresh_btn)
        main_layout.addLayout(bottom_row)

        self.reload()

    def reload(self):
        self.list_widget.clear()
        query = self.search_box.text().strip().lower()
        sessions = self.db.get_sessions(limit=40)

        for s in sessions:
            transcript = s.get("transcript", "") or ""
            generated = s.get("generated_text", "") or ""
            mode_lbl = "Agent" if s.get("mode") == 3 else "Dictate"
            created = s.get("created_at", "")[:19].replace("T", " ")

            if query and query not in transcript.lower() and query not in generated.lower():
                continue

            summary = transcript if transcript else generated
            if len(summary) > 60:
                summary = summary[:57] + "..."

            item = QListWidgetItem(f"[{mode_lbl}] {summary}\n{created}")
            item.setData(Qt.ItemDataRole.UserRole, s)
            self.list_widget.addItem(item)

    def _on_item_double_clicked(self, item: QListWidgetItem):
        data = item.data(Qt.ItemDataRole.UserRole)
        if data:
            self.session_selected.emit(data)

    def _copy_selected(self):
        item = self.list_widget.currentItem()
        if item:
            data = item.data(Qt.ItemDataRole.UserRole)
            text = data.get("generated_text") or data.get("transcript") or ""
            if text:
                pyperclip.copy(text)
