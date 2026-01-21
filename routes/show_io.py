from flask import Blueprint, request, redirect, url_for, abort, send_file, render_template, current_app
from show_logic import find_show, save_data, sync_entire_show_to_db
from models import Show as ShowModel
from exports.export_nomad_csv import export_cues_to_csv
from pdf_export import build_show_report_pdf, build_techrider_pdf
from pdf_export_cuelist import build_cuelist_pdf
import ma3_export
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

    # 1. Rollen extrahieren
    roles = []
    roles_section = re.search(r"Rollen:(.*?)(?:Ort:|Zeit:|Szene|\n\n)", text, re.DOTALL | re.IGNORECASE)
    if roles_section:
        for line in roles_section.group(1).splitlines():
            line = line.strip()
            if line:
                role = re.split(r"[\s\t\-–—:]+", line, 1)[0]
                if role and role.upper() == role:
                    roles.append(role)
                elif role:
                    roles.append(role.split()[0])

    if not roles:
        from collections import Counter
        import spacy.lang.de.stop_words as stopwords_mod
        stopwords = set(stopwords_mod.STOP_WORDS)
        word_counter = Counter()
        for line in text.splitlines():
            words = re.findall(r"\b[A-ZÄÖÜß][a-zäöüß]+\b", line)
            if words and line and line[0].isupper():
                words = words[1:] if len(words) > 1 else []
            for w in words:
                if w.lower() not in stopwords and len(w) > 1:
                    word_counter[w] += 1
        roles.extend([w for w, c in word_counter.items() if c >= 2])

    spacy_roles = set(ent.text for ent in doc.ents if ent.label_ == 'PER')
    for r in spacy_roles:
        if r not in roles:
            roles.append(r)

    # 2. Szenen und Cues extrahieren
    cues = []
    spacy_scenes = set(ent.text for ent in doc.ents if ent.label_ in ('ORG', 'LOC') and 'Szene' in ent.text)
    spacy_cues = [ent.text for ent in doc.ents if ent.label_ in ('MISC', 'EVENT')]
    
    for s in spacy_scenes:
        if s not in [c.get('scene') for c in cues]:
            cues.append({'scene': s, 'role': None, 'text': '', 'uncertain': True})
    for c in spacy_cues:
        cues.append({'scene': None, 'role': None, 'text': c, 'uncertain': True})

    current_scene = None
    current_role = None
    current_text = []
    role_patterns = [re.compile(rf"^\s*{re.escape(role)}[\s:：-]*", re.IGNORECASE) for role in roles]
    marker_patterns = [re.compile(r"(Licht|Ton|Cue|Szene|Musik|Effekt|Sound)", re.IGNORECASE)]
    cue_number_pattern = re.compile(r"^\s*\d+[.:]?\s*")

    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        if re.match(r"Szene ?\d+", line, re.IGNORECASE):
            if current_role and current_text:
                cues.append({"scene": current_scene, "role": current_role, "text": " ".join(current_text), "uncertain": False})
            current_scene = line
            current_role = None
            current_text = []
            continue
        
        matched_role = None
        for idx, pat in enumerate(role_patterns):
            m = pat.match(line)
            if m:
                matched_role = roles[idx]
                break
        
        if matched_role:
            if current_role and current_text:
                cues.append({"scene": current_scene, "role": current_role, "text": " ".join(current_text), "uncertain": False})
            current_role = matched_role
            rest = line[m.end():].strip()
            current_text = [rest] if rest else []
            continue
            
        marker_found = any(pat.search(line) for pat in marker_patterns)
        cue_number_found = cue_number_pattern.match(line)
        if marker_found or cue_number_found:
            cues.append({"scene": current_scene, "role": None, "text": line, "uncertain": True})
            continue
            
        if current_role:
            current_text.append(line)
        else:
            cues.append({"scene": current_scene, "role": None, "text": line, "uncertain": True})
            
    if current_role and current_text:
        cues.append({"scene": current_scene, "role": current_role, "text": " ".join(current_text), "uncertain": False})

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
    db_show = ShowModel.query.get_or_404(show_id)
    file_path = ma3_export.export_ma3_plugin_to_file(db_show)
    return send_file(file_path, as_attachment=True, download_name=file_path.name, mimetype="text/x-lua")
