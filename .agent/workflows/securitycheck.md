---
description: Security-Check vor Veröffentlichung des Projekts
---
# Security Check Workflow

Dieser Workflow prüft das Projekt auf sicherheitsrelevante Aspekte vor einer Veröffentlichung (z.B. auf GitHub).

## 1. Secrets & API-Keys suchen
Durchsuche den Code nach:
- API-Keys, Tokens, Secrets
- Hardcoded Passwörter
- Private Keys, Zertifikate

```bash
# Suche nach verdächtigen Patterns
grep -riE "(api_key|apikey|secret|password|token|private_key)" --include="*.py" --include="*.js" --include="*.json" --include="*.env" .
```

## 2. Prüfe .gitignore
Stelle sicher, dass folgende Dateien/Ordner ausgeschlossen sind:
- `.env` / `.env.*` (Environment-Variablen)
- `instance/` (SQLite-Datenbank mit Nutzerdaten)
- `*.db` (Datenbank-Dateien)
- `__pycache__/` und `*.pyc`
- `.venv/` oder `venv/`
- `exports/` (wenn Nutzerdaten enthalten)
- Jede Datei mit echten Credentials

## 3. Dateizugriffe prüfen
- App greift NUR auf relative Pfade zu (kein Zugriff auf System-Ordner)
- Alle Datei-Operationen sind auf das Projektverzeichnis beschränkt
- Export-Verzeichnis ist innerhalb des Projekts

## 4. Credential-Handling prüfen
- **GDTF-Credentials**: Müssen vom User eingegeben werden, dürfen NIEMALS im Code stehen
- **App-Login**: Hardcoded nur für Development (`Admin/Admin123`)
- **SECRET_KEY**: Muss in Produktion via Environment-Variable gesetzt werden

## 5. DSGVO-Checkliste
- [ ] Keine personenbezogenen Daten werden ohne Zustimmung gespeichert
- [ ] User müssen über Datenspeicherung informiert werden
- [ ] Daten können auf Anfrage gelöscht werden
- [ ] Keine Daten werden an Dritte übermittelt (außer GDTF Share mit User-Consent)

## 6. Vor Veröffentlichung: MUSS-Aktionen
1. `.gitignore` erstellen/aktualisieren (siehe Punkt 2)
2. `instance/` Ordner löschen oder aus Git entfernen
3. `data/shows.json` leeren oder durch Beispieldaten ersetzen
4. `exports/` Ordner leeren
5. Alle Debug-/Test-Dateien entfernen (`debug_*.txt`)
6. README mit Hinweis auf Credential-Eingabe aktualisieren

## 7. Empfehlung: .env Template
Erstelle eine `.env.example` Datei für User:
```
FLASK_SECRET_KEY=your-secret-key-here
# Generiere einen sicheren Key: python -c "import secrets; print(secrets.token_hex(32))"
```

## 8. Finale Prüfung
// turbo
```bash
# Prüfe auf sensible Dateien die nicht im Git sein sollten
git status --ignored
```
