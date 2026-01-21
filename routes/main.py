from flask import Blueprint, render_template, request, redirect, url_for, session, flash, current_app
import show_logic
import os

main_bp = Blueprint('main', __name__)

# GDTF Fixture Search Dummy-Route (früh registrieren)
@main_bp.route('/gdtf_fixture_search')
def gdtf_fixture_search():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    return '<h2>GDTF Fixture Suche (Demo)</h2><p>Hier kommt die API-Suche hin.</p>'

# GDTF-Token Einstellungen-Route (früh registrieren)
@main_bp.route('/settings', methods=['GET', 'POST'])
def settings():
    if 'user' not in session:
        return redirect(url_for('main.login'))
    saved = False
    if request.method == 'POST':
        token = request.form.get('gdtf_token', '').strip()
        session['gdtf_token'] = token
        autosave_interval = request.form.get('autosave_interval', '0')
        session['autosave_interval'] = autosave_interval
        saved = True
    gdtf_token = session.get('gdtf_token', '')
    autosave_interval = session.get('autosave_interval', '0')
    return render_template('settings.html', gdtf_token=gdtf_token, autosave_interval=autosave_interval, saved=saved)

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
        
        if name:
            new_show = show_logic.create_default_show(
                name=name,
                artist=artist,
                date=date,
                venue_type=venue_type,
                genre=genre,
                rig_type=rig_type
            )
            show_logic.shows.append(new_show)
            show_logic.save_data()
            show_logic.sync_entire_show_to_db(new_show)
        return redirect(url_for('main.dashboard'))
    return render_template('index.html', shows=show_logic.shows)

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
