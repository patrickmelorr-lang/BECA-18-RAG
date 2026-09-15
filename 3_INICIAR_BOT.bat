@echo off
chcp 65001 >nul
title Beca18 RAG - Bot de Telegram
cd /d "%~dp0"

if not exist ".venv\" (
    echo [ERROR] Falta instalar. Corre primero 1_INSTALAR.bat
    pause
    exit /b 1
)
if not exist ".env" (
    echo [ERROR] Falta el archivo .env con tus llaves.
    pause
    exit /b 1
)
if not exist "data\chroma\" (
    echo [AVISO] No encuentro el indice. Lo construyo ahora...
    call ".venv\Scripts\activate.bat"
    python build_index.py
)

call ".venv\Scripts\activate.bat"
echo.
echo Bot encendido. Escribele desde Telegram.
echo Para apagarlo: Ctrl+C en esta ventana.
echo IMPORTANTE: solo puede haber UNA ventana del bot abierta a la vez.
echo.
python bot.py
pause
