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

# Configuration
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-change-me')
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100 MB
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///shows.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['TEMPLATES_AUTO_RELOAD'] = True  # Force template reloading
app.jinja_env.auto_reload = True

# Database init
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


# Register Blueprints
from routes.main import main_bp
from routes.show_details import show_details_bp
from routes.show_assets import show_assets_bp
from routes.show_io import show_io_bp

app.register_blueprint(main_bp)
app.register_blueprint(show_details_bp)
app.register_blueprint(show_assets_bp)
app.register_blueprint(show_io_bp)


# Database Migration (Simple)
with app.app_context():
    engine = db.engine
    inspector = inspect(engine)
    if "shows" in inspector.get_table_names():
        existing_columns = [col["name"] for col in inspector.get_columns("shows")]
        if "ma3_sequence_id" not in existing_columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE shows ADD COLUMN ma3_sequence_id INTEGER DEFAULT 101"))
                conn.commit()
        # Migration: modules Spalte hinzufügen (für modulares MVP)
        if "modules" not in existing_columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE shows ADD COLUMN modules VARCHAR(200) DEFAULT 'stammdaten,cuelist,patch,kontakte,requisiten,video'"))
                conn.commit()
        if "eos_macro_id" not in existing_columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE shows ADD COLUMN eos_macro_id INTEGER DEFAULT 101"))
                conn.commit()
        if "eos_cuelist_id" not in existing_columns:
            with engine.connect() as conn:
                conn.execute(text("ALTER TABLE shows ADD COLUMN eos_cuelist_id INTEGER DEFAULT 1"))
                conn.commit()
    db.create_all()

if __name__ == "__main__":
    # Verwende Flask Debug-Server für automatisches Template-Reloading
    # Debug-Modus lädt Templates bei JEDER Anfrage neu (kein Caching)
    print("[INFO] Flask Debug-Server startet auf http://127.0.0.1:5000")
    print("[INFO] Templates werden automatisch neu geladen (kein Caching)")
    print("[INFO] Drücke CTRL+C zum Beenden.")
    app.run(debug=True, host='127.0.0.1', port=5000)