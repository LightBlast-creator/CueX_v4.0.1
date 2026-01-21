from flask import Blueprint, request, redirect, url_for, abort, current_app
from pathlib import Path
import werkzeug
import uuid
from show_logic import find_show, save_data

show_assets_bp = Blueprint('show_assets', __name__)

@show_assets_bp.route("/show/<int:show_id>/upload_prop_image", methods=["POST"])
def upload_prop_image(show_id: int):
    show = find_show(show_id)
    if not show:
        abort(404)
    song_id = request.form.get("song_id", type=int)
    file = request.files.get("prop_image")
    if file and file.filename:
        ext = werkzeug.utils.secure_filename(file.filename).rsplit(".", 1)[-1].lower()
        fname = f"{show_id}_{uuid.uuid4().hex[:8]}.{ext}"
        save_path = Path(current_app.root_path) / "static" / "props" / fname
        file.save(str(save_path))
        
        if song_id:
            for song in show.get("songs", []):
                if song.get("id") == song_id:
                    song.setdefault("prop_images", []).append(fname)
                    break
        else:
            show.setdefault("prop_images", []).append(fname)
        
        save_data()
    return redirect(url_for("show_details.show_detail", show_id=show_id, tab="props"))


@show_assets_bp.route("/show/<int:show_id>/delete_prop_image/<filename>", methods=["POST"])
def delete_prop_image(show_id: int, filename: str):
    show = find_show(show_id)
    if not show:
        abort(404)
    song_id = request.form.get("song_id", type=int)
    found = False
    
    if song_id:
        for song in show.get("songs", []):
            if song.get("id") == song_id and "prop_images" in song and filename in song["prop_images"]:
                song["prop_images"].remove(filename)
                found = True
                break
    
    if not found and "prop_images" in show and filename in show["prop_images"]:
        show["prop_images"].remove(filename)
        found = True
        
    if found:
        save_data()
        try:
            (Path(current_app.root_path) / "static" / "props" / filename).unlink(missing_ok=True)
        except Exception:
            pass
            
    return redirect(url_for("show_details.show_detail", show_id=show_id, tab="props", song_id=song_id if song_id else None))


@show_assets_bp.route("/show/<int:show_id>/upload_video", methods=["POST"])
def upload_video(show_id: int):
    show = find_show(show_id)
    if not show:
        abort(404)
    if "videos" not in show:
        show["videos"] = []
    file = request.files.get("video")
    if file and file.filename:
        ext = werkzeug.utils.secure_filename(file.filename).rsplit(".", 1)[-1].lower()
        fname = f"{show_id}_{uuid.uuid4().hex[:8]}.{ext}"
        save_path = Path(current_app.root_path) / "static" / "videos" / fname
        file.save(str(save_path))
        show["videos"].append(fname)
        save_data()
    return redirect(url_for("show_details.show_detail", show_id=show_id, tab="videos"))


@show_assets_bp.route("/show/<int:show_id>/delete_video/<filename>", methods=["POST"])
def delete_video(show_id: int, filename: str):
    show = find_show(show_id)
    if not show:
        abort(404)
    if "videos" in show and filename in show["videos"]:
        show["videos"].remove(filename)
        save_data()
        try:
            (Path(current_app.root_path) / "static" / "videos" / filename).unlink(missing_ok=True)
        except Exception:
            pass
    return redirect(url_for("show_details.show_detail", show_id=show_id, tab="videos"))
