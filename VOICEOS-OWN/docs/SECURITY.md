# VoiceOS-Own Security & Privacy Policy

## 1. Zero Telemetry & Privacy Guarantee
Unlike commercial cloud wrappers, VoiceOS-Own does not transmit your personal data, recordings, clipboard content, or device identifiers to third-party analytics trackers (PostHog, Sentry, Mixpanel, etc.).
- All database records (`voiceos_own.db`) reside exclusively on your local disk.
- All configuration settings (`config.json`) are stored in your local AppData folder.

---

## 2. Secure API Key Management
- **Never Hardcoded:** No API keys are embedded in source code or Git repositories.
- **Git Protection:** `.env` is permanently excluded via `.gitignore`.
- **UI Masking:** In the Settings and Onboarding UI, your Gemini API key is obscured (`••••••••`) or masked as `AIza••••••••4fG9`.
- **Direct Official Connection:** The application connects exclusively to Google's official endpoints (`generativelanguage.googleapis.com`) using TLS encryption.

---

## 3. Clipboard & Keystroke Safety
- **Non-Destructive Text Injection:** When VoiceOS-Own injects transcribed text via simulated `Ctrl+V`, it temporarily backs up your existing clipboard contents and restores them within 300 milliseconds.
- **Controlled Scope:** The keyboard listener hook listens strictly for designated hotkey combinations (`Ctrl+Shift+D`, `Ctrl+Alt+A`, `Alt+\``) and does not record or log individual key presses.

---

## 4. Code Execution Guardrails
- **Restricted Tool Evaluation:** The `calculate()` tool implements an explicit character whitelist (`0123456789+-*/().,% eE`) and strips `__builtins__` from evaluation to prevent arbitrary code execution attacks.
