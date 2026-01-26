from flask import Blueprint, request, redirect, url_for, abort, send_file, render_template, current_app
from show_logic import find_show, save_data, sync_entire_show_to_db
from models import Show as ShowModel, db
from exports.export_nomad_csv import export_cues_to_csv, export_cues_to_xlsx
from exports.export_asc import export_show_to_asc
from pdf_export import build_show_report_pdf, build_techrider_pdf
from pdf_export_cuelist import build_cuelist_pdf
import ma3_export
import exports.eos_macro as eos_macro
import io
import json
import html
import re
import spacy
import pdfplumber

show_io_bp = Blueprint('show_io', __name__)

@show_io_bp.route("/show/<int:show_id>/export_nomad_csv", methods=["GET"])
def export_nomad_csv(show_id: int):
    file_path = f"exports/nomad_show_{show_id}.csv"
    export_cues_to_csv(show_id, file_path)
    return send_file(file_path, as_attachment=True, download_name=f"nomad_show_{show_id}.csv")

@show_io_bp.route("/show/<int:show_id>/export_eos_xlsx", methods=["GET"])
def export_eos_xlsx(show_id: int):
    file_path = f"exports/eos_show_{show_id}.xlsx"
    export_cues_to_xlsx(show_id, file_path)
    return send_file(file_path, as_attachment=True, download_name=f"eos_show_{show_id}.xlsx")

@show_io_bp.route("/show/<int:show_id>/export_asc", methods=["GET"])
def export_asc(show_id: int):
    show = find_show(show_id)
    if not show:
        abort(404)
        
    # Sicheren Dateinamen erstellen
    custom_name = request.args.get("filename")
    if custom_name:
        # User-Eingabe säubern (nur erlaubte Zeichen, aber Leerzeichen ok)
        safe_title = re.sub(r'[\\/*?:"<>|]', "", custom_name)
    else:
        # Fallback auf Show-Titel
        raw_title = show.get("title", f"Show {show_id}")
        safe_title = re.sub(r'[\\/*?:"<>|]', "", raw_title) # Windows forbidden chars entfernen
        safe_title = safe_title.replace(" ", "_")
    
    # Endung .asc sicherstellen
    if not safe_title.lower().endswith(".asc"):
        safe_title += ".asc"
    
    filename = safe_title
    file_path = f"exports/{filename}"
    
    export_show_to_asc(show_id, file_path)
    return send_file(file_path, as_attachment=True, download_name=filename)

@show_io_bp.route("/show/<int:show_id>/import_cuelist_pdf", methods=["POST"])
def import_cuelist_pdf(show_id: int):
    show = find_show(show_id)
    if not show:
        abort(404)
    file = request.files.get("pdf_file")
    if not file or not file.filename.lower().endswith(".pdf"):
        return "Keine PDF-Datei hochgeladen!", 400
    pdf_bytes = file.read()
    text = ""
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"

    nlp = spacy.load('de_core_news_sm')
    doc = nlp(text)

    # 1. Rollen extrahieren - Verbesserter Algorithmus für Theaterskripte
    roles = []
    roles_with_description = {}  # {role_name: description}
    
    # Strategie 1: Suche nach "Rollen:" Abschnitt und parse Bullet-Point-Format
    # Pattern: • MARA: Regisseurin (Mitte 30 bis 50). Beschreibung...
    roles_section = re.search(r"Rollen[:\s]*(.*?)(?:\n\n|\nOrt:|\nZeit:|\nSzene|\n[A-Z]{2,}:)", text, re.DOTALL | re.IGNORECASE)
    if roles_section:
        for line in roles_section.group(1).splitlines():
            line = line.strip()
            # Überspringe leere Zeilen
            if not line:
                continue
            # Pattern für Bullet-Points: • NAME: Beschreibung oder - NAME: Beschreibung
            bullet_match = re.match(r'^[•\-\*]\s*([A-ZÄÖÜ][A-ZÄÖÜa-zäöüß\s]+?):\s*(.*)$', line)
            if bullet_match:
                role_name = bullet_match.group(1).strip()
                description = bullet_match.group(2).strip()
                if role_name and role_name not in roles:
                    roles.append(role_name)
                    roles_with_description[role_name] = description
                continue
            # Pattern ohne Bullet: NAME: Beschreibung (wenn Zeile mit Großbuchstaben beginnt)
            colon_match = re.match(r'^([A-ZÄÖÜ][A-ZÄÖÜa-zäöüß\s]+?):\s*(.*)$', line)
            if colon_match:
                role_name = colon_match.group(1).strip()
                description = colon_match.group(2).strip()
                # Nur akzeptieren wenn es wie ein Name aussieht (max 3 Wörter, keine Satzzeichen)
                if role_name and len(role_name.split()) <= 3 and role_name not in roles:
                    roles.append(role_name)
                    roles_with_description[role_name] = description
    
    # Strategie 2: Suche nach GROSSBUCHSTABEN-Namen gefolgt von Doppelpunkt im gesamten Text
    # Pattern: MARA: oder LEO: (typisch für Theaterskripte)
    if not roles:
        uppercase_roles = re.findall(r'^[•\-\*\s]*([A-ZÄÖÜ][A-ZÄÖÜ\s]+):\s', text, re.MULTILINE)
        for role in uppercase_roles:
            role = role.strip()
            # Filtere technische Begriffe aus
            if role and role not in roles and role.upper() not in ['SZENE', 'ORT', 'ZEIT', 'CUE', 'LICHT', 'TON', 'MUSIK', 'ROLLEN', 'DATUM']:
                roles.append(role)
    
    # Strategie 3: Suche nach Pattern "• NAME:" am Zeilenanfang (auch gemischte Groß/Klein)
    if not roles:
        bullet_roles = re.findall(r'^[•\-\*]\s*([A-ZÄÖÜ][a-zäöüßA-ZÄÖÜ\s]+?):', text, re.MULTILINE)
        for role in bullet_roles:
            role = role.strip()
            if role and role not in roles and len(role.split()) <= 3:
                roles.append(role)
    
    # Strategie 4: Fallback auf spaCy NER für Personennamen (nur wenn noch keine Rollen gefunden)
    if not roles:
        spacy_roles = set(ent.text for ent in doc.ents if ent.label_ == 'PER')
        for r in spacy_roles:
            if r not in roles and len(r) > 1:
                roles.append(r)
    
    # Bereinige Rollennamen (entferne Klammern, führende/trailing Leerzeichen)
    roles = [re.sub(r'\s*\([^)]*\)\s*', '', role).strip() for role in roles]
    roles = [role for role in roles if role]  # Entferne leere Strings
    roles = list(dict.fromkeys(roles))  # Deduplizieren, Reihenfolge beibehalten

    # 2. Szenen und Dialog-Cues extrahieren
    # Theaterskript-Format: ROLLE: Dialog-Text oder • ROLLE: Dialog-Text
    cues = []
    current_scene = None
    current_role = None
    current_dialogue = []
    
    # Pattern für Rollen-Zeilen: "ROLLE:" oder "• ROLLE:" oder "ROLLE (Regieanweisung):"
    # Wir erstellen Patterns basierend auf den erkannten Rollen
    role_pattern_str = '|'.join([re.escape(role) for role in roles]) if roles else r'[A-ZÄÖÜ][A-ZÄÖÜa-zäöüß\s]+'
    
    # Pattern 1: Mit Doppelpunkt - "ROLLE: text" oder "ROLLE (Anweisung): text"
    dialogue_line_pattern_colon = re.compile(
        rf'^[•\-\*\s]*({role_pattern_str})(?:\s*\([^)]*\))?\s*[:：]\s*(.*)$',
        re.IGNORECASE
    )
    
    # Pattern 2: Ohne Doppelpunkt - "ROLLE text" (Rolle muss exakt am Zeilenanfang stehen)
    # Nur matchen wenn die Rolle bekannt ist und direkt am Anfang steht
    dialogue_line_pattern_no_colon = re.compile(
        rf'^({role_pattern_str})(?:\s*\([^)]*\))?\s+(.+)$',
        re.IGNORECASE
    ) if roles else None
    
    # Pattern für Szenen-Marker
    scene_pattern = re.compile(r'^(?:Szene|Scene|Akt|Act)\s*\d*\s*[:：\-–]?\s*(.*)?$', re.IGNORECASE)
    
    # Überspringe den Rollen-Abschnitt am Anfang (vor dem eigentlichen Dialog)
    in_roles_section = False
    roles_section_ended = False
    
    for line in text.splitlines():
        line_stripped = line.strip()
        if not line_stripped:
            continue
        
        # Erkenne Beginn des Rollen-Abschnitts
        if re.match(r'^Rollen\s*[:：]?\s*$', line_stripped, re.IGNORECASE):
            in_roles_section = True
            continue
        
        # Erkenne Ende des Rollen-Abschnitts (wenn eine Szene beginnt oder ein klarer Abschnittswechsel)
        if in_roles_section:
            # Prüfe ob wir noch im Rollen-Abschnitt sind (Bullet-Points oder Rollenbeschreibungen)
            if re.match(r'^[•\-\*]', line_stripped) or re.match(r'^[A-ZÄÖÜ][A-ZÄÖÜa-zäöüß\s]+:', line_stripped):
                # Noch im Rollen-Abschnitt - ist das eine Rollenbeschreibung?
                # Rollenbeschreibungen haben typischerweise Klammern mit Alter oder sind länger
                if '(' in line_stripped or len(line_stripped) > 100:
                    continue  # Überspringe Rollenbeschreibungen
            else:
                in_roles_section = False
                roles_section_ended = True
        
        # Prüfe auf Szenen-Marker
        scene_match = scene_pattern.match(line_stripped)
        if scene_match:
            # Speichere vorherigen Dialog
            if current_role and current_dialogue:
                cues.append({
                    'scene': current_scene,
                    'role': current_role,
                    'text': ' '.join(current_dialogue),
                    'uncertain': False
                })
            current_scene = line_stripped
            current_role = None
            current_dialogue = []
            continue
        
        # Prüfe auf Dialog-Zeile - erst mit Doppelpunkt, dann ohne
        dialogue_match = dialogue_line_pattern_colon.match(line_stripped)
        if not dialogue_match and dialogue_line_pattern_no_colon:
            dialogue_match = dialogue_line_pattern_no_colon.match(line_stripped)
        
        if dialogue_match:
            # Speichere vorherigen Dialog
            if current_role and current_dialogue:
                cues.append({
                    'scene': current_scene,
                    'role': current_role,
                    'text': ' '.join(current_dialogue),
                    'uncertain': False
                })
            
            # Starte neuen Dialog
            matched_role_name = dialogue_match.group(1).strip()
            dialogue_text = dialogue_match.group(2).strip() if dialogue_match.group(2) else ''
            
            # Finde die korrekte Rolle (case-insensitive Matching)
            current_role = None
            for role in roles:
                if role.upper() == matched_role_name.upper():
                    current_role = role
                    break
            if not current_role:
                current_role = matched_role_name
            
            current_dialogue = [dialogue_text] if dialogue_text else []
            continue
        
        # Fortsetzung des aktuellen Dialogs
        if current_role:
            current_dialogue.append(line_stripped)
        else:
            # Zeile ohne erkannte Rolle - als unsicheren Cue hinzufügen (nur wenn nicht im Rollen-Abschnitt)
            if not in_roles_section and roles_section_ended:
                # Prüfe ob es technische Marker enthält
                is_technical = any(marker in line_stripped.lower() for marker in ['licht', 'ton', 'cue', 'musik', 'effekt', 'sound'])
                if is_technical or len(line_stripped) > 20:
                    cues.append({
                        'scene': current_scene,
                        'role': None,
                        'text': line_stripped,
                        'uncertain': True
                    })
    
    # Letzten Dialog speichern
    if current_role and current_dialogue:
        cues.append({
            'scene': current_scene,
            'role': current_role,
            'text': ' '.join(current_dialogue),
            'uncertain': False
        })
    
    # Filtere leere Cues und dedupliziere
    cues = [c for c in cues if c.get('role') or c.get('text')]

    return render_template("import_cuelist_pdf_preview.html", show=show, pdf_text=text, cues=cues, roles=roles)


@show_io_bp.route("/show/<int:show_id>/import_cuelist_pdf_commit", methods=["POST"])
def import_cuelist_pdf_commit(show_id: int):
    show = find_show(show_id)
    if not show:
        abort(404)
    cues_json = request.form.get("cues_json")
    if not cues_json:
        return "Keine Cues erkannt oder übergeben! (Feld leer)", 400
    cues_json_decoded = html.unescape(cues_json)
    try:
        cues = json.loads(cues_json_decoded)
    except Exception as e:
        return f"Fehler beim Parsen der Cues! ({e})<br><pre>{cues_json_decoded}</pre>", 400
    if not cues or not isinstance(cues, list):
        return f"Keine Cues erkannt oder übergeben!<br><pre>{cues_json_decoded}</pre>", 400
    
    if "songs" not in show:
        show["songs"] = []
    order_index = max([s.get("order_index", 0) for s in show["songs"]], default=0) + 1
    for cue in cues:
        show["songs"].append({
            "id": int(1e6) + order_index,
            "order_index": order_index,
            "name": f"{cue.get('scene') or ''} {cue.get('role') or ''}".strip(),
            "mood": "",
            "colors": "",
            "movement_style": "",
            "eye_candy": "",
            "special_notes": cue.get("text", ""),
            "general_notes": "",
        })
        order_index += 1
    save_data()
    sync_entire_show_to_db(show)
    return redirect(url_for("show_details.show_detail", show_id=show_id, tab="songs"))


@show_io_bp.route("/show/<int:show_id>/export_cuelist_pdf")
def export_cuelist_pdf(show_id: int):
    show = find_show(show_id)
    if not show:
        abort(404)
    buffer, filename = build_cuelist_pdf(show)
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")


@show_io_bp.route("/show/<int:show_id>/export_pdf")
def export_show_pdf(show_id: int):
    show = find_show(show_id)
    if not show:
        return redirect(url_for("main.dashboard"))
    buffer, filename = build_show_report_pdf(show)
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")


@show_io_bp.route("/show/<int:show_id>/export_techrider")
def export_techrider_pdf(show_id: int):
    show = find_show(show_id)
    if not show:
        return redirect(url_for("main.dashboard"))
    buffer, filename = build_techrider_pdf(show)
    return send_file(buffer, as_attachment=True, download_name=filename, mimetype="application/pdf")


@show_io_bp.route("/show/<int:show_id>/export_ma3")
def export_ma3(show_id: int):
    db_show = db.session.get(ShowModel, show_id)
    if not db_show:
        # Fallback: Aus JSON laden und synchronisieren
        show_data = find_show(show_id)
        if show_data:
            sync_entire_show_to_db(show_data)
            db_show = db.session.get(ShowModel, show_id)
            
    if not db_show:
        abort(404)
    file_path = ma3_export.export_ma3_plugin_to_file(db_show)
    return send_file(file_path, as_attachment=True, download_name=file_path.name, mimetype="application/zip")


@show_io_bp.route("/show/<int:show_id>/export_eos_macro")
def export_eos_macro(show_id: int):
    db_show = db.session.get(ShowModel, show_id)
    if not db_show:
        # Fallback
        show_data = find_show(show_id)
        if show_data:
            sync_entire_show_to_db(show_data)
            db_show = db.session.get(ShowModel, show_id)
            
    if not db_show:
        abort(404)
    file_path = eos_macro.export_eos_macro_to_file(db_show)
    return send_file(file_path, as_attachment=True, download_name=file_path.name, mimetype="text/plain")
