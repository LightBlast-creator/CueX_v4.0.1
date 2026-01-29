# CueX – v4.0.1+

**Modern Lighting Design & Production Assistant**

CueX ist eine webbasierte Anwendung für Lichtdesigner und Operator zur Planung, Dokumentation und Durchführung von Lichtshows. Der Fokus liegt auf klarer Kommunikation, effizientem Workflow und modernster Technologie (inkl. NLP und GDTF).

---

## 🚀 Features

### 1. 🎛 Show-Dashboard & Stammdaten
- Verwaltung mehrerer Shows und Projekte.
- Detaillierte Stammdaten: Artist, Venue, Crew, Dates.
- **NEU:** Modernes UI mit Dark Mode und Glassmorphism-Elementen.

### 2. 💡 Rig-Planung & Patch
- **Rig Editor:** Visuelle Planung auf einer 2D-Bühne.
- **Array Arrangement Tool:** Automatische Anordnung von Lampen in Linien, Kreisen oder Gittern.
- **GDTF-Integration:** Suche und Import von Fixture-Modi direkt aus der GDTF Share Datenbank.
- **MVR Export:** Exportiere dein Rig als `.mvr` Datei für Pult-Import (GrandMA3, Vectorworks etc.).
- **Patch-Liste:** DMX-Adressierung, Universen, Modes.

### 3. 🎵 Song- & Cue-Management
- **Cue-Liste:** Detaillierte Planung von Songs und Szenen (Mood, Farbe, Bewegung).
- **Regie-Ansicht:** Optimierte Ansicht für den FOH-Betrieb während der Show.
- **PDF-Import mit KI:** Lade eine PDF-Setliste hoch – CueX extrahiert Songs und Cues automatisch mittels NLP (`spacy`).

### 4. 📄 Export & Dokumentation
- **Show-Report (PDF):** Sauber formatierte Übersicht für die Produktion.
- **Tech-Rider (PDF):** Technische Anforderungen für Venues.
- **GrandMA3 Plugin:** Exportiere Cues direkt als MA3-Plugin.
- **ETC EOS:** Export als `.asc` Datei.

### 5. 🛠 Tools & Helfer
- **Checklisten:** Pre-Production, Aufbau, Show-Tag.
- **Kontakte:** Crew- und Venue-Kontakte verwalten.
- **Requisiten & Video:** Zusätzliche Listen für Props und Video-Content.

---

## 🛠 Tech Stack

- **Backend:** Python 3.13+ (Flask, SQLAlchemy)
- **Frontend:** HTML5, Bootstrap 5, Vanilla JS (Canvas API)
- **Datenbank:** SQLite (Lokal)
- **KI / NLP:** spaCy (`de_core_news_sm`) für PDF-Analyse
- **MVR / GDTF:** `pymvr`, GDTF-API Integration
- **PDF:** ReportLab

---

## 📦 Installation & Setup

1. **Repository klonen**
   ```bash
   git clone <repo-url>
   cd CueX
   ```

2. **Virtuelle Umgebung erstellen & aktivieren**
   ```bash
   python -m venv .venv
   # Windows:
   .venv\Scripts\activate
   # Linux/Mac:
   source .venv/bin/activate
   ```

3. **Dependencies installieren**
   ```bash
   pip install -r requirements.txt
   ```

4. **NLP-Modell laden** (Wichtig für PDF-Import!)
   ```bash
   python -m spacy download de_core_news_sm
   ```

5. **Server starten**
   ```bash
   python app.py
   ```
   Die App ist unter `http://localhost:8080` erreichbar.
   (Zum Beenden: `STRG+C` im Terminal)

---

## 📱 Mobile Companion (Working Title)
*In Entwicklung...*
- Geplant: QR-Code am Case scannen → Patch-Info auf dem Handy.
- Geplant: Einfacher DMX-Check via ArtNet.

---

## 🤝 Contribution & Rules
Bitte beachte die Projekt-Regeln (`.agent/RULES.md` oder Memory), insbesondere:
- Keine echten GDTF-Logindaten im Code committen.
- DSGVO-Konformität beachten.
- Frontend: Deutsch (UI), Code: Englisch (Vars/Funcs).
