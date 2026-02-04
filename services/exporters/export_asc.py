from core.show_logic import find_show


def export_show_to_asc(show_id: int, file_path: str):
    """
    Exportiert die Show im USITT ASCII Format (.asc).
    Das ist ein Industriestandard, den EOS sehr gut lesen kann.
    """
    show = find_show(show_id)
    if not show:
        raise ValueError("Show not found")
        
    songs = show.get("songs", [])
    cuelist_id = show.get("eos_cuelist_id", 1)
    
    lines = []
    
    # Header Information
    lines.append("! USITT ASCII Export from Lichtassistent")
    lines.append("Ident 3:0")
    lines.append(f"$$")
    
    lines.append("! -------------------------------------------------")
    lines.append("! Cues")
    lines.append("! -------------------------------------------------")
    
    for idx, song in enumerate(songs, 1):
        cue_num = song.get("order_index", idx)
        name = song.get("name", f"Cue {cue_num}")
        mood = song.get("mood", "")
        colors = song.get("colors", "")
        notes = (song.get("special_notes") or "") + " " + (song.get("general_notes") or "")
        
        # Label zusammenbauen
        label = name
        if mood or colors:
            label += f" [{mood}|{colors}]"
        
        # Cue Definition
        lines.append(f"CUE {cue_num}")
        lines.append("UP 0")
        lines.append("DOWN 0")
        # Dummy Channel damit der Cue existiert (optional, aber sicherer)
        # lines.append("Chan 1@0") 
        
        # Text/Label
        if label:
            # Anführungszeichen escapen oder entfernen
            clean_label = label.replace('"', "'")
            lines.append(f'TEXT "{clean_label}"')
            
        lines.append("$$")
        
    lines.append("ENDDATA")
    
    import os
    export_dir = os.path.dirname(file_path)
    if export_dir:
        os.makedirs(export_dir, exist_ok=True)
        
    with open(file_path, "w", encoding="ascii", errors="replace") as f:
        f.write("\n".join(lines))
