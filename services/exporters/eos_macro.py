# eos_macro.py
from __future__ import annotations
from pathlib import Path
from datetime import datetime
import re
from typing import Any, List

def _safe_text(text: str) -> str:
    """Bereinigt Text für EOS Kommandozeile (keine Anführungszeichen)"""
    if text is None:
        return ""
    text = str(text)
    # Entferne Zeilenumbrüche und Anführungszeichen
    text = text.replace('\n', ' ').replace('\r', ' ').replace('"', "'")
    # Entferne doppelte Leerzeichen
    text = re.sub(r'\s+', ' ', text).strip()
    return text

def _get_attr(obj: Any, *names: str, default: Any = "") -> Any:
    for n in names:
        if hasattr(obj, n):
            v = getattr(obj, n)
            if v is not None:
                return v
    return default

def _iter_items(db_show: Any) -> List[Any]:
    for cand in ("songs", "cues", "scenes", "szenen"):
        if hasattr(db_show, cand):
            items = getattr(db_show, cand)
            try:
                return list(items)
            except TypeError:
                return []
    return []

def build_eos_macro(db_show: Any) -> str:
    """
    Erzeugt eine Liste von EOS Kommandos als Text.
    Diese können in ein EOS Macro kopiert werden oder als .txt importiert werden.
    """
    title = str(_get_attr(db_show, "title", "name", default="Show"))
    macro_id = _get_attr(db_show, "eos_macro_id", default=101)
    items = _iter_items(db_show)
    
    lines: List[str] = []
    lines.append(f"Clear_CommandLine")
    
    # Optional: Benenne die Show / Cuelist (hier als Kommentar)
    lines.append(f"# EOS Macro Export for: {title}")
    lines.append(f"# Macro ID: {macro_id}")
    lines.append(f"# Generated: {datetime.now().isoformat(timespec='seconds')}")
    lines.append("")

    # Macro Header (falls wir das Macro direkt definieren wollen)
    # Macro X Label LABEL Enter
    lines.append(f"Macro {macro_id} Label {title} Enter")
    lines.append("")

    for i, it in enumerate(items, start=1):
        # Wir nutzen den order_index oder die Schleifen-Variable
        cue_num = _get_attr(it, "order_index", default=i)
        cue_name = _safe_text(_get_attr(it, "title", "name", default=f"Cue {cue_num}"))
        mood = _safe_text(_get_attr(it, "mood", "stimmung", default=""))
        colors = _safe_text(_get_attr(it, "colors", "farben", default=""))
        notes = _safe_text(_get_attr(it, "special_notes", "general_notes", "notes", default=""))

        # Label kombinieren (Name + [Mood|Colors])
        label = cue_name
        if mood or colors:
            label += f" [{mood}|{colors}]"
        
        # EOS Syntax: Cue X Label LABEL_TEXT Enter
        lines.append(f"Cue {cue_num} Label {label} Enter")
        
        # Falls Notizen vorhanden: Cue X Notes NOTES_TEXT Enter
        if notes:
            lines.append(f"Cue {cue_num} Notes {notes} Enter")

    return "\n".join(lines)

def export_eos_macro_to_file(db_show: Any, export_dir: str | Path | None = None) -> Path:
    """Schreibt das Macro in eine Textdatei im exports Verzeichnis"""
    if export_dir:
        out_dir = Path(export_dir).resolve()
    else:
        out_dir = (Path(__file__).resolve().parent.parent.parent / "exports").resolve()

    out_dir.mkdir(parents=True, exist_ok=True)
    
    title = _get_attr(db_show, "title", "name", default="Show")
    safe_title = re.sub(r"[^\w\-]+", "_", str(title))
    filename = f"{safe_title}_EOS_Macro.txt"
    file_path = out_dir / filename
    
    content = build_eos_macro(db_show)
    file_path.write_text(content, encoding='utf-8')
    
    return file_path
