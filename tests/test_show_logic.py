import pytest
from unittest.mock import patch, MagicMock
from core import show_logic

@pytest.fixture
def mock_persistence():
    with patch("core.show_logic.save_data") as mock_save, \
         patch("core.show_logic.sync_entire_show_to_db") as mock_sync:
        yield mock_save, mock_sync

@pytest.fixture
def clean_state():
    # Save original state
    original_shows = list(show_logic.shows)
    original_id = show_logic.next_show_id
    original_song_id = show_logic.next_song_id
    
    # Reset state
    show_logic.shows.clear()
    show_logic.next_show_id = 1
    show_logic.next_song_id = 1
    
    yield
    
    # Restore
    show_logic.shows[:] = original_shows
    show_logic.next_show_id = original_id
    show_logic.next_song_id = original_song_id

def test_create_default_show(mock_persistence, clean_state):
    show = show_logic.create_default_show(
        name="Test Show",
        artist="Test Artist",
        date="2025-01-01",
        venue_type="Club",
        genre="Rock",
        rig_type="Touring"
    )
    
    # It must NOT add to the list automatically, caller does that usually? 
    # Checking create_default_show implementation: it creates dict, increments ID. 
    # It does NOT append to 'shows' list? 
    # Wait, create_default_show implementation returns 'show' dict but doesn't append to logic.shows?
    # Actually looking at show_logic.py source:
    # It just returns 'show'. 
    # But duplicate_show DOES append.
    # The caller (route) typically appends or show_logic SHOULD append? 
    # Let's check routes usually. But here we test the function.
    
    assert show["name"] == "Test Show"
    assert show["id"] == 1
    assert show["artist"] == "Test Artist"
    assert show["songs"] == []

def test_create_song(mock_persistence, clean_state):
    # Setup a show
    show = show_logic.create_default_show("S1", "", "", "", "", "")
    show_logic.shows.append(show)
    
    song = show_logic.create_song(
        show=show, 
        name="Song 1", 
        mood="Happy", 
        colors="Red", 
        movement_style="Fast", 
        eye_candy="None", 
        special_notes="Note", 
        general_notes="Gen"
    )
    
    assert len(show["songs"]) == 1
    assert song["id"] == 1
    assert song["name"] == "Song 1"
    assert song["order_index"] == 1

    # Add second song
    song2 = show_logic.create_song(show, "Song 2", "", "", "", "", "", "")
    assert len(show["songs"]) == 2
    assert song2["id"] == 2
    assert song2["order_index"] == 2

def test_remove_song_reorders_indices(mock_persistence, clean_state):
    show = show_logic.create_default_show("S1", "", "", "", "", "")
    s1 = show_logic.create_song(show, "S1", "", "", "", "", "", "")
    s2 = show_logic.create_song(show, "S2", "", "", "", "", "", "")
    s3 = show_logic.create_song(show, "S3", "", "", "", "", "", "")
    
    assert show["songs"][0]["order_index"] == 1
    assert show["songs"][1]["order_index"] == 2
    assert show["songs"][2]["order_index"] == 3
    
    # Remove middle song (id=2)
    show_logic.remove_song_from_show(show, 2)
    
    assert len(show["songs"]) == 2
    assert show["songs"][0]["id"] == 1
    assert show["songs"][0]["order_index"] == 1
    
    assert show["songs"][1]["id"] == 3
    assert show["songs"][1]["order_index"] == 2  # Should be re-indexed

def test_duplicate_show(mock_persistence, clean_state):
    show = show_logic.create_default_show("Original", "Artist", "2025-01-01", "", "", "")
    show_logic.shows.append(show)
    show_logic.create_song(show, "Song 1", "", "", "", "", "", "")
    
    # Duplicate
    new_show = show_logic.duplicate_show(show["id"])
    
    assert new_show is not None
    assert new_show["id"] != show["id"]
    assert "Original (Kopie)" in new_show["name"]
    assert new_show["date"] == ""  # Date should be empty
    assert len(new_show["songs"]) == 1
    assert new_show["songs"][0]["name"] == "Song 1"
    # Verify IDs are new
    assert new_show["songs"][0]["id"] != show["songs"][0]["id"]
    
    # Persistence should be called
    mock_save, mock_sync = mock_persistence
    mock_save.assert_called()
    mock_sync.assert_called()
