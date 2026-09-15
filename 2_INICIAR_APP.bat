@echo off
chcp 65001 >nul
title Beca18 RAG - App web
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

call ".venv\Scripts\activate.bat"
echo Abriendo la app en http://localhost:8501
echo Para detenerla: Ctrl+C en esta ventana.
echo.
streamlit run app.py
pause
