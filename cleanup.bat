@echo off
echo [CueX] Cleanup wird durchgefuehrt...
echo.

REM Stoppe Server falls laeuft
echo [1/4] Server beenden...
taskkill /F /IM python.exe 2>nul

REM Loesche __pycache__ Ordner
echo [2/4] Python Cache loeschen...
for /d /r . %%d in (__pycache__) do @if exist "%%d" rd /s /q "%%d" 2>nul
for /d /r . %%d in (.pytest_cache) do @if exist "%%d" rd /s /q "%%d" 2>nul

REM Loesche .pyc Dateien
echo [3/4] Kompilierte Python-Dateien loeschen...
del /s /q *.pyc 2>nul

REM Fertig
echo [4/4] Fertig!
echo.
echo [CueX] Cleanup abgeschlossen.
pause
