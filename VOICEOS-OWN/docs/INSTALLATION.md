# VoiceOS-Own Installation & Setup Guide

## System Requirements

- **Operating System:** Windows 10 or Windows 11 (64-bit)
- **Python:** Python 3.10, 3.11, or 3.12 (verified on Python 3.12)
- **Audio:** Functional microphone and speakers/headphones
- **Internet:** Active connection for Google Gemini API and speech recognition
- **API Key:** A Google Gemini API Key (free tier available at [Google AI Studio](https://aistudio.google.com/))

---

## 1. Quick Installation

Open PowerShell as your standard user and run:

```powershell
# 1. Navigate to the project directory
cd G:\Coding\VOICE-OS\VOICEOS-OWN

# 2. Install dependencies
python -m pip install -r requirements.txt

# 3. Configure environment file
Copy-Item .env.example .env
```

---

## 2. Configuring Your Gemini API Key

You can configure your API key through either method:

### Method A: Through the Application UI (Recommended)
1. Launch the application:
   ```powershell
   python main.py
   ```
2. During the first-run onboarding wizard (or in **Settings**), paste your Gemini API key.
3. Click **Test Connection**. A green checkmark confirms authentication!

### Method B: Via `.env` File
Open `.env` in any text editor and set your key:
```ini
GEMINI_API_KEY=AIzaSyYourSecretKeyHere
GEMINI_MODEL=gemini-2.5-flash
```

---

## 3. Launching VoiceOS-Own

### Option 1: PowerShell Script
```powershell
.\run.ps1
```

### Option 2: Windows Batch
Double-click `run.bat` or run:
```cmd
run.bat
```

### Option 3: Python Command
```powershell
python main.py
```

---

## 4. Running the Automated Test Suite

To verify system integrity and offline mock tests:

```powershell
python -m pytest tests -v
```
All 18 automated tests should pass.
