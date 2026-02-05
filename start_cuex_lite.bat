@echo off
echo ========================================
echo    CueX Lite MVP - Starter
echo ========================================
echo.
echo Bitte stelle sicher, dass Python installiert ist.
echo.
echo Installiere Abhaengigkeiten...
py -m pip install -r requirements.txt
echo.
echo Starte Server auf http://127.0.0.1:5000
echo Browser wird automatisch geoeffnet...
echo.
echo Login: Benutzername = Admin, Passwort = Admin123
echo.
echo Um den Server zu beenden: Druecke STRG+C oder schliesse dieses Fenster.
echo.
REM Browser wird automatisch von app.py geoeffnet
py app.py
pause
