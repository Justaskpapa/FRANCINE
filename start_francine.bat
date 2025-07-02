@echo off
REM This script starts the Francine AI assistant.

REM Navigate to the directory where this script is located.
REM This assumes main.py and other Francine files are in the same directory.
cd /d "%~dp0"

REM Activate the virtual environment.
REM The 'venv' folder should be in the same directory as this script.
if exist "venv\Scripts\activate.bat" (
    call "venv\Scripts\activate.bat"
) else (
    echo ERROR: Virtual environment not found. Please run install_francine.py first.
    pause
    exit /b 1
)

REM Start Francine.
REM The 'python' command will now use the Python interpreter from the activated virtual environment.
REM 'main.py' will then check config.json for 'speech' mode.
echo Starting Francine AI assistant...
python main.py

REM Keep the console window open after Francine exits or if an error occurs,
REM so you can see any messages. Remove if you want the window to close automatically.
pause
