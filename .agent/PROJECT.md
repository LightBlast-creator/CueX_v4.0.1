# CueX – Projekt-Übersicht

## Was ist CueX?
Eine Flask-basierte Webanwendung für **Lichtdesigner und Veranstaltungstechniker** zur Verwaltung von Shows, Cue-Listen, Rig-Setups und Crew-Kontakten.

## Tech Stack
- **Backend**: Python 3, Flask, SQLAlchemy (SQLite)
- **Frontend**: Jinja2 Templates, Bootstrap 5, Vanilla CSS/JS
- **Server**: Waitress (Windows-kompatibel)

## Projektstruktur
```
├── app.py              # Flask App Entry Point
├── models.py           # SQLAlchemy Models (Show, Song, ChecklistItem, Contact)
├── show_logic.py       # Business Logic
├── routes/             # Flask Blueprints
│   ├── main.py         # Dashboard, Login
│   ├── show_details.py # Show CRUD, Tabs
│   ├── show_assets.py  # File Uploads
│   └── show_io.py      # Import/Export (PDF, MA3, CSV)
├── templates/          # Jinja2 Templates
│   ├── index.html      # Dashboard
│   ├── show_detail.html # Show-Detailseite
│   └── partials/       # Tab-Inhalte
└── tests/              # pytest Unit Tests
```

## Aktuelle Features
- Show-Verwaltung mit Stammdaten
- Cue-Listen (Songs mit Mood, Farben, Notizen)
- Rig & Strom Setup
- Kontakt-Verwaltung
- Regie-Ansicht
- PDF/MA3/CSV Export

## Geplante Erweiterung: Modularer MVP
**Ziel**: Benutzer wählen beim Erstellen einer Show, welche Module sie brauchen.

| Modul | Funktion |
|-------|----------|
| stammdaten | Basis-Infos |
| cuelist | Songs / Cue-Liste |
| patch | Rig & Strom |
| kontakte | Ansprechpartner |
| requisiten | Props |
| video | Medien |

## Wichtige Kommandos
```bash
# App starten
python app.py
# oder: start.bat

# Tests ausführen
python -m pytest tests/ -v

# Abhängigkeiten
pip install -r requirements.txt
```

## Login
- **User**: Admin
- **Passwort**: Admin123
