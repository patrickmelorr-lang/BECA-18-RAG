@echo off
chcp 65001 >nul
title Beca18 RAG - Reporte de costos
cd /d "%~dp0"
call ".venv\Scripts\activate.bat"
python -m src.costs
echo.
pause
