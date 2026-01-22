---
description: Richtet die Entwicklungsumgebung für CueX ein
---

Um das Projekt lokal einzurichten:

// turbo-all
1. Virtuelle Umgebung erstellen (falls nicht vorhanden)
```powershell
python -m venv .venv
```

2. Abhängigkeiten installieren
```powershell
.\.venv\Scripts\activate; pip install -r requirements.txt
```

> [!NOTE]
> Dieser Workflow stellt sicher, dass alle notwendigen Python-Pakete installiert sind.
