# Anleitung: Import in GrandMA3

Hier erfährst du, wie du das generierte Lua-Plugin in deine GrandMA3 Console oder onPC importierst.

## 1. Exportieren & Vorbereiten
1.  Klicke im Lichtassistenten auf **"GrandMA3 Plugin (.zip)"**.
2.  Lade die Datei herunter.
3.  Entpacke die ZIP-Datei. Du erhältst einen Ordner, der eine `.xml` Datei und einen Unterordner mit `.lua` Dateien enthält.
4.  **USB-Stick vorbereiten**:
    *   Erstelle auf deinem USB-Stick (oder im MA3 Verzeichnis auf dem PC) folgenden Pfad:
        `grandMA3/gma3_library/datapools/plugins`
    *   Kopiere die entpackten Dateien (die XML und den zugehörigen Ordner) genau dort hinein.

## 2. In GrandMA3 importieren
1.  Öffne deine Show.
2.  Öffne einen **Plugin Pool** (oder erstelle ein Fenster dafür).
3.  Drücke **Edit** und klicke auf ein leeres Feld im Pool.
4.  Klicke unten auf **Import**.
5.  Wähle oben im Reiter deinen **USB-Stick** (oder `Internal`, wenn du am selben PC bist).
6.  Wähle das Plugin aus (Name der Show oder `Lichtassistent_Plugin`).
7.  Klicke **Import**.

## 3. Plugin starten
1.  Klicke einfach auf das Plugin im Pool.
2.  Es öffnet sich ein Pop-Up.
3.  Wähle **"Create/Update Sequ"**.
4.  Das Plugin erstellt nun automatisch:
    *   Eine Sequence mit allen Cues.
    *   Die passenden Labels, Notizen und Farben.
5.  Fertig! 💡
