# VoiceOS Developer Setup & Contribution Guide

## 1. Prerequisites
- **Operating System:** Windows 10 or Windows 11 64-bit.
- **Python:** Version 3.10, 3.11, or 3.12 (Python 3.12 recommended).
- **Git:** Installed and configured in PATH.
- **Google Gemini API Key:** Free key from [Google AI Studio](https://aistudio.google.com/).

---

## 2. Local Development Setup

```powershell
# 1. Clone repository
git clone https://github.com/nived938/Voiceos.git
cd Voiceos\VOICEOS-OWN

# 2. Install requirements
python -m pip install --upgrade pip
python -m pip install -r requirements.txt

# 3. Create .env configuration
Copy-Item .env.example .env

# Edit .env and set:
# GEMINI_API_KEY=your_gemini_api_key_here
```

---

## 3. Running the Application
```powershell
# Launch via Python
python main.py

# Alternatively, launch via script
.\run.ps1
```

---

## 4. Running Automated Tests
```powershell
# Run all tests
python -m pytest

# Run with verbose output
python -m pytest -v

# Run specific test modules
python -m pytest tests/test_history_drawer.py tests/test_notch_widget.py
```

---

## 5. Coding Standards & Git Workflow
- Maintain documentation integrity: Preserve existing docstrings, schemas, and architecture contracts.
- Strictly adhere to the monochromatic design system: `#000000`, `#16161c`, `#252830`, `#8a8a8e`, `#ffffff`.
- Run pytest before committing to ensure all unit tests pass without warnings or regressions.
- Push clean atomic commits to GitHub `main` branch.
