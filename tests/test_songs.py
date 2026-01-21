import show_logic

def test_add_song(client, sample_show):
    """Test adding a song to a show."""
    client.post('/login', data=dict(username="Admin", password="Admin123"))
    
    show_id = sample_show["id"]
    
    response = client.post(f'/show/{show_id}/add_song', data=dict(
        song_name="Test Song",
        song_mood="Energetic",
        song_colors="Red, Blue",
        song_movement_style="Fast",
        song_eye_candy="Strobes",
        song_special_notes="Go hard",
        song_general_notes="General note"
    ), follow_redirects=True)
    
    assert response.status_code == 200
    assert len(sample_show["songs"]) == 1
    assert sample_show["songs"][0]["name"] == "Test Song"

def test_add_multiple_songs(client, sample_show):
    """Test adding multiple songs."""
    client.post('/login', data=dict(username="Admin", password="Admin123"))
    
    show_id = sample_show["id"]
    
    for i in range(3):
        client.post(f'/show/{show_id}/add_song', data=dict(
            song_name=f"Song {i+1}",
            song_mood="",
            song_colors="",
            song_movement_style="",
            song_eye_candy="",
            song_special_notes="",
            song_general_notes=""
        ), follow_redirects=True)
    
    assert len(sample_show["songs"]) == 3
    assert sample_show["songs"][0]["order_index"] == 1
    assert sample_show["songs"][2]["order_index"] == 3

def test_delete_song(client, sample_show):
    """Test deleting a song."""
    client.post('/login', data=dict(username="Admin", password="Admin123"))
    
    show_id = sample_show["id"]
    
    # Add a song first
    show_logic.create_song(sample_show, "To Delete", "", "", "", "", "", "")
    assert len(sample_show["songs"]) == 1
    song_id = sample_show["songs"][0]["id"]
    
    # Delete it
    response = client.post(f'/show/{show_id}/delete_song', data=dict(
        song_id=song_id
    ), follow_redirects=True)
    
    assert response.status_code == 200
    assert len(sample_show["songs"]) == 0

def test_move_song(client, sample_show):
    """Test reordering songs."""
    client.post('/login', data=dict(username="Admin", password="Admin123"))
    
    show_id = sample_show["id"]
    
    # Add two songs
    show_logic.create_song(sample_show, "Song A", "", "", "", "", "", "")
    show_logic.create_song(sample_show, "Song B", "", "", "", "", "", "")
    
    assert sample_show["songs"][0]["name"] == "Song A"
    song_b_id = sample_show["songs"][1]["id"]
    
    # Move Song B up
    response = client.post(f'/show/{show_id}/move_song', data=dict(
        song_id=song_b_id,
        direction="up"
    ), follow_redirects=True)
    
    assert response.status_code == 200
    assert sample_show["songs"][0]["name"] == "Song B"
    assert sample_show["songs"][1]["name"] == "Song A"
