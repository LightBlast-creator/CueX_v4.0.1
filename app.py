import sys
import os
from flask import Flask, session, redirect, url_for, flash, render_template, request
try:
    from flask_wtf import CSRFProtect
    _CSRF_AVAILABLE = True
except Exception:
    CSRFProtect = None
    _CSRF_AVAILABLE = False
from sqlalchemy import inspect, text
from core.models import db


sys.modules["app"] = sys.modules.get(__name__)

app = Flask(__name__, template_folder="templates")

# PyInstaller Path Fix
if getattr(sys, 'frozen', False):
    template_folder = os.path.join(sys._MEIPASS, 'templates')
    static_folder = os.path.join(sys._MEIPASS, 'static')
    app = Flask(__name__, template_folder=template_folder, static_folder=static_folder)

# Configuration
# WARNUNG: Dieser Key ist nur für die Entwicklung! In Produktion muss er via Environment Variable gesetzt werden.
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-change-me')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB
app.config['LITE_MODE'] = True  # Hardcoded for Lite MVP

if app.config.get('LITE_MODE'):
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    print("[INFO] LITE_MODE aktiv: Verwende In-Memory Datenbank (Daten werden NICHT gespeichert)")
else:
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///shows.db"
    print(f"[INFO] LITE_MODE inaktiv: Verwende Dateibasierte Datenbank: {app.config['SQLALCHEMY_DATABASE_URI']}")

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Force template reloading
app.jinja_env.auto_reload = True

@app.context_processor
def inject_lite_mode():
    from core import show_logic
    return dict(
        lite_mode=app.config['LITE_MODE'],
        max_lite_shows=show_logic.MAX_LITE_SHOWS
    )
db.init_app(app)

# Error Handler
@app.errorhandler(413)
def request_entity_too_large(error):
    return render_template('error.html', message='Die hochgeladene Datei ist zu groß (max. 100 MB). Bitte wähle eine kleinere Datei oder teile sie auf.'), 413

# CSRF init
if _CSRF_AVAILABLE and CSRFProtect is not None:
    csrf = CSRFProtect()
    csrf.init_app(app)
else:
    def _empty_csrf_token():
        return ""
    @app.context_processor
    def _inject_csrf_token():
        return {"csrf_token": _empty_csrf_token}
    print("[WARN] Flask-WTF nicht installiert — CSRF deaktiviert. Installiere 'Flask-WTF' für Schutz.")

# Domain Logic Import (ensure it loads)
from core import show_logic
if app.config.get('LITE_MODE'):
    show_logic.LITE_MODE = True
    show_logic.shows.clear()  # Ensure it starts empty
    print("[INFO] show_logic: LITE_MODE aktiv - JSON-Speicherung deaktiviert.")


# Register Blueprints
from routes.main import main_bp
from routes.show_details import show_details_bp
from routes.show_assets import show_assets_bp
from routes.show_io import show_io_bp

app.register_blueprint(main_bp)
app.register_blueprint(show_details_bp)
app.register_blueprint(show_assets_bp)
app.register_blueprint(show_io_bp)


def run_migrations():
    """Führt einfache Datenbank-Migrationen durch."""
    with app.app_context():
        engine = db.engine
        inspector = inspect(engine)
        if "shows" in inspector.get_table_names():
            existing_columns = [col["name"] for col in inspector.get_columns("shows")]
            
            # Migration: ma3_sequence_id
            if "ma3_sequence_id" not in existing_columns:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE shows ADD COLUMN ma3_sequence_id INTEGER DEFAULT 101"))
                    conn.commit()
            
            # Migration: modules
            if "modules" not in existing_columns:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE shows ADD COLUMN modules VARCHAR(200) DEFAULT 'stammdaten,cuelist,patch,kontakte,requisiten,video'"))
                    conn.commit()
            
            # Migration: eos_macro_id
            if "eos_macro_id" not in existing_columns:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE shows ADD COLUMN eos_macro_id INTEGER DEFAULT 101"))
                    conn.commit()
            
            # Migration: eos_cuelist_id
            if "eos_cuelist_id" not in existing_columns:
                with engine.connect() as conn:
                    conn.execute(text("ALTER TABLE shows ADD COLUMN eos_cuelist_id INTEGER DEFAULT 1"))
                    conn.commit()
        
        db.create_all()

# Initialisiere DB & Migrationen
run_migrations()

if __name__ == "__main__":
    # Verwende Flask Debug-Server für automatisches Template-Reloading
    # Debug-Modus lädt Templates bei JEDER Anfrage neu (kein Caching)
    print("[INFO] Flask Debug-Server startet auf http://127.0.0.1:5000")
    print("[INFO] Templates werden automatisch neu geladen (kein Caching)")
    print("[INFO] Hard Shutdown (Windows): CTRL+C im Terminal oder TaskManager -> 'CueX.exe' -> End Task")
    print("[INFO] Soft Shutdown: Einfach dieses Fenster schließen.")
    # Browser automatisch öffnen (nur wenn nicht im Refresher-Loop des Debuggers)
    import threading
    import webbrowser
    
    def open_browser():
        webbrowser.open_new("http://127.0.0.1:5000")

    # Timer starten (nur im Hauptprozess, verhindert doppelte Tabs bei Reload oder Frozen)
    if not os.environ.get("WERKZEUG_RUN_MAIN"):
        threading.Timer(1.5, open_browser).start()

    # Debug-Modus nur in der Entwicklung, nicht in der .exe (verhindert doppelte Logs)
    is_frozen = getattr(sys, 'frozen', False)
    app.run(host="127.0.0.1", port=5000, debug=not is_frozen)