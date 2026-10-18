"""
Styles and theme definitions for VoiceOS-Own.
High-contrast, sleek Black and White monochrome theme (OLED Pure Black & Crisp White).
"""

DARK_THEME_QSS = """
/* Global Window & Typography */
QWidget {
    background-color: #000000;
    color: #ffffff;
    font-family: 'Segoe UI', -apple-system, BlinkMacSystemFont, Roboto, sans-serif;
    font-size: 13px;
    outline: none;
}

/* Sidebar & Navigation */
#sidebar {
    background-color: #050505;
    border-right: 1px solid #1c1c1c;
    min-width: 210px;
    max-width: 240px;
}

#navBtn {
    background-color: transparent;
    color: #888888;
    text-align: left;
    padding: 10px 16px;
    border-radius: 8px;
    font-size: 13px;
    font-weight: 500;
    border: none;
    margin: 2px 8px;
}

#navBtn:hover {
    background-color: #141414;
    color: #ffffff;
}

#navBtn[active="true"] {
    background-color: #1f1f1f;
    color: #ffffff;
    font-weight: 600;
    border-left: 3px solid #ffffff;
}

/* Cards & Containers */
#card {
    background-color: #0a0a0a;
    border: 1px solid #222222;
    border-radius: 12px;
    padding: 16px;
}

#card:hover {
    border-color: #444444;
}

/* Buttons */
QPushButton {
    background-color: #121212;
    color: #ffffff;
    border: 1px solid #2e2e2e;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #222222;
    border-color: #ffffff;
    color: #ffffff;
}

QPushButton:pressed {
    background-color: #050505;
}

#primaryBtn {
    background-color: #ffffff;
    color: #000000;
    border: 1px solid #ffffff;
    font-weight: 700;
    border-radius: 8px;
    padding: 9px 18px;
}

#primaryBtn:hover {
    background-color: #e2e2e2;
    border-color: #e2e2e2;
    color: #000000;
}

#primaryBtn:pressed {
    background-color: #cccccc;
}

#dangerBtn {
    background-color: #1a0808;
    color: #ff6b6b;
    border: 1px solid #5a1e1e;
}

#dangerBtn:hover {
    background-color: #ff4747;
    color: #ffffff;
    border-color: #ff4747;
}

#ghostBtn {
    background-color: transparent;
    color: #888888;
    border: 1px solid transparent;
}

#ghostBtn:hover {
    color: #ffffff;
    background-color: #1a1a1a;
    border-color: #333333;
}

/* Inputs & Forms */
QLineEdit, QTextEdit, QPlainTextEdit, QComboBox {
    background-color: #050505;
    border: 1px solid #262626;
    border-radius: 8px;
    padding: 8px 12px;
    color: #ffffff;
    selection-background-color: #ffffff;
    selection-color: #000000;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QComboBox:focus {
    border: 1px solid #ffffff;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #0a0a0a;
    color: #ffffff;
    selection-background-color: #ffffff;
    selection-color: #000000;
    border: 1px solid #333333;
}

/* Tables */
QTableWidget {
    background-color: #000000;
    border: 1px solid #1f1f1f;
    border-radius: 8px;
    gridline-color: #1a1a1a;
}

QHeaderView::section {
    background-color: #0d0d0d;
    color: #aaaaaa;
    padding: 8px 12px;
    border: none;
    border-bottom: 1px solid #222222;
    font-weight: 600;
}

QTableWidget::item {
    padding: 6px 12px;
    border-bottom: 1px solid #141414;
    color: #e0e0e0;
}

QTableWidget::item:selected {
    background-color: #1c1c1c;
    color: #ffffff;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #000000;
    width: 6px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #2a2a2a;
    border-radius: 3px;
    min-height: 24px;
}

QScrollBar::handle:vertical:hover {
    background: #ffffff;
}

/* Checkboxes */
QCheckBox {
    spacing: 8px;
    color: #dddddd;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #444444;
    background: #080808;
}

QCheckBox::indicator:checked {
    background-color: #ffffff;
    border-color: #ffffff;
    image: none;
}

/* Notch Widget Dynamic Island Styling */
#notchRoot {
    background-color: #000000;
    border: 1px solid #2a2a2a;
    border-top: none;
    border-bottom-left-radius: 20px;
    border-bottom-right-radius: 20px;
}

#notchPeekRoot {
    background-color: #000000;
    border: 1px solid #2a2a2a;
    border-top: none;
    border-bottom-left-radius: 14px;
    border-bottom-right-radius: 14px;
}

#notchInput {
    background-color: #0d0d0d;
    border: 1px solid #262626;
    border-radius: 8px;
    padding: 6px 12px;
    color: #ffffff;
    font-size: 12px;
}

#notchInput:focus {
    border: 1px solid #ffffff;
}
"""
