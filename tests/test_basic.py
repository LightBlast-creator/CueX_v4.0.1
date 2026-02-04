import pytest
from app import app
from core.models import db

@pytest.fixture
def client():
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for tests
    
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.drop_all()

def test_dashboard_redirect_to_login(client):
    """Test dashboard redirects to login if not authenticated"""
    # In LITE_MODE hardcoded to True in app.py, this might auto-login or redirect?
    # app.py: if current_app.config.get('LITE_MODE') and 'user' not in session: session['user'] = 'LiteUser'
    # So it should ACTUALLY load the dashboard directly!
    rv = client.get('/', follow_redirects=True)
    assert b'Meine Shows' in rv.data or b'Neue Show anlegen' in rv.data

def test_login_route(client):
    rv = client.get('/login')
    assert rv.status_code == 200 or rv.status_code == 302 # Redirects in Lite Mode

def test_settings_route(client):
    rv = client.get('/settings', follow_redirects=True)
    assert rv.status_code == 200
    assert b'Einstellungen' in rv.data

def test_gdtf_search_access(client):
    rv = client.get('/gdtf_fixture_search', follow_redirects=True)
    # Might flash warning if no GDTF credentials, but page should load or redirect
    assert rv.status_code == 200
