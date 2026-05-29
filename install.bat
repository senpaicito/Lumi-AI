@echo off
title LUMI AI - Dependency Installer
color 0B
cls
echo.
echo   ██╗         ██╗   ██╗    ███╗   ███╗    ██╗
echo   ██║         ██║   ██║    ████╗ ████║    ██║
echo   ██║         ██║   ██║    ██╔████╔██║    ██║
echo   ██║         ██║   ██║    ██║╚██╔╝██║    ██║
echo   ███████╗    ╚██████╔╝    ██║ ╚═╝ ██║    ██║
echo   ╚══════╝     ╚═════╝     ╚═╝     ╚═╝    ╚═╝
echo.
echo ==================================================
echo  Dependency Installation Interface
echo ==================================================
echo.
echo [INFO] Upgrading Python package manager (pip)...
python -m pip install --upgrade pip >nul
echo [INFO] Installing packages from requirements.txt...
pip install -r requirements.txt
echo.
echo [SUCCESS] System is up to date and ready for deployment.
pause