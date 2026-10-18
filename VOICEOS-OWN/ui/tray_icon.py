from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QIcon, QPixmap, QColor, QPainter

class SystemTrayManager(QSystemTrayIcon):
    """
    Windows System Tray icon with quick actions and Notch toggle in Black and White theme.
    """
    def __init__(self, main_window, parent=None):
        super().__init__(parent)
        self.main_window = main_window

        # Generate a monochromatic high-contrast icon pixmap
        pixmap = QPixmap(32, 32)
        pixmap.fill(QColor(0, 0, 0, 0))
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setBrush(QColor("#ffffff"))
        painter.setPen(QColor("#000000"))
        painter.drawEllipse(4, 4, 24, 24)
        painter.setBrush(QColor("#000000"))
        painter.drawEllipse(12, 12, 8, 8)
        painter.end()

        self.setIcon(QIcon(pixmap))
        self.setToolTip("VoiceOS — Universal AI Voice Interface")

        self._create_menu()
        self.activated.connect(self._on_activated)

    def _create_menu(self):
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #000000;
                color: #ffffff;
                border: 1px solid #2a2a2a;
                border-radius: 6px;
                padding: 6px;
                font-family: 'Segoe UI', sans-serif;
                font-size: 12px;
            }
            QMenu::item {
                padding: 6px 14px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #222222;
                color: #ffffff;
            }
            QMenu::separator {
                height: 1px;
                background-color: #1f1f1f;
                margin: 4px 0px;
            }
        """)

        act_dashboard = menu.addAction("Open Dashboard")
        act_dashboard.triggered.connect(self.main_window.show_and_activate)

        act_notch = menu.addAction("Toggle Top Notch Dynamic Island")
        act_notch.triggered.connect(self.main_window.toggle_notch)

        menu.addSeparator()

        act_settings = menu.addAction("Settings")
        act_settings.triggered.connect(lambda: (self.main_window.show_and_activate(), self.main_window.navigate_to_tab("settings")))

        menu.addSeparator()

        act_quit = menu.addAction("Quit VoiceOS")
        act_quit.triggered.connect(self.main_window.safe_shutdown)

        self.setContextMenu(menu)

    def _on_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.main_window.show_and_activate()
