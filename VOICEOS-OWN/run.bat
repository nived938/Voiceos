@echo off
cd /d "%~dp0"
echo ==========================================
echo      Launching VoiceOS-Own Desktop App    
echo ==========================================
python main.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Application exited with error code %ERRORLEVEL%.
    pause
)
