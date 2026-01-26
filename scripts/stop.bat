@echo off
echo [CueX] Server wird beendet...
taskkill /F /IM python.exe 2>nul
if %ERRORLEVEL% == 0 (
    echo [CueX] Server erfolgreich beendet!
) else (
    echo [CueX] Kein Server gefunden oder bereits beendet.
)
pause
