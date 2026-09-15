@echo off
chcp 65001 >nul
title Beca18 RAG - Lanzador
cd /d "%~dp0"

if not exist ".venv\" (
    echo [ERROR] Falta instalar. Corre primero 1_INSTALAR.bat
    pause
    exit /b 1
)

echo Abriendo la app web y el bot en ventanas separadas...
start "Beca18 - App web" cmd /k "cd /d ""%~dp0"" && call .venv\Scripts\activate.bat && streamlit run app.py"
timeout /t 3 >nul
start "Beca18 - Bot Telegram" cmd /k "cd /d ""%~dp0"" && call .venv\Scripts\activate.bat && python bot.py"

echo.
echo Listo. Se abrieron dos ventanas.
echo Cierra cada una con Ctrl+C cuando termines.
timeout /t 5 >nul
