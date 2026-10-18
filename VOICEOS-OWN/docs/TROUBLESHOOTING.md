# VoiceOS-Own Troubleshooting Guide

### 1. "No API key configured" or "Invalid Gemini API Key"
- **Cause:** No key was entered in `.env` or in Settings, or the key was mistyped.
- **Resolution:**
  1. Open VoiceOS-Own -> Go to **Settings**.
  2. Paste your Gemini API key from [Google AI Studio](https://aistudio.google.com/).
  3. Click **Test Connection**. Once verified, click **Save Key**.

### 2. "Microphone capture failed" or No Audio Waveform
- **Cause:** Windows privacy settings blocking microphone access or wrong default audio input device.
- **Resolution:**
  1. Open Windows Settings -> **Privacy & Security** -> **Microphone**.
  2. Ensure "Microphone access" and "Let desktop apps access your microphone" are set to **On**.
  3. Check the Windows Sound Control Panel to verify your microphone is set as the Default Device.

### 3. Hotkeys (`Ctrl+Shift+D` or `Ctrl+Alt+A`) do not respond
- **Cause:** Another application has registered the same global hotkey with exclusive priority.
- **Resolution:**
  1. You can trigger Dictation or Agent Mode directly by clicking the 🎤 icon or mode badge on the Floating Pill.
  2. Alternatively, adjust the hotkey combinations in `main.py` or `config.json`.

### 4. Text does not paste into the target application
- **Cause:** Target application is running as Administrator while VoiceOS-Own is running with standard user privileges (Windows UIPI boundary).
- **Resolution:**
  - Launch VoiceOS-Own with equivalent permissions (or run your target application under standard user privileges).
  - Use the "Paste" button on the Floating Pill to paste manually.

### 5. Gemini Rate Limit / Resource Exhausted (429)
- **Cause:** Free tier Gemini API requests exceeded quota per minute.
- **Resolution:**
  - In Settings, switch the model from `gemini-2.5-pro` to `gemini-2.5-flash` or `gemini-1.5-flash` for higher request allowances.
