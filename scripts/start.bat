@echo off
echo [CueX] Server wird gestartet...
echo [CueX] Zum Beenden: Dieses Fenster schliessen oder stop.bat ausfuehren
echo.
cd /d "%~dp0.."
call .venv\Scripts\activate
python app.py

