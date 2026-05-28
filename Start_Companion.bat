@echo off
TITLE Project Companion - AI Interface
COLOR 0A

:: --- CONFIGURATION ---
SET VENV_DIR=.venv
SET MAIN_SCRIPT=src\main.py
SET REQ_FILE=requirements.txt

:: --- CHECK PYTHON ---
python --version >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Python is not installed or not in your PATH.
    echo Please install Python 3.10+ and tick "Add Python to PATH" in the installer.
    pause
    exit
)

:: --- CHECK VIRTUAL ENVIRONMENT ---
IF NOT EXIST "%VENV_DIR%" (
    echo [INFO] Virtual Environment not found. Creating one...
    python -m venv %VENV_DIR%
    echo [INFO] Virtual Environment created.
)

:: --- ACTIVATE VENV ---
call %VENV_DIR%\Scripts\activate.bat

:: --- CHECK DEPENDENCIES ---
echo [INFO] Checking dependencies...
pip install -r %REQ_FILE% >nul 2>&1
IF %ERRORLEVEL% NEQ 0 (
    echo [WARNING] Could not install dependencies automatically.
    echo Running install with output to see errors:
    pip install -r %REQ_FILE%
    pause
) else (
    echo [INFO] Dependencies are up to date.
)

:: --- RUN BOT ---
echo.
echo ===================================================
echo    PROJECT COMPANION IS STARTING
echo    Press Ctrl+C to stop the bot.
echo ===================================================
echo.

python %MAIN_SCRIPT%

:: --- FINISH ---
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [CRASH] The bot crashed with an error code.
    pause
)

deactivate