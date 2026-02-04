from flask import Blueprint, request, redirect, url_for, abort, send_file, render_template, current_app
from core.show_logic import find_show, save_data, sync_entire_show_to_db, ensure_show_in_db
from core.models import Show as ShowModel, db
from services.exporters.export_nomad_csv import export_cues_to_csv, export_cues_to_xlsx
from services.exporters.export_asc import export_show_to_asc
from services.exporters.pdf_export import build_show_report_pdf, build_techrider_pdf
from services.exporters.pdf_export_cuelist import build_cuelist_pdf
from services.pdf_import_service import extract_cues_from_pdf
from services.exporters import ma3_export
from services.exporters import eos_macro
from services.exporters import mvr_export

import io
import os
import json
import html
import re

show_io_bp = Blueprint('show_io', __name__)

# Zentraler Export-Pfad (Absolut, basierend auf CWD/Exe-Ort)
# WICHTIG: Damit landen Dateien in 'CueX Lite/exports' und nicht in '_internal/exports'
USER_EXPORTS_DIR = os.path.join(os.getcwd(), "exports")
os.makedirs(USER_EXPORTS_DIR, exist_ok=True)

@show_io_bp.route("/show/<int:show_id>/export_nomad_csv", methods=["GET"])
def export_nomad_csv(show_id: int):
    filename = f"nomad_show_{show_id}.csv"
    file_path = os.path.join(USER_EXPORTS_DIR, filename)
    export_cues_to_csv(show_id, file_path)
    return send_file(file_path, as_attachment=True, download_name=filename)

@show_io_bp.route("/show/<int:show_id>/export_eos_xlsx", methods=["GET"])
def export_eos_xlsx(show_id: int):
    filename = f"eos_show_{show_id}.xlsx"
    file_path = os.path.join(USER_EXPORTS_DIR, filename)
    export_cues_to_xlsx(show_id, file_path)
    return send_file(file_path, as_attachment=True, download_name=filename)

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
    file_path = os.path.join(USER_EXPORTS_DIR, filename)
    
    export_show_to_asc(show_id, file_path)
    # WICHTIG: Absoluten Pfad an send_file übergeben!
    return send_file(file_path, as_attachment=True, download_name=filename)

@show_io_bp.route("/show/<int:show_id>/import_cuelist_pdf", methods=["POST"])
def import_cuelist_pdf(show_id: int):
    show = find_show(show_id)
    if not show:
        abort(404)
    file = request.files.get("pdf_file")
    if not file or not file.filename.lower().endswith(".pdf"):
        return "Keine PDF-Datei hochgeladen!", 400
    
    # Logic moved to service
    try:
        text, cues, roles = extract_cues_from_pdf(file.read())
    except Exception as e:
        return f"Fehler beim Lesen der PDF: {e}", 400

    return render_template("import_cuelist_pdf_preview.html", show=show, pdf_text=text, cues=cues, roles=roles)


@show_io_bp.route("/show/<int:show_id>/import_cuelist_pdf_commit", methods=["POST"])
def import_cuelist_pdf_commit(show_id: int):
    show = find_show(show_id)
    if not show:
        abort(404)
    cues_json = request.form.get("cues_json")
    export_target = request.form.get("export_target", "")  # ma3, eos, oder leer
    
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
    
    # Direkter Export wenn gewünscht
    if export_target == "ma3":
        return redirect(url_for("show_io.export_ma3", show_id=show_id))
    elif export_target == "eos":
        return redirect(url_for("show_io.export_asc", show_id=show_id))
    
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
    from flask import session
    from pathlib import Path
    import shutil
    import zipfile
    
    db_show = ensure_show_in_db(show_id)
    if not db_show:
        abort(404)
    
    # Optional: Sequence ID aus Query-Parameter (für direkten Export mit benutzerdefinierter ID)
    seq_id = request.args.get('sequence_id', type=int)
    if seq_id:
        db_show.ma3_sequence_id = seq_id
        db.session.commit()
    
    # Plugin als ZIP erstellen
    # Übergabe des USER_EXPORTS_DIR
    ma3_export_dir = os.path.join(USER_EXPORTS_DIR, "ma3")
    zip_path = ma3_export.export_ma3_plugin_to_file(db_show, export_dir=ma3_export_dir)
    
    # Prüfen ob MA3 Plugin-Pfad gesetzt ist
    ma3_plugin_path = session.get('ma3_plugin_path', '').strip()
    if ma3_plugin_path and Path(ma3_plugin_path).exists():
        # Direkt in den Plugin-Ordner extrahieren
        try:
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(ma3_plugin_path)
            # Erfolgsmeldung als JSON zurückgeben (für AJAX) oder Redirect
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return {"success": True, "message": f"Plugin nach {ma3_plugin_path} exportiert!", "path": ma3_plugin_path}
            # Flash-Message und redirect bei normalem Request
            from flask import flash
            flash(f"Plugin direkt nach {ma3_plugin_path} exportiert!", "success")
            return redirect(url_for("show_details.show_detail", show_id=show_id, tab="songs"))
        except Exception as e:
            # Fallback auf Download bei Fehler
            pass
    
    # Normaler Download als Fallback
    return send_file(zip_path, as_attachment=True, download_name=zip_path.name, mimetype="application/zip")


@show_io_bp.route("/show/<int:show_id>/export_eos_macro")
def export_eos_macro(show_id: int):
    db_show = ensure_show_in_db(show_id)
    if not db_show:
        abort(404)
    # Pass export_dir
    file_path = eos_macro.export_eos_macro_to_file(db_show, export_dir=USER_EXPORTS_DIR)
    return send_file(file_path, as_attachment=True, download_name=file_path.name, mimetype="text/plain")


@show_io_bp.route("/show/<int:show_id>/export_mvr")
def export_mvr(show_id: int):
    show = find_show(show_id)
    if not show:
        abort(404)
    # MVR export_dir
    mvr_export_dir = os.path.join(USER_EXPORTS_DIR, "mvr")
    file_path = mvr_export.export_mvr_to_file(show, export_dir=mvr_export_dir)
    return send_file(file_path, as_attachment=True, download_name=file_path.name, mimetype="application/zip")
