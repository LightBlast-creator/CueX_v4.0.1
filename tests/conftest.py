import pytest
import os
import tempfile
import json
from app import app
from show_logic import shows, save_data, DATA_FILE, next_show_id
import show_logic

@pytest.fixture
def client():
    """Configures the app for testing and returns a test client."""
    db_fd, db_path = tempfile.mkstemp()
    
    # Configure app for testing
    app.config['TESTING'] = True
    app.config['WTF_CSRF_ENABLED'] = False  # Disable CSRF for easier testing
    
    # Mock the data file path in show_logic to use a temp file
    # We can't easily change the global constant, but we can patch the load/save logic
    # or just use a temporary file name if we could mock the module constant.
    # Since constants are hard to mock, we will backup the current shows and restore them.
    
    # Backup existing data
    original_shows = list(show_logic.shows)
    original_data_file = show_logic.DATA_FILE
    
    # Use a temp file for tests
    show_logic.DATA_FILE = db_path
    show_logic.shows = [] # Start empty
    show_logic.next_show_id = 1
    
    with app.test_client() as client:
        yield client

    # Cleanup: Restore original data
    show_logic.shows = original_shows
    show_logic.DATA_FILE = original_data_file
    
    os.close(db_fd)
    os.remove(db_path)

@pytest.fixture
def sample_show():
    """Creates a sample show in the test database."""
    show = show_logic.create_default_show("Test Show", "Tester", "2025-01-01", "", "", "")
    show_logic.shows.append(show)
    return show
