@echo off
REM ==========================================================
REM  Future Envelope — Windows Setup Script
REM  Run this ONCE to create a clean virtual environment.
REM  Double-click or run from Command Prompt in this folder.
REM ==========================================================

echo.
echo  [1/4] Creating virtual environment (venv)...
python -m venv venv
if errorlevel 1 (
    echo ERROR: Could not create venv. Make sure Python 3.8+ is installed.
    pause
    exit /b 1
)

echo.
echo  [2/4] Activating venv and upgrading pip...
call venv\Scripts\activate.bat
python -m pip install --upgrade pip --quiet

echo.
echo  [3/4] Installing dependencies into venv (isolated from Anaconda)...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Dependency installation failed. See above for details.
    pause
    exit /b 1
)

echo.
echo  [4/4] Starting Future Envelope...
echo        Open http://127.0.0.1:5000 in your browser.
echo        Press Ctrl+C to stop the server.
echo.
python app.py

pause
