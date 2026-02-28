@echo off
REM Script de demarrage Windows pour Football Backend

echo ======================================================================
echo   FOOTBALL BACKEND - Demarrage du service
echo ======================================================================

cd /d "%~dp0"

echo.
echo [1] Verification de Python...
python --version
if errorlevel 1 (
    echo [ERREUR] Python n'est pas installe ou pas dans le PATH
    pause
    exit /b 1
)

echo.
echo [2] Verification des dependances...
python -c "import fastapi, uvicorn, pandas" 2>nul
if errorlevel 1 (
    echo [WARNING] Dependances manquantes. Installation...
    pip install -r requirements.txt
)

echo.
echo [3] Demarrage du serveur...
echo     API disponible sur: http://localhost:8000
echo     Documentation: http://localhost:8000/docs
echo.
echo     Appuyez sur Ctrl+C pour arreter le serveur
echo ======================================================================
echo.

python main.py

pause
