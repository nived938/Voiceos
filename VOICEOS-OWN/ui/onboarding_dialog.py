from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QPushButton, QStackedWidget, QWidget, QFrame, QMessageBox
)

class OnboardingDialog(QDialog):
    """
    Step-by-step first-run onboarding wizard.
    Monochrome Black and White theme.
    """
    onboarding_finished = Signal()

    def __init__(self, config_manager, ai_provider, parent=None):
        super().__init__(parent)
        self.config = config_manager
        self.ai = ai_provider
        self.setWindowTitle("VoiceOS — Setup & Onboarding")
        self.setFixedSize(580, 420)
        self.setStyleSheet("""
            QDialog {
                background-color: #000000;
                color: #ffffff;
            }
            QLineEdit {
                background-color: #0d0d0d;
                border: 1px solid #2a2a2a;
                border-radius: 6px;
                padding: 8px 12px;
                color: #ffffff;
            }
            QLineEdit:focus {
                border-color: #ffffff;
            }
            QPushButton {
                background-color: #1a1a1a;
                color: #ffffff;
                border: 1px solid #333333;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #2a2a2a;
                border-color: #ffffff;
            }
        """)

        self._init_ui()

    def _init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(28, 28, 28, 28)
        main_layout.setSpacing(16)

        # Progress indicator
        self.step_label = QLabel("Step 1 of 4: Welcome", self)
        self.step_label.setStyleSheet("color: #ffffff; font-weight: 700; font-size: 12px; letter-spacing: 0.5px;")
        main_layout.addWidget(self.step_label)

        self.stack = QStackedWidget(self)

        # Page 1: Name & Introduction
        page1 = QWidget()
        p1_layout = QVBoxLayout(page1)
        p1_layout.setSpacing(12)

        title1 = QLabel("Welcome to VoiceOS", page1)
        title1.setStyleSheet("font-size: 22px; font-weight: 800; color: white;")
        desc1 = QLabel("Your personal, fast AI voice assistant on Windows.\nLet's configure everything in just a moment.", page1)
        desc1.setStyleSheet("color: #888888; line-height: 1.4;")

        name_lbl = QLabel("What should VoiceOS call you?", page1)
        name_lbl.setStyleSheet("font-weight: 600; margin-top: 10px; color: #ffffff;")
        self.name_input = QLineEdit(page1)
        self.name_input.setText(self.config.get("profile.first_name", "Nived"))
        self.name_input.setPlaceholderText("Enter your name")

        p1_layout.addWidget(title1)
        p1_layout.addWidget(desc1)
        p1_layout.addWidget(name_lbl)
        p1_layout.addWidget(self.name_input)
        p1_layout.addStretch()

        # Page 2: Audio & Permissions
        page2 = QWidget()
        p2_layout = QVBoxLayout(page2)
        p2_layout.setSpacing(12)

        title2 = QLabel("Audio & Microphone", page2)
        title2.setStyleSheet("font-size: 22px; font-weight: 800; color: white;")
        desc2 = QLabel("VoiceOS captures high-fidelity audio for speech recognition.\nTest your microphone below.", page2)
        desc2.setStyleSheet("color: #888888;")

        self.mic_status = QLabel("Microphone status: Ready (Default device detected)", page2)
        self.mic_status.setStyleSheet("color: #ffffff; font-weight: 600; margin-top: 10px; background-color: #121212; padding: 10px; border-radius: 6px; border: 1px solid #2a2a2a;")

        p2_layout.addWidget(title2)
        p2_layout.addWidget(desc2)
        p2_layout.addWidget(self.mic_status)
        p2_layout.addStretch()

        # Page 3: Hotkey & Notch Introduction
        page3 = QWidget()
        p3_layout = QVBoxLayout(page3)
        p3_layout.setSpacing(12)

        title3 = QLabel("Operating Modes & Top Notch", page3)
        title3.setStyleSheet("font-size: 22px; font-weight: 800; color: white;")

        info_box = QFrame(page3)
        info_box.setStyleSheet("background-color: #0d0d0d; border: 1px solid #2a2a2a; border-radius: 8px; padding: 12px;")
        ib_layout = QVBoxLayout(info_box)

        mode0_lbl = QLabel("🎙️ Dictation Mode: Speak naturally to inject text directly into active windows.", info_box)
        mode0_lbl.setStyleSheet("color: #ffffff; font-weight: 500;")

        mode3_lbl = QLabel("🧠 Agent Mode: Conversational intelligence powered by Google Gemini with silent Omniroute.", info_box)
        mode3_lbl.setStyleSheet("color: #cccccc; font-weight: 500; margin-top: 6px;")

        notch_lbl = QLabel("✨ Top Notch: Move mouse to top center of screen to peek; click to expand.", info_box)
        notch_lbl.setStyleSheet("color: #aaaaaa; font-weight: 500; margin-top: 6px;")

        ib_layout.addWidget(mode0_lbl)
        ib_layout.addWidget(mode3_lbl)
        ib_layout.addWidget(notch_lbl)

        p3_layout.addWidget(title3)
        p3_layout.addWidget(info_box)
        p3_layout.addStretch()

        # Page 4: Gemini API Key & Omniroute
        page4 = QWidget()
        p4_layout = QVBoxLayout(page4)
        p4_layout.setSpacing(10)

        title4 = QLabel("Connect Google Gemini API", page4)
        title4.setStyleSheet("font-size: 22px; font-weight: 800; color: white;")
        desc4 = QLabel("Enter your Gemini API key from Google AI Studio.\nVoiceOS Omniroute automatically switches models if one is busy.", page4)
        desc4.setStyleSheet("color: #888888;")

        self.key_input = QLineEdit(page4)
        self.key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.key_input.setPlaceholderText("Paste your Gemini API Key (e.g. AIzaSy...)")
        if self.config.get_gemini_api_key():
            self.key_input.setText(self.config.get_gemini_api_key())

        self.test_btn = QPushButton("Test API Key", page4)
        self.test_btn.clicked.connect(self._test_key)

        self.test_result_lbl = QLabel("", page4)
        self.test_result_lbl.setWordWrap(True)

        p4_layout.addWidget(title4)
        p4_layout.addWidget(desc4)
        p4_layout.addWidget(self.key_input)
        p4_layout.addWidget(self.test_btn)
        p4_layout.addWidget(self.test_result_lbl)
        p4_layout.addStretch()

        self.stack.addWidget(page1)
        self.stack.addWidget(page2)
        self.stack.addWidget(page3)
        self.stack.addWidget(page4)
        main_layout.addWidget(self.stack)

        # Nav Buttons
        btn_row = QHBoxLayout()
        self.back_btn = QPushButton("Back", self)
        self.back_btn.clicked.connect(self._prev_step)
        self.back_btn.setEnabled(False)

        self.next_btn = QPushButton("Continue", self)
        self.next_btn.setStyleSheet("background-color: #ffffff; color: #000000; font-weight: 800;")
        self.next_btn.clicked.connect(self._next_step)

        btn_row.addWidget(self.back_btn)
        btn_row.addStretch()
        btn_row.addWidget(self.next_btn)
        main_layout.addLayout(btn_row)

    def _test_key(self):
        key = self.key_input.text().strip()
        if not key:
            self.test_result_lbl.setText("❌ Please enter a Gemini API Key first.")
            self.test_result_lbl.setStyleSheet("color: #ff6b6b;")
            return

        self.test_result_lbl.setText("Testing connection to Google Gemini with Omniroute...")
        self.test_result_lbl.setStyleSheet("color: #aaaaaa;")
        self.ai.initialize(key, self.config.get("gemini.model", "gemini-3.8-flash"))
        res = self.ai.test_connection()
        if res.get("success"):
            self.test_result_lbl.setText(f"✅ {res.get('message')}")
            self.test_result_lbl.setStyleSheet("color: #ffffff; font-weight: 600;")
            self.config.set_gemini_api_key(key)
        else:
            self.test_result_lbl.setText(f"❌ {res.get('error')}")
            self.test_result_lbl.setStyleSheet("color: #ff6b6b;")

    def _next_step(self):
        curr = self.stack.currentIndex()
        if curr == 0:
            name = self.name_input.text().strip() or "User"
            self.config.set("profile.first_name", name)
            self.stack.setCurrentIndex(1)
            self.step_label.setText("Step 2 of 4: Audio Setup")
            self.back_btn.setEnabled(True)
        elif curr == 1:
            self.stack.setCurrentIndex(2)
            self.step_label.setText("Step 3 of 4: Operating Modes")
        elif curr == 2:
            self.stack.setCurrentIndex(3)
            self.step_label.setText("Step 4 of 4: Gemini AI Key")
            self.next_btn.setText("Finish Setup")
        elif curr == 3:
            key = self.key_input.text().strip()
            if key:
                self.config.set_gemini_api_key(key)
                self.ai.initialize(key, self.config.get("gemini.model", "gemini-3.8-flash"))
            self.config.set_onboarding_completed(True)
            self.onboarding_finished.emit()
            self.accept()

    def _prev_step(self):
        curr = self.stack.currentIndex()
        if curr > 0:
            self.stack.setCurrentIndex(curr - 1)
            self.next_btn.setText("Continue")
            if curr - 1 == 0:
                self.back_btn.setEnabled(False)
                self.step_label.setText("Step 1 of 4: Welcome")
            elif curr - 1 == 1:
                self.step_label.setText("Step 2 of 4: Audio Setup")
            elif curr - 1 == 2:
                self.step_label.setText("Step 3 of 4: Operating Modes")
