@echo off
TITLE Project Companion - DIRECT LINK
COLOR 0B

SET VENV_DIR=.venv

:: Activate Venv and run CLI
call %VENV_DIR%\Scripts\activate.bat
python src/cli.py

pause