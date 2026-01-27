from flask import Blueprint, render_template, request, redirect, url_for, abort, session, current_app, jsonify, make_response
from core.show_logic import find_show, save_data, sync_entire_show_to_db, MANUFACTURERS, create_song, create_check_item, toggle_check_item, remove_show, delete_check_item
from core.models import db, Show as ShowModel, ContactPersonModel

from services.power_service import calculate_rig_power

show_details_bp = Blueprint('show_details', __name__)

@show_details_bp.route("/show/<int:show_id>", methods=["GET"])
def show_detail(show_id: int):
    """
    Show-Detailseite: Stammdaten, Songs, Rig, Checklisten.
    Mit Tab-Logik: active_tab = meta | rig | songs | regie
    """
    show = find_show(show_id)
    if not show:
        abort(404)

    # Aktiven Tab aus Query-Parameter lesen (Standard: meta/Stammdaten)
    active_tab = request.args.get("tab", "meta")

    # ---------------- GET: Rig-Power-Berechnung ----------------
    rig = show.get("rig_setup", {}) or {}
    rig_power_summary = calculate_rig_power(rig)

    # Kontakte (aus der DB) holen
    db_show = db.session.get(ShowModel, show_id)
    contacts = db_show.contacts if db_show else []

    # Optional: restore values set by POST handlers (stored in session)
    restore_scroll = session.pop('restore_scroll', None)
    restore_tab = session.pop('restore_tab', None)

    # Template bekommt Show + Herstellerliste + aktiven Tab + Kontakte
    # Template bekommt Show + Herstellerliste + aktiven Tab + Kontakte
    resp = make_response(render_template(
        "show_detail.html",
        show=show,
        manufacturers=MANUFACTURERS,
        active_tab=active_tab,
        rig_power_summary=rig_power_summary,
        contacts=contacts,
        restore_scroll=restore_scroll,
        restore_tab=restore_tab,
    ))
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp

@show_details_bp.route("/show/<int:show_id>/update_meta", methods=["POST"])
def update_meta(show_id: int):
    show = find_show(show_id)
    if not show:
        abort(404)

    show["name"] = request.form.get("name", "").strip() or show.get("name", "")
    show["artist"] = request.form.get("artist", "").strip()
    show["date"] = request.form.get("date", "").strip()
    show["venue_type"] = request.form.get("venue_type", "").strip()
    show["genre"] = request.form.get("genre", "").strip()
    show["rig_type"] = request.form.get("rig_type", "").strip()
    show["regie"] = request.form.get("regie", "").strip()
    show["veranstalter"] = request.form.get("veranstalter", "").strip()
    show["vt_firma"] = request.form.get("vt_firma", "").strip()
    show["technischer_leiter"] = request.form.get("technischer_leiter", "").strip()
    show["notes"] = request.form.get("notes", "").strip()

    seq_raw = (request.form.get("ma3_sequence_id") or "").strip()
    if seq_raw:
        try:
            show["ma3_sequence_id"] = int(seq_raw)
        except ValueError:
            show["ma3_sequence_id"] = 101
    else:
        show["ma3_sequence_id"] = 101

    eos_seq_raw = (request.form.get("eos_macro_id") or "").strip()
    if eos_seq_raw:
        try:
            show["eos_macro_id"] = int(eos_seq_raw)
        except ValueError:
            show["eos_macro_id"] = 101
    else:
        show["eos_macro_id"] = 101

    eos_cl_raw = (request.form.get("eos_cuelist_id") or "").strip()
    if eos_cl_raw:
        try:
            show["eos_cuelist_id"] = int(eos_cl_raw)
        except ValueError:
            show["eos_cuelist_id"] = 1
    else:
        show["eos_cuelist_id"] = 1

    save_data()
    sync_entire_show_to_db(show)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify(success=True)

    return_tab = request.form.get("return_tab") or request.args.get("return_tab") or "meta"
    return redirect(url_for("show_details.show_detail", show_id=show_id, tab=return_tab))

@show_details_bp.route("/show/<int:show_id>/update_rig", methods=["POST"])
def update_rig(show_id: int):
    show = find_show(show_id)
    if not show:
        abort(404)

    rig = show.setdefault("rig_setup", {})
    # Use update() or manual assignment to preserve existing keys like 'visual_plan'
    rig["main_brand"] = request.form.get("rig_main_brand", "").strip()

    for prefix in ("spots", "washes", "beams", "blinders", "strobes"):
        counts = request.form.getlist(f"rig_{prefix}__count[]")
        manufacturers = request.form.getlist(f"rig_{prefix}__manufacturer[]")
        models = request.form.getlist(f"rig_{prefix}__model[]")
        modes = request.form.getlist(f"rig_{prefix}__mode[]")
        universes = request.form.getlist(f"rig_{prefix}__universe[]")
        addresses = request.form.getlist(f"rig_{prefix}__address[]")
        watts = request.form.getlist(f"rig_{prefix}__watt[]")
        phases = request.form.getlist(f"rig_{prefix}__phase[]")

        items = []
        for i, c in enumerate(counts):
            item = {
                "count": c.strip() if c else "",
                "manufacturer": (manufacturers[i].strip() if i < len(manufacturers) else ""),
                "model": (models[i].strip() if i < len(models) else ""),
                "mode": (modes[i].strip() if i < len(modes) else ""),
                "universe": (universes[i].strip() if i < len(universes) else ""),
                "address": (addresses[i].strip() if i < len(addresses) else ""),
                "watt": (watts[i].strip() if i < len(watts) else ""),
                "phase": (phases[i].strip() if i < len(phases) else ""),
            }
            items.append(item)
        if items:
            rig[f"{prefix}_items"] = items
        else:
            # Only update basic fields, don't wipe everything
            rig[f"{prefix}"] = request.form.get(f"rig_{prefix}", "").strip()
            rig[f"manufacturer_{prefix}"] = request.form.get(f"rig_manufacturer_{prefix}", "").strip()
            rig[f"universe_{prefix}"] = request.form.get(f"rig_universe_{prefix}", "").strip()
            rig[f"address_{prefix}"] = request.form.get(f"rig_address_{prefix}", "").strip()
            rig[f"watt_{prefix}"] = request.form.get(f"rig_watt_{prefix}", "").strip()
            rig[f"phase_{prefix}"] = request.form.get(f"rig_phase_{prefix}", "").strip()

    rig["positions"] = request.form.get("rig_positions", "").strip()
    rig["notes"] = request.form.get("rig_notes", "").strip()
    rig["power_main"] = request.form.get("rig_power_main", "").strip()
    rig["power_light"] = request.form.get("rig_power_light", "").strip()
    rig["power_sound"] = request.form.get("rig_power_sound", "").strip()
    rig["power_video"] = request.form.get("rig_power_video", "").strip()
    rig["power_foh"] = request.form.get("rig_power_foh", "").strip()
    rig["power_other"] = request.form.get("rig_power_other", "").strip()

    custom_counts = request.form.getlist("custom_devices__count[]")
    custom_names = request.form.getlist("custom_devices__name[]")
    custom_models = request.form.getlist("custom_devices__model[]")
    custom_modes = request.form.getlist("custom_devices__mode[]")
    custom_manufacturers = request.form.getlist("custom_devices__manufacturer[]")
    custom_universes = request.form.getlist("custom_devices__universe[]")
    custom_addresses = request.form.getlist("custom_devices__address[]")
    custom_watts = request.form.getlist("custom_devices__watt[]")
    custom_phases = request.form.getlist("custom_devices__phase[]")

    custom_devices = []
    for i in range(len(custom_counts)):
        if (
            (custom_counts[i] and custom_counts[i].strip()) or
            (custom_names[i] and custom_names[i].strip()) or
            (custom_manufacturers[i] and custom_manufacturers[i].strip())
        ):
            custom_devices.append({
                "count": custom_counts[i].strip() if i < len(custom_counts) else "",
                "name": custom_names[i].strip() if i < len(custom_names) else "",
                "manufacturer": custom_manufacturers[i].strip() if i < len(custom_manufacturers) else "",
                "model": custom_models[i].strip() if i < len(custom_models) else "",
                "mode": custom_modes[i].strip() if i < len(custom_modes) else "",
                "universe": custom_universes[i].strip() if i < len(custom_universes) else "",
                "address": custom_addresses[i].strip() if i < len(custom_addresses) else "",
                "watt": custom_watts[i].strip() if i < len(custom_watts) else "",
                "phase": custom_phases[i].strip() if i < len(custom_phases) else "",
            })
    rig["custom_devices"] = custom_devices

    save_data()
    sync_entire_show_to_db(show)
    
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"status": "success", "message": "Rig stored successfully"})
        
    return redirect(url_for("show_details.show_detail", show_id=show_id, tab="rig"))


@show_details_bp.route("/show/<int:show_id>/add_song", methods=["POST"])
def add_song_route(show_id: int):
    show = find_show(show_id)
    if not show:
        abort(404)
    create_song(
        show=show,
        name=request.form.get("song_name", "").strip(),
        mood=request.form.get("song_mood", "").strip(),
        colors=request.form.get("song_colors", "").strip(),
        movement_style=request.form.get("song_movement_style", "").strip(),
        eye_candy=request.form.get("song_eye_candy", "").strip(),
        special_notes=request.form.get("song_special_notes", "").strip(),
        general_notes=request.form.get("song_general_notes", "").strip(),
    )
    save_data()
    sync_entire_show_to_db(show)
    return redirect(url_for("show_details.show_detail", show_id=show_id, tab="songs"))


@show_details_bp.route("/show/<int:show_id>/checklists/add", methods=["POST"])
def add_check_item_route(show_id: int):
    show = find_show(show_id)
    if not show:
        abort(404)
    category = request.form.get("category", "")
    text = request.form.get("text", "").strip()
    if category in ("preproduction", "aufbau", "show") and text:
        create_check_item(show, category, text)
        save_data()
        sync_entire_show_to_db(show)
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"status": "success", "message": "Item added"})
        
    return_tab = request.form.get("tab") or request.args.get("tab") or "meta"
    return redirect(url_for("show_details.show_detail", show_id=show_id, tab=return_tab) + "#checklists")


@show_details_bp.route("/show/<int:show_id>/checklists/toggle", methods=["POST"])
def toggle_check_item_route(show_id: int):
    show = find_show(show_id)
    if not show:
        abort(404)

    category = request.form.get("category", "")
    try:
        item_id = int(request.form.get("item_id", ""))
    except (TypeError, ValueError):
        item_id = None

    if category in ("preproduction", "aufbau", "show") and item_id is not None:
        toggle_check_item(show, category, item_id)
        save_data()
        sync_entire_show_to_db(show)
        
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"status": "success", "message": "Item toggled"})
        
    return_tab = request.form.get("tab") or request.args.get("tab") or "meta"
    return redirect(url_for("show_details.show_detail", show_id=show_id, tab=return_tab) + "#checklists")


@show_details_bp.route("/show/<int:show_id>/checklists/update", methods=["POST"])
def update_check_item_route(show_id: int):
    show = find_show(show_id)
    if not show:
        abort(404)

    category = request.form.get("category", "")
    try:
        item_id = int(request.form.get("item_id", ""))
    except (TypeError, ValueError):
        item_id = None
    text = request.form.get("text", "").strip()

    if (
        category in ("preproduction", "aufbau", "show")
        and item_id is not None
        and "checklists" in show
        and isinstance(show["checklists"], dict)
    ):
        items = show["checklists"].get(category, [])
        for item in items:
            if item.get("id") == item_id:
                item["text"] = text
                break
        save_data()
        sync_entire_show_to_db(show)
        
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"status": "success", "message": "Item updated"})
        
    return_tab = request.form.get("tab") or request.args.get("tab") or "meta"
    return redirect(url_for("show_details.show_detail", show_id=show_id, tab=return_tab) + "#checklists")



@show_details_bp.route("/show/<int:show_id>/checklists/delete", methods=["POST"])
def delete_check_item_route(show_id: int):
    show = find_show(show_id)
    if not show:
        abort(404)
    category = request.form.get("category", "")
    try:
        item_id = int(request.form.get("item_id", ""))
    except (TypeError, ValueError):
        item_id = None
        
    if category and item_id is not None:
        delete_check_item(show, category, item_id)
        save_data()
        sync_entire_show_to_db(show)
        
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"status": "success", "message": "Item deleted"})
        
    return_tab = request.form.get("tab") or request.args.get("tab") or "meta"
    return redirect(url_for("show_details.show_detail", show_id=show_id, tab=return_tab) + "#checklists")


@show_details_bp.route("/show/<int:show_id>/regie", methods=["GET"])
def show_regie_view(show_id: int):
    show = find_show(show_id)
    if not show:
        abort(404)
    songs = show.get("songs", [])
    return render_template("regie_view.html", show=show, songs=songs)


@show_details_bp.route("/show/<int:show_id>/regie/update_cue", methods=["POST"])
def regie_update_cue(show_id: int):
    show = find_show(show_id)
    if not show:
        abort(404)
    song_id = request.form.get("song_id", type=int)
    name = request.form.get("song_name", "").strip()
    special_notes = request.form.get("song_special_notes", "").strip()
    for song in show.get("songs", []):
        if song.get("id") == song_id:
            song["name"] = name
            song["special_notes"] = special_notes
            break
    save_data()
    return redirect(url_for("show_details.show_regie_view", show_id=show_id))


@show_details_bp.route("/show/<int:show_id>/regie/move_cue", methods=["POST"])
def regie_move_cue(show_id: int):
    show = find_show(show_id)
    if not show:
        abort(404)
    song_id = request.form.get("song_id", type=int)
    direction = request.form.get("direction")
    songs = show.get("songs", [])
    idx = next((i for i, s in enumerate(songs) if s.get("id") == song_id), None)
    if idx is not None:
        if direction == "up" and idx > 0:
            songs[idx], songs[idx-1] = songs[idx-1], songs[idx]
        elif direction == "down" and idx < len(songs)-1:
            songs[idx], songs[idx+1] = songs[idx+1], songs[idx]
        for i, s in enumerate(songs, 1):
            s["order_index"] = i
        save_data()
    return redirect(url_for("show_details.show_regie_view", show_id=show_id))


@show_details_bp.route("/show/<int:show_id>/update_song", methods=["POST"])
def update_song(show_id: int):
    show = find_show(show_id)
    if not show:
        abort(404)
    song_id_raw = request.form.get("song_id", "")
    from_regie = request.form.get("from_regie")
    try:
        song_id = int(song_id_raw)
    except (TypeError, ValueError):
        if from_regie:
            return redirect(url_for("show_details.show_regie_view", show_id=show_id))
        return redirect(url_for("show_details.show_detail", show_id=show_id, tab="songs"))

    for song in show.get("songs", []):
        if song.get("id") == song_id:
            name = request.form.get("song_name", "").strip()
            if name:
                song["name"] = name
            song["mood"] = request.form.get("song_mood", "").strip()
            song["colors"] = request.form.get("song_colors", "").strip()
            song["movement_style"] = request.form.get("song_movement_style", "").strip()
            song["eye_candy"] = request.form.get("song_eye_candy", "").strip()
            song["special_notes"] = request.form.get("song_special_notes", "").strip()
            song["general_notes"] = request.form.get("song_general_notes", "").strip()
            break
    save_data()
    sync_entire_show_to_db(show)
    
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"status": "success", "message": "Song stored successfully"})
        
    if from_regie:
        return redirect(url_for("show_details.show_regie_view", show_id=show_id))
    return redirect(url_for("show_details.show_detail", show_id=show_id, tab="songs"))


@show_details_bp.route("/show/<int:show_id>/move_song", methods=["POST"])
def move_song(show_id: int):
    show = find_show(show_id)
    if not show:
        abort(404)
    song_id_raw = request.form.get("song_id", "")
    direction = request.form.get("direction", "")
    from_regie = request.form.get("from_regie")

    try:
        song_id = int(song_id_raw)
    except (TypeError, ValueError):
        if from_regie:
            return redirect(url_for("show_details.show_regie_view", show_id=show_id))
        return redirect(url_for("show_details.show_detail", show_id=show_id, tab="songs"))

    songs_list = show.get("songs", [])
    index = None
    for i, s in enumerate(songs_list):
        if s.get("id") == song_id:
            index = i
            break
    if index is None:
        if from_regie:
            return redirect(url_for("show_details.show_regie_view", show_id=show_id))
        return redirect(url_for("show_details.show_detail", show_id=show_id, tab="songs"))

    if direction == "up" and index > 0:
        songs_list[index - 1], songs_list[index] = songs_list[index], songs_list[index - 1]
    elif direction == "down" and index < len(songs_list) - 1:
        songs_list[index + 1], songs_list[index] = songs_list[index], songs_list[index + 1]

    for idx, s in enumerate(songs_list, start=1):
        s["order_index"] = idx

    show["songs"] = songs_list
    save_data()
    sync_entire_show_to_db(show)

    if from_regie:
        return redirect(url_for("show_details.show_regie_view", show_id=show_id))
    return redirect(url_for("show_details.show_detail", show_id=show_id, tab="songs"))


@show_details_bp.route("/show/<int:show_id>/delete_all_cues", methods=["POST"])
def delete_all_cues(show_id):
    show = find_show(show_id)
    if not show:
        abort(404)
    show["songs"] = []
    save_data()
    sync_entire_show_to_db(show)
    return redirect(url_for("show_details.show_detail", show_id=show_id, tab="songs"))


@show_details_bp.route("/show/<int:show_id>/delete_song", methods=["POST"])
def delete_song(show_id: int):
    show = find_show(show_id)
    if not show:
        abort(404)
    
    song_id_raw = request.form.get("song_id", "")
    try:
        song_id = int(song_id_raw)
    except (TypeError, ValueError):
        return redirect(url_for("show_details.show_detail", show_id=show_id, tab="songs"))

    songs = show.get("songs", [])
    # Filter out the song with the matching ID
    show["songs"] = [s for s in songs if s.get("id") != song_id]
    
    # Re-index
    for idx, s in enumerate(show["songs"], start=1):
        s["order_index"] = idx
        
    save_data()
    sync_entire_show_to_db(show)
    return redirect(url_for("show_details.show_detail", show_id=show_id, tab="songs"))

# --- Contact Routes ---

@show_details_bp.route("/show/<int:show_id>/contacts/add", methods=["POST"])
def add_contact(show_id: int):
    show = find_show(show_id)
    if not show:
        abort(404)
    try:
        contact = ContactPersonModel(
            show_id=show_id,
            role=request.form.get("role", "").strip() or "",
            name=request.form.get("name", "").strip() or None,
            company=request.form.get("company", "").strip() or None,
            phone=request.form.get("phone", "").strip() or None,
            email=request.form.get("email", "").strip() or None,
            notes=request.form.get("notes", "").strip() or None,
        )
        db.session.add(contact)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[DB] Fehler beim Anlegen des Kontakts: {e}")
    return redirect(url_for("show_details.show_detail", show_id=show_id, tab="contacts"))

@show_details_bp.route("/show/<int:show_id>/contacts/<int:contact_id>/update", methods=["POST"])
def update_contact(show_id: int, contact_id: int):
    contact = db.session.get(ContactPersonModel, contact_id)
    if not contact or contact.show_id != show_id:
        abort(404)
    contact.role = request.form.get("role", "").strip() or contact.role
    contact.name = request.form.get("name", "").strip() or contact.name
    contact.company = request.form.get("company", "").strip() or contact.company
    contact.phone = request.form.get("phone", "").strip() or contact.phone
    contact.email = request.form.get("email", "").strip() or contact.email
    contact.notes = request.form.get("notes", "").strip() or contact.notes
    try:
        db.session.add(contact)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[DB] Fehler beim Aktualisieren des Kontakts: {e}")
        
    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return jsonify({"status": "success", "message": "Contact updated"})
        
    return redirect(url_for("show_details.show_detail", show_id=show_id, tab="contacts"))

@show_details_bp.route("/show/<int:show_id>/contacts/<int:contact_id>/delete", methods=["POST"])
def delete_contact(show_id: int, contact_id: int):
    contact = db.session.get(ContactPersonModel, contact_id)
    if not contact or contact.show_id != show_id:
        abort(404)
    try:
        db.session.delete(contact)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"[DB] Fehler beim Löschen des Kontakts: {e}")
    return redirect(url_for("show_details.show_detail", show_id=show_id, tab="contacts"))


@show_details_bp.route("/show/<int:show_id>/delete", methods=["POST"])
def delete_show(show_id: int):
    show = find_show(show_id)
    if not show:
        abort(404)
    
    # Remove from JSON memory and save
    remove_show(show_id)
    save_data()
    
    # Remove from DB
    try:
        db_show = db.session.get(ShowModel, show_id)
        if db_show:
            db.session.delete(db_show)
            db.session.commit()
    except Exception as e:
        print(f"Error deleting show from DB: {e}")
    return redirect(url_for("main.dashboard"))


@show_details_bp.route("/show/<int:show_id>/api/get_rig", methods=["GET"])
def api_get_rig(show_id: int):
    show = find_show(show_id)
    if not show:
        return jsonify({"error": "Show not found"}), 404
        
    rig = show.get("rig_setup", {}) or {}
    
    # Flatten items for the frontend
    items = []
    
    # Helper to add items
    def add_items(prefix):
        raw_items = rig.get(f"{prefix}_items", [])
        for it in raw_items:
            # Check if this item group has saved positions
            # For simplicity in V1, we might need to store positions IN the item dict.
            # But the item dict in JSON is a list of dicts. 
            # We need to ensure we can map them back.
            # Ideally, we used a unique ID per fixture, but we generated them on the fly in MVR export.
            # Here we might need to stick to the list index or add IDs if missing.
            
            count = 0
            try: count = int(it.get("count", 0))
            except: pass
            
            # Position data might be stored in a separate list or inside the item?
            # Let's say we store 'positions_data': { 'spots_items_0_0': {x:100, y:100}, ... }
            # Or we enrich the items directly in the backend if we saved them there.
            pass
            
    # Actually, let's keep it simple:
    # We return the whole rig object. The frontend can parse count/watt etc.
    # But for positions: where do we store them?
    # Let's verify where 'update_rig' saves data. It saves to 'rig_setup'.
    # We can add a 'visual_plan' dict to rig_setup where keys are stable IDs.
    
    visual_plan = rig.get("visual_plan", {})
    return jsonify({
        "rig": rig,
        "visual_plan": visual_plan
    })


@show_details_bp.route("/show/<int:show_id>/api/save_rig_positions", methods=["POST"])
def api_save_rig_positions(show_id: int):
    show = find_show(show_id)
    if not show:
        return jsonify({"error": "Show not found"}), 404
        
    data = request.json
    if not data:
        return jsonify({"error": "No data"}), 400
        
    rig = show.get("rig_setup", {})
    # Save the visual plan (x, y, rotation for each fixture 'key')
    rig["visual_plan"] = data.get("visual_plan", {})
    
    save_data()
    sync_entire_show_to_db(show)
    
    return jsonify({"success": True})

