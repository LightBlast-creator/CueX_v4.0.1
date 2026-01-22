from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app, jsonify
import show_logic
import gdtf_api
import os

main_bp = Blueprint('main', __name__)

# GDTF API Endpoint: Fixtures für Hersteller (für Autocomplete)
@main_bp.route('/api/gdtf/fixtures/<manufacturer>')
def api_gdtf_fixtures(manufacturer):
    """
    Gibt alle Modelle eines Herstellers aus GDTF Share zurück.
    Wird vom Frontend für Autocomplete genutzt.
    """
    if 'user' not in session:
        return jsonify({'error': 'Nicht eingeloggt', 'models': []}), 401
    
    gdtf_user = session.get('gdtf_user', '')
    gdtf_password = session.get('gdtf_password', '')
    
    if not gdtf_user or not gdtf_password:
        return jsonify({
            'error': 'GDTF Login fehlt. Bitte unter Einstellungen hinterlegen.',
            'models': []
        }), 400
    
    try:
        fixtures = gdtf_api.get_fixtures_by_manufacturer(gdtf_user, gdtf_password, manufacturer)
        # Nur Namen für Autocomplete
        models = list(set(f.get('fixture', '') for f in fixtures if f.get('fixture')))
        models.sort()
        return jsonify({
            'manufacturer': manufacturer,
            'models': models,
            'fixtures': fixtures,  # Vollständige Daten inkl. Modes
            'count': len(models)
        })
    except Exception as e:
        return jsonify({'error': str(e), 'models': []}), 500


# GDTF API Endpoint: Modes für ein spezifisches Fixture
@main_bp.route('/api/gdtf/modes/<manufacturer>/<fixture_name>')
def api_gdtf_modes(manufacturer, fixture_name):
    """
    Gibt alle Modes eines spezifischen Fixtures zurück (mit DMX-Footprint).
    """
    if 'user' not in session:
        return jsonify({'error': 'Nicht eingeloggt', 'modes': []}), 401
    
    gdtf_user = session.get('gdtf_user', '')
    gdtf_password = session.get('gdtf_password', '')
    
    if not gdtf_user or not gdtf_password:
        return jsonify({'error': 'GDTF Login fehlt', 'modes': []}), 400
    
    try:
        modes = gdtf_api.get_modes_for_fixture(gdtf_user, gdtf_password, manufacturer, fixture_name)
        return jsonify({
            'manufacturer': manufacturer,
            'fixture': fixture_name,
            'modes': modes
        })
    except Exception as e:
        return jsonify({'error': str(e), 'modes': []}), 500


# GDTF Fixture Search Page (erweitert)
@main_bp.route('/gdtf_fixture_search')
def gdtf_fixture_search():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    
    gdtf_user = session.get('gdtf_user', '')
    gdtf_password = session.get('gdtf_password', '')
    
    if not gdtf_user or not gdtf_password:
        flash('Bitte zuerst GDTF Login-Daten in den Einstellungen hinterlegen.', 'warning')
        return redirect(url_for('main.settings'))
    
    # Alle Hersteller aus GDTF laden (nutzt Cache)
    try:
        manufacturers = gdtf_api.get_manufacturers(gdtf_user, gdtf_password)
        return render_template('gdtf_search.html', manufacturers=manufacturers)
    except Exception as e:
        flash(f'Fehler beim Laden der GDTF-Hersteller: {str(e)}', 'danger')
        return redirect(url_for('main.settings'))

# GDTF-Einstellungen-Route
@main_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    saved = False
    gdtf_error = None
    if request.method == 'POST':
        gdtf_user = request.form.get('gdtf_user', '').strip()
        gdtf_password = request.form.get('gdtf_password', '').strip()
        session['gdtf_user'] = gdtf_user
        session['gdtf_password'] = gdtf_password
        autosave_interval = request.form.get('autosave_interval', '0')
        session['autosave_interval'] = autosave_interval
        gdtf_api.clear_cache()  # Cache leeren bei neuen Credentials
        saved = True
    gdtf_user = session.get('gdtf_user', '')
    gdtf_password = session.get('gdtf_password', '')
    autosave_interval = session.get('autosave_interval', '0')
    return render_template('settings.html', 
                           gdtf_user=gdtf_user, 
                           gdtf_password=gdtf_password,
                           autosave_interval=autosave_interval, 
                           saved=saved,
                           gdtf_error=gdtf_error)

# Helper: Lampen zählen
def calculate_total_lamps(rig):
    if not rig:
        return 0
    total = 0
    
    # Helper to safe-int
    def safe_int(val):
        try:
            return int(val)
        except (ValueError, TypeError):
            return 0

    # 1. Spots
    if rig.get('spots_items'):
        for it in rig['spots_items']:
            total += safe_int(it.get('count'))
    else:
        total += safe_int(rig.get('spots'))

    # 2. Washes
    if rig.get('washes_items'):
        for it in rig['washes_items']:
            total += safe_int(it.get('count'))
    else:
        total += safe_int(rig.get('washes'))

    # 3. Beams
    if rig.get('beams_items'):
        for it in rig['beams_items']:
            total += safe_int(it.get('count'))
    else:
        total += safe_int(rig.get('beams'))

    # 4. Blinders
    if rig.get('blinders_items'):
        for it in rig['blinders_items']:
            total += safe_int(it.get('count'))
    else:
        # Blinder legacy input was named rig_blinders__count[] originally too? 
        # Check show_logic: "blinders": "" defaults to string.
        total += safe_int(rig.get('blinders'))

    # 5. Strobes
    if rig.get('strobes_items'):
        for it in rig['strobes_items']:
            total += safe_int(it.get('count'))
    else:
        total += safe_int(rig.get('strobes'))

    # 6. Custom Devices
    if rig.get('custom_devices'):
        for it in rig['custom_devices']:
            total += safe_int(it.get('count'))

    return total

# Dashboard: Show creation form + show list
@main_bp.route('/', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    if request.method == 'POST':
        # Neue Show anlegen
        name = request.form.get('name', '').strip()
        artist = request.form.get('artist', '').strip()
        date = request.form.get('date', '').strip()
        venue_type = request.form.get('venue_type', '').strip()
        genre = request.form.get('genre', '').strip()
        rig_type = request.form.get('rig_type', '').strip()
        
        # Module aus Checkboxen (Liste von Werten)
        modules_list = request.form.getlist('modules')
        modules_str = ','.join(modules_list) if modules_list else 'stammdaten'
        
        if name:
            new_show = show_logic.create_default_show(
                name=name,
                artist=artist,
                date=date,
                venue_type=venue_type,
                genre=genre,
                rig_type=rig_type,
                modules=modules_str
            )
            show_logic.shows.append(new_show)
            show_logic.save_data()
            show_logic.sync_entire_show_to_db(new_show)
        return redirect(url_for('main.dashboard'))
    
    # Statistiken berechnen
    total_lamps = 0
    total_songs = 0
    for show in show_logic.shows:
        rig = show.get('rig_setup', {})
        total_lamps += calculate_total_lamps(rig)
        songs = show.get('songs') or []
        total_songs += len(songs)

    return render_template('index.html', shows=show_logic.shows, total_lamps=total_lamps, total_songs=total_songs)

# Optional: /show_overview leitet auf / weiter (altes Routing)
@main_bp.route('/show_overview')
def show_overview():
    return redirect(url_for('main.dashboard'))

# Login-Route
@main_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        # Zugangsdaten: Admin / Admin123
        if username == 'Admin' and password == 'Admin123':
            session['user'] = username
            flash('Login erfolgreich!', 'success')
            return redirect(url_for('main.show_overview'))
        else:
            flash('Login fehlgeschlagen. Bitte überprüfe Benutzername und Passwort.', 'danger')
    return render_template('login.html')

# Logout-Route
@main_bp.route('/logout')
def logout():
    session.pop('user', None)
    flash('Du wurdest ausgeloggt.', 'info')
    return redirect(url_for('main.login'))
