import os
import shutil
import sys
import json

def create_mvp():
    source_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    target_dir = r"C:\Users\pasca\Desktop\CueX_MVP"
    
    print(f"Erstelle CueX MVP in: {target_dir}")
    
    # Verzeichnisse ausschließen
    ignore_patterns = shutil.ignore_patterns(
        '.git', '__pycache__', '.venv', '.pytest_cache', '.vscode', 
        'instance', 'exports', 'data', 'docs', 'tests', '*.pyc', '.gitignore'
    )
    
    if os.path.exists(target_dir):
        print("Zielverzeichnis existiert bereits. Lösche alten Inhalt...")
        shutil.rmtree(target_dir)
    
    # Kopieren
    shutil.copytree(source_dir, target_dir, ignore=ignore_patterns)
    print("Dateien kopiert.")
    
    # app.py im Ziel anpassen (LITE_MODE erzwingen)
    app_py_path = os.path.join(target_dir, 'app.py')
    if os.path.exists(app_py_path):
        with open(app_py_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Ersetze die LITE_MODE Zeile
        import re
        content = re.sub(
            r"app\.config\['LITE_MODE'\]\s*=.*",
            "app.config['LITE_MODE'] = True  # Hardcoded for Lite MVP",
            content
        )
        
        with open(app_py_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print("LITE_MODE in app.py aktiviert.")

    # Leeres data-Verzeichnis und shows.json erstellen
    data_dir = os.path.join(target_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)
    shows_json_path = os.path.join(data_dir, 'shows.json')
    # Format muss ein Dictionary sein, nicht eine Liste!
    initial_data = {
        "shows": [],
        "next_show_id": 1,
        "next_song_id": 1,
        "next_check_item_id": 1
    }
    with open(shows_json_path, 'w', encoding='utf-8') as f:
        json.dump(initial_data, f, ensure_ascii=False, indent=2)
    print("Leeres data-Verzeichnis und shows.json erstellt.")

    # Batch-Datei zum Starten erstellen
    bat_content = """@echo off
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
REM Starte Browser nach kurzer Verzoegerung im Hintergrund (2 Sekunden)
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:5000"
py app.py
pause
"""
    with open(os.path.join(target_dir, 'start_cuex_lite.bat'), 'w') as f:
        f.write(bat_content)
    print("Start-Batch-Datei erstellt.")
    
    print("\nFertig! Die Anwendung ist nun auf deinem Desktop unter 'CueX_MVP'.")
    print("Du kannst diesen Ordner einfach zippen und verschicken.")

if __name__ == "__main__":
    create_mvp()
