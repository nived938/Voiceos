import time
import threading
from PySide6.QtCore import Qt, QTimer, Signal, Slot
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QPushButton,
    QLabel, QStackedWidget, QTableWidget, QTableWidgetItem,
    QLineEdit, QComboBox, QCheckBox, QFrame, QHeaderView,
    QMessageBox, QScrollArea, QTextEdit
)
import pyperclip

from ui.styles import DARK_THEME_QSS
from ui.notch_widget import NotchWidget
from ui.history_drawer import HistoryDrawer
from ui.onboarding_dialog import OnboardingDialog
from core.window_watcher import WindowWatcher
from core.text_injector import TextInjector
from core.selection_reader import SelectionReader

class MainWindow(QMainWindow):
    """
    Main Dashboard for VoiceOS-Own.
    Features:
    - Sleek, monochromatic Black and White theme.
    - Integrated direct Typing Interface on the dashboard ("Typre thing").
    - Advanced Top Notch dynamic island integration (hidden -> hover peek -> click expand).
    - Selectable Voice Personas: Jarvis, Friday, Edith, and Ultron.
    - Omniroute Gemini AI auto-switch support.
    """

    def __init__(self, config_manager, db_manager, ai_provider, audio_capture, stt_engine, tts_engine, ducker=None):
        super().__init__()
        self.config = config_manager
        self.db = db_manager
        self.ai = ai_provider
        self.audio = audio_capture
        self.stt = stt_engine
        self.tts = tts_engine
        self.ducker = ducker

        self.setWindowTitle("VoiceOS")
        self.setMinimumSize(980, 660)
        self.resize(1040, 700)
        self.setStyleSheet(DARK_THEME_QSS)

        # Set initial persona
        current_persona = self.config.get("audio.voice_persona", "Jarvis")
        self.tts.set_persona(current_persona)

        # Advanced Top Notch (replaces floating pill)
        self.notch = NotchWidget()
        self.notch.set_persona(current_persona)
        self.history_drawer = HistoryDrawer(self.db)

        self._active_session_id = None
        self._current_mode = 0  # 0: Dictate, 3: Agent

        self._init_ui()
        self._wire_signals()

        # Check onboarding
        if not self.config.is_onboarding_completed:
            QTimer.singleShot(250, self._show_onboarding)

        # Show notch if enabled
        if self.config.get("ui.notch_enabled", True):
            self.notch.show()

    def _init_ui(self):
        root_widget = QWidget(self)
        self.setCentralWidget(root_widget)
        main_layout = QHBoxLayout(root_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Left Sidebar
        sidebar = QWidget(self)
        sidebar.setObjectName("sidebar")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(14, 18, 14, 18)
        sidebar_layout.setSpacing(6)

        # Brand Header
        brand_row = QHBoxLayout()
        brand_row.setContentsMargins(6, 0, 6, 10)
        brand_title = QLabel("VOICEOS", sidebar)
        brand_title.setStyleSheet("font-size: 18px; font-weight: 800; color: #ffffff; letter-spacing: 2px;")
        version_badge = QLabel("v0.1.40", sidebar)
        version_badge.setStyleSheet("color: #777777; font-size: 10px; padding-top: 5px;")
        brand_row.addWidget(brand_title)
        brand_row.addWidget(version_badge)
        brand_row.addStretch()
        sidebar_layout.addLayout(brand_row)

        # Nav Buttons
        self.nav_buttons = {}
        nav_items = [
            ("home", "🏠  Home"),
            ("insights", "📊  Insights"),
            ("history", "🕒  History"),
            ("dictionary", "📖  Dictionary"),
            ("settings", "⚙️  Settings")
        ]

        for tab_id, label in nav_items:
            btn = QPushButton(label, sidebar)
            btn.setObjectName("navBtn")
            btn.clicked.connect(lambda _, t=tab_id: self.navigate_to_tab(t))
            sidebar_layout.addWidget(btn)
            self.nav_buttons[tab_id] = btn

        sidebar_layout.addStretch()

        # Persona Quick Badge
        current_persona = self.config.get("audio.voice_persona", "Jarvis")
        self.sidebar_persona_lbl = QLabel(f"Voice: {current_persona}", sidebar)
        self.sidebar_persona_lbl.setStyleSheet("color: #666666; font-size: 11px; padding: 4px 8px;")
        sidebar_layout.addWidget(self.sidebar_persona_lbl)

        # Quick Mic Action in Sidebar
        self.quick_mic_btn = QPushButton("🎤 Start Dictation", sidebar)
        self.quick_mic_btn.setObjectName("primaryBtn")
        self.quick_mic_btn.clicked.connect(self.toggle_dictation)
        sidebar_layout.addWidget(self.quick_mic_btn)

        # Main Content Area
        content_area = QWidget(self)
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(28, 24, 28, 24)

        self.stack = QStackedWidget(content_area)
        self.stack.addWidget(self._build_home_page())
        self.stack.addWidget(self._build_insights_page())
        self.stack.addWidget(self._build_history_page())
        self.stack.addWidget(self._build_dictionary_page())
        self.stack.addWidget(self._build_settings_page())

        content_layout.addWidget(self.stack)

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content_area)

        self.navigate_to_tab("home")

    def _wire_signals(self):
        # Audio volume updates -> Live soundwave in the Top Notch
        self.audio.set_volume_callback(self.notch.set_volume_level)

        # Top Notch interactions
        self.notch.toggle_dictation_requested.connect(self.toggle_dictation)
        self.notch.toggle_agent_requested.connect(self.toggle_agent)
        self.notch.toggle_history_requested.connect(self.toggle_history)
        self.notch.text_submitted.connect(self.handle_text_query)
        self.notch.paste_requested.connect(self.paste_last_output)
        self.notch.mode_changed.connect(self._on_notch_mode_changed)

        # History drawer selection
        self.history_drawer.session_selected.connect(self._on_drawer_session_selected)

    def _on_notch_mode_changed(self, mode: int):
        self._current_mode = mode

    # --- Pages Construction ---
    def _build_home_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(18)

        user_name = self.config.get("profile.first_name", "Nived")
        greeting = QLabel(f"Good day, {user_name} 👋", page)
        greeting.setStyleSheet("font-size: 24px; font-weight: 800; color: #ffffff;")
        layout.addWidget(greeting)

        subtitle = QLabel("VoiceOS is ready. Use global hotkeys, hover at top center for the Notch, or type below.", page)
        subtitle.setStyleSheet("color: #888888; font-size: 13px; margin-bottom: 4px;")
        layout.addWidget(subtitle)

        # Action Cards Row
        cards_row = QHBoxLayout()
        cards_row.setSpacing(16)

        card1 = QFrame(page)
        card1.setObjectName("card")
        c1_layout = QVBoxLayout(card1)
        c1_title = QLabel("🎙️ Dictation Mode", card1)
        c1_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #ffffff;")
        c1_desc = QLabel("Speak naturally to dictate text straight into any focused window (Word, Chrome, Slack, VS Code).", card1)
        c1_desc.setWordWrap(True)
        c1_desc.setStyleSheet("color: #888888; font-size: 12px;")
        c1_btn = QPushButton("Dictate Now", card1)
        c1_btn.setObjectName("primaryBtn")
        c1_btn.clicked.connect(self.toggle_dictation)
        c1_layout.addWidget(c1_title)
        c1_layout.addWidget(c1_desc)
        c1_layout.addStretch()
        c1_layout.addWidget(c1_btn)

        card2 = QFrame(page)
        card2.setObjectName("card")
        c2_layout = QVBoxLayout(card2)
        c2_title = QLabel("🧠 Agent Mode", card2)
        c2_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #ffffff;")
        c2_desc = QLabel("Conversational assistant powered by Google Gemini with silent Omniroute failover. Real-time tools & facts.", card2)
        c2_desc.setWordWrap(True)
        c2_desc.setStyleSheet("color: #888888; font-size: 12px;")
        c2_btn = QPushButton("Ask Agent", card2)
        c2_btn.clicked.connect(self.toggle_agent)
        c2_layout.addWidget(c2_title)
        c2_layout.addWidget(c2_desc)
        c2_layout.addStretch()
        c2_layout.addWidget(c2_btn)

        cards_row.addWidget(card1)
        cards_row.addWidget(card2)
        layout.addLayout(cards_row)

        # Direct Typing Input Box ("Typre Thing") on Dashboard
        type_box = QFrame(page)
        type_box.setObjectName("card")
        tb_layout = QVBoxLayout(type_box)
        tb_layout.setSpacing(10)

        tb_header = QHBoxLayout()
        tb_title = QLabel("⌨️ Direct Typing & Prompt Bar", type_box)
        tb_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")

        self.home_mode_combo = QComboBox(type_box)
        self.home_mode_combo.addItems(["🧠 Agent Prompt", "🎙️ Inject Text (Dictate)"])
        self.home_mode_combo.setFixedWidth(190)

        tb_header.addWidget(tb_title)
        tb_header.addStretch()
        tb_header.addWidget(self.home_mode_combo)
        tb_layout.addLayout(tb_header)

        input_row = QHBoxLayout()
        self.home_type_input = QLineEdit(type_box)
        self.home_type_input.setPlaceholderText("Type a prompt or text to inject... [Press Enter to Submit]")
        self.home_type_input.returnPressed.connect(self._on_home_type_submit)

        home_send_btn = QPushButton("↵ Submit", type_box)
        home_send_btn.setObjectName("primaryBtn")
        home_send_btn.clicked.connect(self._on_home_type_submit)

        input_row.addWidget(self.home_type_input)
        input_row.addWidget(home_send_btn)
        tb_layout.addLayout(input_row)

        layout.addWidget(type_box)

        # Recent Sessions Preview Box
        recents_box = QFrame(page)
        recents_box.setObjectName("card")
        rb_layout = QVBoxLayout(recents_box)
        rb_title = QLabel("Recent Interactions", recents_box)
        rb_title.setStyleSheet("font-size: 14px; font-weight: bold; color: #ffffff;")
        rb_layout.addWidget(rb_title)

        self.home_recents_label = QLabel("No recent sessions yet. Start speaking or typing to see results!", recents_box)
        self.home_recents_label.setStyleSheet("color: #888888; margin-top: 6px; font-size: 12px;")
        rb_layout.addWidget(self.home_recents_label)

        layout.addWidget(recents_box)
        layout.addStretch()
        return page

    def _on_home_type_submit(self):
        text = self.home_type_input.text().strip()
        if not text:
            return
        mode = 3 if "Agent" in self.home_mode_combo.currentText() else 0
        self.handle_text_query(text, mode)
        self.home_type_input.clear()

    def _build_insights_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(16)

        title = QLabel("Productivity & Usage Insights", page)
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        layout.addWidget(title)

        # Stats Cards Grid
        grid_row = QHBoxLayout()
        grid_row.setSpacing(12)

        self.stat_sessions = self._create_stat_card("Sessions", "0", "Total voice/text sessions")
        self.stat_words = self._create_stat_card("Words Dictated", "0", "Words transcribed")
        self.stat_time = self._create_stat_card("Time Saved", "0.0s", "Estimated typing time saved")
        self.stat_tools = self._create_stat_card("Tools Executed", "0", "Weather, system, math tools")

        grid_row.addWidget(self.stat_sessions)
        grid_row.addWidget(self.stat_words)
        grid_row.addWidget(self.stat_time)
        grid_row.addWidget(self.stat_tools)
        layout.addLayout(grid_row)

        layout.addStretch()
        return page

    def _create_stat_card(self, title: str, val: str, subtitle: str) -> QFrame:
        card = QFrame()
        card.setObjectName("card")
        l = QVBoxLayout(card)
        t = QLabel(title, card)
        t.setStyleSheet("color: #888888; font-size: 12px; font-weight: 500;")
        v = QLabel(val, card)
        v.setStyleSheet("color: #ffffff; font-size: 26px; font-weight: 800; margin: 4px 0;")
        s = QLabel(subtitle, card)
        s.setStyleSheet("color: #666666; font-size: 11px;")
        l.addWidget(t)
        l.addWidget(v)
        l.addWidget(s)
        card.value_label = v
        return card

    def _build_history_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        header_row = QHBoxLayout()
        title = QLabel("Session History", page)
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        header_row.addWidget(title)
        header_row.addStretch()

        refresh_btn = QPushButton("Refresh", page)
        refresh_btn.clicked.connect(self._reload_history)
        header_row.addWidget(refresh_btn)
        layout.addLayout(header_row)

        # Table
        self.history_table = QTableWidget(page)
        self.history_table.setColumnCount(6)
        self.history_table.setHorizontalHeaderLabels(["Timestamp", "Mode", "App", "Transcript / Input", "Response", "Actions"])
        self.history_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Interactive)
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self.history_table)

        return page

    def _build_dictionary_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setSpacing(12)

        title = QLabel("Personal Vocabulary & Dictionary", page)
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        desc = QLabel("Add uncommon names, technical terms, or company acronyms. VoiceOS prioritizes these during speech recognition.", page)
        desc.setStyleSheet("color: #888888;")
        layout.addWidget(title)
        layout.addWidget(desc)

        # Add Row
        add_box = QFrame(page)
        add_box.setObjectName("card")
        ab_layout = QHBoxLayout(add_box)
        self.dict_input = QLineEdit(add_box)
        self.dict_input.setPlaceholderText("Enter word or term (e.g. Nived, VoiceOS, Kubernetes, PySide6)...")
        self.dict_input.returnPressed.connect(self._add_dictionary_word)
        add_btn = QPushButton("Add Word", add_box)
        add_btn.setObjectName("primaryBtn")
        add_btn.clicked.connect(self._add_dictionary_word)
        ab_layout.addWidget(self.dict_input)
        ab_layout.addWidget(add_btn)
        layout.addWidget(add_box)

        # Words Table
        self.dict_table = QTableWidget(page)
        self.dict_table.setColumnCount(3)
        self.dict_table.setHorizontalHeaderLabels(["Word / Term", "Added", "Action"])
        self.dict_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.dict_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.dict_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        layout.addWidget(self.dict_table)

        return page

    def _build_settings_page(self) -> QWidget:
        page = QWidget()
        scroll = QScrollArea(page)
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: transparent; }")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(20)

        title = QLabel("Application Settings", container)
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: white;")
        layout.addWidget(title)

        # Section 1: Gemini AI & Omniroute
        sec1 = QFrame(container)
        sec1.setObjectName("card")
        s1_layout = QVBoxLayout(sec1)
        s1_layout.setSpacing(12)

        s1_title = QLabel("Google Gemini AI & Omniroute", sec1)
        s1_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #ffffff;")
        s1_layout.addWidget(s1_title)

        omniroute_banner = QLabel("✨ Omniroute Silent Failover Active\n"
                                  "If a model is unavailable, rate-limited, or slow to respond, VoiceOS automatically "
                                  "switches to the next best available model (gemini-2.5-flash → gemini-2.5-pro → gemini-1.5-flash → gemini-1.5-pro) "
                                  "silently without interrupting your conversation.", sec1)
        omniroute_banner.setWordWrap(True)
        omniroute_banner.setStyleSheet("color: #aaaaaa; font-size: 11px; background-color: #141414; padding: 10px; border-radius: 8px; border: 1px solid #262626;")
        s1_layout.addWidget(omniroute_banner)

        key_row = QHBoxLayout()
        key_lbl = QLabel("API Key:", sec1)
        key_lbl.setFixedWidth(80)
        self.settings_key_input = QLineEdit(sec1)
        self.settings_key_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.settings_key_input.setPlaceholderText("Paste your Gemini API key from Google AI Studio")
        current_key = self.config.get_gemini_api_key()
        if current_key:
            self.settings_key_input.setText(current_key)

        test_key_btn = QPushButton("Test Connection", sec1)
        test_key_btn.clicked.connect(self._test_settings_gemini_key)

        save_key_btn = QPushButton("Save Key", sec1)
        save_key_btn.setObjectName("primaryBtn")
        save_key_btn.clicked.connect(self._save_gemini_key)

        key_row.addWidget(key_lbl)
        key_row.addWidget(self.settings_key_input)
        key_row.addWidget(test_key_btn)
        key_row.addWidget(save_key_btn)
        s1_layout.addLayout(key_row)

        self.key_status_label = QLabel(f"Current Status: {self.config.mask_api_key()}", sec1)
        self.key_status_label.setStyleSheet("color: #888888; font-size: 11px;")
        s1_layout.addWidget(self.key_status_label)

        # Preferred Primary Model Selector
        model_row = QHBoxLayout()
        model_lbl = QLabel("Primary Model:", sec1)
        model_lbl.setFixedWidth(100)
        self.model_combo = QComboBox(sec1)
        self.model_combo.addItems(["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash", "gemini-1.5-pro"])
        cur_model = self.config.get("gemini.model", "gemini-2.5-flash")
        if cur_model in ["gemini-2.5-flash", "gemini-2.5-pro", "gemini-1.5-flash", "gemini-1.5-pro"]:
            self.model_combo.setCurrentText(cur_model)
        self.model_combo.currentTextChanged.connect(self._on_model_changed)
        model_row.addWidget(model_lbl)
        model_row.addWidget(self.model_combo)
        model_row.addStretch()
        s1_layout.addLayout(model_row)

        layout.addWidget(sec1)

        # Section 2: Voice Personas (Jarvis, Friday, Edith, Ultron)
        sec2 = QFrame(container)
        sec2.setObjectName("card")
        s2_layout = QVBoxLayout(sec2)
        s2_layout.setSpacing(12)

        s2_title = QLabel("Voice Personas & Audio Synthesis", sec2)
        s2_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #ffffff;")
        s2_layout.addWidget(s2_title)

        persona_row = QHBoxLayout()
        persona_lbl = QLabel("AI Voice Persona:", sec2)
        persona_lbl.setFixedWidth(120)

        self.persona_combo = QComboBox(sec2)
        self.persona_combo.addItems(["Jarvis", "Friday", "Edith", "Ultron"])
        cur_persona = self.config.get("audio.voice_persona", "Jarvis")
        if cur_persona in ["Jarvis", "Friday", "Edith", "Ultron"]:
            self.persona_combo.setCurrentText(cur_persona)
        self.persona_combo.currentTextChanged.connect(self._on_persona_changed)

        test_persona_btn = QPushButton("🔊 Preview Voice", sec2)
        test_persona_btn.clicked.connect(self._test_voice_persona)

        persona_row.addWidget(persona_lbl)
        persona_row.addWidget(self.persona_combo)
        persona_row.addWidget(test_persona_btn)
        persona_row.addStretch()
        s2_layout.addLayout(persona_row)

        self.persona_desc_label = QLabel(self._get_persona_desc(cur_persona), sec2)
        self.persona_desc_label.setStyleSheet("color: #888888; font-size: 11px;")
        s2_layout.addWidget(self.persona_desc_label)

        # Speed row
        speed_row = QHBoxLayout()
        speed_lbl = QLabel("TTS Speed:", sec2)
        speed_lbl.setFixedWidth(120)
        self.speed_combo = QComboBox(sec2)
        self.speed_combo.addItems(["1.0x", "1.2x", "1.5x", "1.8x", "2.0x"])
        self.speed_combo.setCurrentText(f"{self.config.get('audio.tts_speed', 1.2)}x")
        self.speed_combo.currentTextChanged.connect(self._on_speed_changed)
        speed_row.addWidget(speed_lbl)
        speed_row.addWidget(self.speed_combo)
        speed_row.addStretch()
        s2_layout.addLayout(speed_row)

        self.ducking_check = QCheckBox("Enable Background Audio Ducking (attenuate music/media while speaking)", sec2)
        self.ducking_check.setChecked(self.config.get("audio.audio_ducking_enabled", True))
        self.ducking_check.stateChanged.connect(lambda s: self.config.set("audio.audio_ducking_enabled", s == 2))
        s2_layout.addWidget(self.ducking_check)

        layout.addWidget(sec2)

        # Section 3: Interface & Notch Controls
        sec3 = QFrame(container)
        sec3.setObjectName("card")
        s3_layout = QVBoxLayout(sec3)
        s3_layout.setSpacing(10)

        s3_title = QLabel("Top Notch & System Tray", sec3)
        s3_title.setStyleSheet("font-size: 15px; font-weight: bold; color: #ffffff;")
        s3_layout.addWidget(s3_title)

        notch_expl = QLabel("• Top Notch Interaction:\n"
                            "  - Hidden by default at the top-center edge of your screen.\n"
                            "  - Hover near the top center to reveal the sleek peeking pill.\n"
                            "  - Click the peeking pill (or press Alt + `) to fully expand into the interactive dynamic island.\n"
                            "  - Includes direct typing input, mode toggle, waveform, and clipboard actions.", sec3)
        notch_expl.setStyleSheet("color: #888888; font-size: 11px; line-height: 1.4;")
        s3_layout.addWidget(notch_expl)

        self.notch_check = QCheckBox("Enable Top Notch Dynamic Island", sec3)
        self.notch_check.setChecked(self.config.get("ui.notch_enabled", True))
        self.notch_check.stateChanged.connect(self._on_notch_toggled)
        s3_layout.addWidget(self.notch_check)

        self.tray_check = QCheckBox("Close to System Tray (keep running seamlessly in background)", sec3)
        self.tray_check.setChecked(self.config.get("ui.close_to_tray", True))
        self.tray_check.stateChanged.connect(lambda s: self.config.set("ui.close_to_tray", s == 2))
        s3_layout.addWidget(self.tray_check)

        layout.addWidget(sec3)
        layout.addStretch()

        scroll.setWidget(container)
        p_layout = QVBoxLayout(page)
        p_layout.setContentsMargins(0, 0, 0, 0)
        p_layout.addWidget(scroll)
        return page

    def _get_persona_desc(self, persona: str) -> str:
        descs = {
            "Jarvis": "Jarvis: Calm, articulate, measured British-style AI presence (ideal for productive work).",
            "Friday": "Friday: Warm, crisp, fast and highly responsive female assistant.",
            "Edith": "Edith: Gentle, smooth, precision-tactical intelligence.",
            "Ultron": "Ultron: Deep, commanding, deliberate tone with authoritative cadence."
        }
        return descs.get(persona, "")

    def _on_persona_changed(self, persona: str):
        self.config.set("audio.voice_persona", persona)
        self.tts.set_persona(persona)
        self.notch.set_persona(persona)
        self.sidebar_persona_lbl.setText(f"Voice: {persona}")
        self.persona_desc_label.setText(self._get_persona_desc(persona))

    def _test_voice_persona(self):
        persona = self.persona_combo.currentText()
        test_phrase = f"VoiceOS online. Persona {persona} operational. All systems nominal."
        self.notch.expand(test_phrase, status=f"{persona} Testing")
        self.tts.speak(test_phrase, persona=persona)
        self.notch.auto_collapse_after(4000)

    def _on_model_changed(self, model: str):
        self.config.set("gemini.model", model)
        self.ai.model_name = model

    # --- Navigation & Actions ---
    def navigate_to_tab(self, tab_id: str):
        tabs = ["home", "insights", "history", "dictionary", "settings"]
        if tab_id in tabs:
            idx = tabs.index(tab_id)
            self.stack.setCurrentIndex(idx)
            for tid, btn in self.nav_buttons.items():
                btn.setProperty("active", "true" if tid == tab_id else "false")
                btn.style().polish(btn)

            if tab_id == "insights":
                self._reload_insights()
            elif tab_id == "history":
                self._reload_history()
            elif tab_id == "dictionary":
                self._reload_dictionary()

    def _show_onboarding(self):
        diag = OnboardingDialog(self.config, self.ai, self)
        diag.onboarding_finished.connect(self._reload_home)
        diag.exec()

    def _reload_home(self):
        sessions = self.db.get_sessions(limit=1)
        if sessions:
            s = sessions[0]
            txt = s.get("generated_text") or s.get("transcript") or ""
            self.home_recents_label.setText(f"Last Interaction ({s.get('created_at', '')[:19]}):\n\"{txt[:120]}\"")

    def _reload_insights(self):
        stats = self.db.get_total_insights()
        self.stat_sessions.value_label.setText(str(stats["total_sessions"]))
        self.stat_words.value_label.setText(str(stats["total_words"]))
        self.stat_time.value_label.setText(f"{stats['total_time_saved_seconds']:.1f}s")
        self.stat_tools.value_label.setText(str(stats["total_tools"]))

    def _reload_history(self):
        sessions = self.db.get_sessions(limit=100)
        self.history_table.setRowCount(len(sessions))
        for row, s in enumerate(sessions):
            created = s.get("created_at", "")[:19].replace("T", " ")
            mode = "Agent" if s.get("mode") == 3 else "Dictate"
            app = s.get("app_name", "") or ""
            transcript = s.get("transcript", "") or ""
            response = s.get("generated_text", "") or ""

            self.history_table.setItem(row, 0, QTableWidgetItem(created))
            self.history_table.setItem(row, 1, QTableWidgetItem(mode))
            self.history_table.setItem(row, 2, QTableWidgetItem(app))
            self.history_table.setItem(row, 3, QTableWidgetItem(transcript[:80]))
            self.history_table.setItem(row, 4, QTableWidgetItem(response[:80]))

            copy_btn = QPushButton("Copy")
            copy_btn.clicked.connect(lambda _, text=response or transcript: pyperclip.copy(text))
            self.history_table.setCellWidget(row, 5, copy_btn)

    def _reload_dictionary(self):
        words = self.db.get_dictionary_words()
        self.dict_table.setRowCount(len(words))
        for row, w in enumerate(words):
            word_text = w.get("text", "")
            created = w.get("created_at", "")[:10]
            w_id = w.get("id")

            self.dict_table.setItem(row, 0, QTableWidgetItem(word_text))
            self.dict_table.setItem(row, 1, QTableWidgetItem(created))

            del_btn = QPushButton("Delete")
            del_btn.setObjectName("dangerBtn")
            del_btn.clicked.connect(lambda _, wid=w_id: self._delete_dict_word(wid))
            self.dict_table.setCellWidget(row, 2, del_btn)

    def _add_dictionary_word(self):
        text = self.dict_input.text().strip()
        if text:
            if self.db.add_dictionary_word(text):
                self.dict_input.clear()
                self._reload_dictionary()
            else:
                QMessageBox.warning(self, "Word Exists", f"'{text}' is already in your custom vocabulary.")

    def _delete_dict_word(self, word_id: str):
        self.db.delete_dictionary_word(word_id)
        self._reload_dictionary()

    def _save_gemini_key(self):
        key = self.settings_key_input.text().strip()
        if key:
            self.config.set_gemini_api_key(key)
            self.ai.initialize(key, self.config.get("gemini.model", "gemini-2.5-flash"))
            self.key_status_label.setText(f"Current Status: {self.config.mask_api_key()}")
            QMessageBox.information(self, "Saved", "Gemini API Key saved successfully.")

    def _test_settings_gemini_key(self):
        key = self.settings_key_input.text().strip()
        if not key:
            QMessageBox.warning(self, "Missing Key", "Please enter an API key to test.")
            return
        self.ai.initialize(key, self.config.get("gemini.model", "gemini-2.5-flash"))
        res = self.ai.test_connection()
        if res.get("success"):
            QMessageBox.information(self, "Success", f"{res.get('message')}\nSample: \"{res.get('sample', '')}\"")
        else:
            QMessageBox.critical(self, "Error", res.get("error"))

    def _on_speed_changed(self, text: str):
        try:
            val = float(text.replace("x", ""))
            self.config.set("audio.tts_speed", val)
            self.tts.speed_multiplier = val
        except Exception:
            pass

    def _on_notch_toggled(self, state: int):
        enabled = state == 2
        self.config.set("ui.notch_enabled", enabled)
        self.notch.setVisible(enabled)

    def _on_drawer_session_selected(self, session_data: dict):
        transcript = session_data.get("transcript") or ""
        generated = session_data.get("generated_text") or ""
        text = generated or transcript
        if text:
            pyperclip.copy(text)

        # Restore into Notch display
        self.notch.show_restored_conversation(transcript, generated)

    def toggle_history(self):
        self.history_drawer.toggle()

    # --- Core Voice & Interaction Pipeline ---
    def toggle_dictation(self):
        self._current_mode = 0
        self.notch.set_mode(0)
        self._toggle_voice_flow()

    def toggle_agent(self):
        self._current_mode = 3
        self.notch.set_mode(3)
        self._toggle_voice_flow()

    def _toggle_voice_flow(self):
        if not self.audio.is_recording:
            # Start Recording
            if self.ducker and self.config.get("audio.audio_ducking_enabled", True):
                self.ducker.duck()
            if self.audio.start_recording():
                mode_str = "Agent Mode" if self._current_mode == 3 else "Dictation"
                self.notch.set_listening(True)
                self.notch.expand("Listening...", status=mode_str)
        else:
            # Stop Recording & Process
            self.notch.set_listening(False)
            self.notch.set_thinking()
            self.notch.expand("Processing speech...", status="Thinking")

            wav_file = self.audio.stop_recording()
            if not wav_file:
                self._finish_flow("No audio captured.")
                return

            threading.Thread(target=self._process_audio, args=(wav_file, self._current_mode), daemon=True).start()

    def _process_audio(self, wav_file: str, mode: int):
        start_time = time.time()
        words = [w["text"] for w in self.db.get_dictionary_words()]
        transcript = self.stt.transcribe_file(wav_file, custom_words=words)
        duration_sec = round(time.time() - start_time, 2)

        if not transcript:
            self._finish_flow("Could not transcribe speech.")
            return

        app_name, win_title = WindowWatcher.get_active_window_info()

        if mode == 0:
            # Mode 0: Dictation -> Inject text directly into active application!
            TextInjector.inject_text(transcript + " ")
            self.db.create_session(transcript=transcript, generated_text=transcript,
                                   app_name=app_name, window_title=win_title,
                                   duration_seconds=duration_sec, mode=0)
            self._finish_flow(f"Dictated: \"{transcript}\"")
        else:
            # Mode 3: Agent Mode -> Send query to Gemini AI!
            self.notch.expand(f"\"{transcript}\"", status="Gemini Thinking")
            self._execute_agent_turn(transcript, app_name, win_title, duration_sec)

    def _execute_agent_turn(self, query: str, app_name: str, win_title: str, duration_sec: float):
        full_response = []
        tool_runs = []

        # Active Window context for intelligent situational awareness
        context = []
        if app_name and "voiceos" not in app_name.lower():
            context.append({"role": "user", "content": f"[Active Application Context: '{app_name}' (Title: '{win_title}')]"})

        try:
            for event in self.ai.generate_response(prompt=query, context=context):
                etype = event.get("type")
                if etype == "chunk":
                    chunk = event.get("content", "")
                    full_response.append(chunk)
                    self.notch.update_text("".join(full_response))
                elif etype == "tool_call":
                    tool_name = event.get("tool_name", "")
                    tool_runs.append({"tool_name": tool_name, "input": event.get("input", {}), "status": "completed"})
                    self.notch.expand(f"Running tool: {tool_name}...", tool=tool_name, status="Tool Calling")
                elif etype == "error":
                    full_response.append(f"\n{event.get('content')}")
        except Exception as e:
            full_response.append(f"Error: {str(e)}")

        resp_text = "".join(full_response).strip()
        if not resp_text:
            resp_text = "I received your request, but got an empty response."

        # Save session to SQLite
        session_id = self.db.create_session(transcript=query, generated_text=resp_text,
                                            app_name=app_name, window_title=win_title,
                                            duration_seconds=duration_sec, mode=3)
        self.db.record_turn(session_id=session_id, user_message=query, assistant_response=resp_text,
                            duration_ms=int(duration_sec * 1000), tool_calls=tool_runs)

        # Speak Response using active Persona
        self.notch.set_speaking()
        self.notch.expand(resp_text, status=f"{self.tts.persona} Speaking")
        self.tts.speak(resp_text)

        self._finish_flow(resp_text)

    def handle_text_query(self, text: str, mode: int):
        """Fallback / direct keyboard query handler."""
        if mode == 0:
            TextInjector.inject_text(text + " ")
            self.notch.expand(f"Injected: {text}", status="Injected")
            self.notch.auto_collapse_after(2500)
        else:
            self.notch.expand(f"\"{text}\"", status="Thinking")
            app_name, win_title = WindowWatcher.get_active_window_info()
            threading.Thread(target=self._execute_agent_turn, args=(text, app_name or "Keyboard", win_title or "", 0.4), daemon=True).start()

    def paste_last_output(self):
        sessions = self.db.get_sessions(limit=1)
        if sessions:
            text = sessions[0].get("generated_text") or sessions[0].get("transcript") or ""
            if text:
                TextInjector.inject_text(text)
                self.notch.expand("Pasted last output!", status="Pasted")
                self.notch.auto_collapse_after(2500)

    def _finish_flow(self, message: str = ""):
        if self.ducker and self.config.get("audio.audio_ducking_enabled", True):
            self.ducker.unduck()
        self.notch.set_listening(False)
        self._reload_home()
        self.history_drawer.reload()
        self.notch.auto_collapse_after(7000)

    # --- Window Controls ---
    def show_and_activate(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def toggle_notch(self):
        if self.notch.isVisible():
            if self.notch._state == NotchWidget.STATE_EXPANDED:
                self.notch.collapse_to_hidden()
            else:
                self.notch.transition_to_expanded()
        else:
            self.notch.show()
            self.notch.transition_to_expanded()

    def closeEvent(self, event):
        if self.config.get("ui.close_to_tray", True):
            event.ignore()
            self.hide()
        else:
            self.safe_shutdown()

    def safe_shutdown(self):
        self.audio.cancel_recording()
        self.tts.stop()
        if self.ducker:
            self.ducker.unduck()
        self.notch.close()
        self.history_drawer.close()
        self.close()
        import sys
        sys.exit(0)
