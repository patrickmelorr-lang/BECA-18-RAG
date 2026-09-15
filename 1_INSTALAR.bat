@echo off
chcp 65001 >nul
title Beca18 RAG - Instalacion
cd /d "%~dp0"

echo ===============================================
echo   BECA 18 RAG - INSTALACION (solo la 1a vez)
echo ===============================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] Python no esta instalado o no esta en el PATH.
    echo Descargalo de python.org y marca "Add Python to PATH".
    pause
    exit /b 1
)
python --version
echo.

if not exist ".venv\" (
    echo [1/5] Creando entorno virtual...
    python -m venv .venv
) else (
    echo [1/5] El entorno virtual ya existe.
)

echo [2/5] Activando entorno...
call ".venv\Scripts\activate.bat"

echo [3/5] Instalando PyTorch version CPU (esto tarda, es el paso pesado)...
python -m pip install --upgrade pip --quiet
pip install torch --index-url https://download.pytorch.org/whl/cpu --quiet

echo [4/5] Instalando el resto de dependencias...
pip install -r requirements.txt --quiet

if not exist ".env" (
    echo.
    echo [5/5] No existe el archivo .env. Lo creo a partir del ejemplo.
    copy ".env.example" ".env" >nul
    echo.
    echo   ATENCION: se va a abrir el Bloc de notas.
    echo   Pega tus dos llaves, guarda con Ctrl+S y cierra la ventana.
    echo.
    pause
    notepad ".env"
) else (
    echo [5/5] El archivo .env ya existe.
)

echo.
echo Construyendo el indice (la 1a vez descarga el modelo, ~470 MB)...
python build_index.py

echo.
echo ===============================================
echo   LISTO. Ahora puedes usar:
echo     2_INICIAR_APP.bat   -^> la pagina web
echo     3_INICIAR_BOT.bat   -^> el bot de Telegram
echo     4_INICIAR_TODO.bat  -^> los dos a la vez
echo ===============================================
pause
