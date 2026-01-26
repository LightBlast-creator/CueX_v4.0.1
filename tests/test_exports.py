import pytest
from app import app
from models import db, Show as ShowModel
from show_logic import sync_entire_show_to_db

def test_export_asc(client, sample_show):
    """Test USITT ASCII export route returns a valid file."""
    # Login
    client.post('/login', data=dict(username="Admin", password="Admin123"))
    
    # Init DB Sync
    with app.app_context():
        # Add a dummy song so we have Cues
        sample_show["songs"] = [{
            "id": 999, 
            "order_index": 1, 
            "name": "Test Cue", 
            "mood": "", "colors": "", "special_notes": "", "general_notes": ""
        }]
        sync_entire_show_to_db(sample_show)
        
    response = client.get(f'/show/{sample_show["id"]}/export_asc')
    assert response.status_code == 200
    assert b"Ident 3:0" in response.data
    assert b"CUE" in response.data

def test_export_ma3(client, sample_show):
    """Test MA3 export route returns a ZIP file."""
    client.post('/login', data=dict(username="Admin", password="Admin123"))
    
    with app.app_context():
        sync_entire_show_to_db(sample_show)

    response = client.get(f'/show/{sample_show["id"]}/export_ma3')
    assert response.status_code == 200
    assert response.content_type == "application/zip"
    # Zip header check (PK..)
    assert response.data[:2] == b'PK'

def test_export_sync_fallback(client, sample_show):
    """
    CRITICAL TEST: Verify that export succeeds even if the show is missing 
    from the SQLite DB (but exists in JSON), triggering the auto-repair.
    """
    client.post('/login', data=dict(username="Admin", password="Admin123"))
    
    # 1. Ensure clean state: Show is in JSON (sample_show fixture does this) 
    # and we forcefully sync it to DB first to have an ID to delete.
    with app.app_context():
        sync_entire_show_to_db(sample_show)
        show_id = sample_show["id"]
        
        # 2. SABOTAGE: Manually delete the show from the SQLite DB!
        db_show = db.session.get(ShowModel, show_id)
        assert db_show is not None, "Setup failed: Show should be in DB"
        
        db.session.delete(db_show)
        db.session.commit()
        
        # Verify it's gone from DB
        assert db.session.get(ShowModel, show_id) is None, "Sabotage failed: Show still in DB"
        
    # 3. Trigger Export (this would previously 404)
    # The route should detect missing DB entry -> load from JSON -> Sync -> Export
    response = client.get(f'/show/{sample_show["id"]}/export_ma3')
    
    # 4. Assert Success
    assert response.status_code == 200
    assert response.content_type == "application/zip"
    
    # 5. Verify it was restored to DB
    with app.app_context():
        restored_show = db.session.get(ShowModel, sample_show["id"])
        assert restored_show is not None, "Auto-repair failed: Show was not restored to DB"
