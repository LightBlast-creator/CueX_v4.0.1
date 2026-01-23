# CueX – Projekt-Regeln & Guidelines

Diese Regeln dienen als Leitfaden für die Entwicklung von CueX, um Konsistenz, Wartbarkeit und ein erstklassiges Nutzungserlebnis zu gewährleisten. 

Niemals Selber login Daten von GDTF eingeben das MUSS der User Selber machen um sich mit GTDF zu verbinden. 

## 1. Sprache & Dokumentation
- **Frontend/UI**: Die Benutzeroberfläche ist aktuell auf **Deutsch** (Labels, Buttons, Fehlermeldungen).

- **Internationalisierung (i18n)**: Die Architektur soll so vorbereitet werden, dass eine spätere Übersetzung auf **Englisch** (oder andere Sprachen) einfach möglich ist (z.B. durch Vermeidung von hardcoded Strings in komplexer Logik).
- **Kommentare**: Docstrings und Kommentare im Code werden auf **Deutsch** verfasst.
- **Code**: Variablen, Funktionen, Klassen und Datenbankfelder werden konsequent in **Englisch** benannt.
- **Git**: Commit-Messages sollten kurz und aussagekräftig sein (vorzugsweise Englisch oder Deutsch, aber konsistent).

## 2. Architektur (Backend)
- **Flask Blueprints**: Neue Routen müssen in Blueprints organisiert werden (siehe Verzeichnis `routes/`).
- **Separation of Concerns**: 
    - Logik gehört in `show_logic.py` oder spezifische Service-Module.
    - Routen (Blueprints) dienen nur der Anfrageverarbeitung und Response-Erstellung.
    - Modelle befinden sich ausschließlich in `models.py`.
- **Datenbank**: SQLAlchemy wird für alle Datenbankoperationen genutzt. Manuelle SQL-Queries sind zu vermeiden.

## 3. Frontend & Design (UI/UX)
- **Ästhetik**: CueX soll ein **Modernes & Premium-Gefühl** vermitteln.
    - Nutzung von Glassmorphism (subtile Transpanrenz, Unschärfe).
    - Harmonische Farbpaletten (kein Standard-Rot/Blau).
    - Weiche Übergänge und Animationen.
- **Frameworks**: Bootstrap 5 für das Grid-System; Vanilla CSS für individuelles Styling.
- **Responsive Design**: Die Anwendung muss auf verschiedenen Bildschirmgrößen (Tablet/Desktop) flüssig funktionieren.

## Testen 
Nach jedem Ein/Ausbau oder Umbau von features. 

## 4. Qualitätssicherung & Tests
- **Testing**: Für neue Features müssen entsprechende Unittests in `tests/` erstellt werden.
- **Verifizierung**: Vor jedem Merge/Abschluss eines Features müssen die vorhandenen Tests mit `pytest` erfolgreich durchlaufen.
- **Fehlerbehandlung**: Klare Fehlermeldungen an den User im Frontend; detailliertes Logging im Backend.

## 5. Arbeitsweise mit der KI (Antigravity)
- **Transparenz**: Bei größeren Änderungen wird immer erst ein `implementation_plan.md` erstellt.
- **Validierung**: Nach Änderungen wird die Funktionalität (wenn möglich) via Browser-Tool oder Tests verifiziert.

## SOFTWARE
Die Anwendung CueX soll später auch die Möglichkeit haben sich in eine Vollwerige Software zu entwickeln. 

## LOGIN
Verhindetere dass dir der fehler mit admin/admin passiert das stimmt nicht!
zur ENtwicklung sind die Login Daten Benutzername: Admin und Passwort Admin123

## Anwendung starten
Printe mir bitte immer den Befehl wie ich die Anwendung hart beenden kann und den Server aus mache.

## DSGVO
achte wie ein absoluter Experte auf die DSGVO konformität, mach keine ausnahmen, die anwendung muss später zu 100% DSGVO konform sein. 

## Arbeitstag ende 
Immer wenn wir den Arbeitstag beenden muss der code und die anwendung refractort werden. danach ein Ganzer anwendungstest durchführen. 

## Github 
Github werde nur ich befüllen du hast da Absolut nichts zu machen !