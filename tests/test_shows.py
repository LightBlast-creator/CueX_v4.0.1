import show_logic

def test_create_show(client):
    """Test creating a new show via the dashboard form."""
    # Login first
    client.post('/login', data=dict(username="Admin", password="Admin123"))
    
    # Create a show
    response = client.post('/', data=dict(
        name="Pytest Show",
        artist="Pytest Artist",
        date="2025-12-31",
        venue_type="Arena",
        genre="Rock",
        rig_type="Full"
    ), follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Pytest Show" in response.data
    assert len(show_logic.shows) == 1
    assert show_logic.shows[0]["name"] == "Pytest Show"

def test_show_has_songs_list(client):
    """Test that a newly created show has an empty songs list."""
    client.post('/login', data=dict(username="Admin", password="Admin123"))
    
    client.post('/', data=dict(
        name="Show With Songs",
        artist="",
        date="",
        venue_type="",
        genre="",
        rig_type=""
    ), follow_redirects=True)
    
    assert len(show_logic.shows) == 1
    assert "songs" in show_logic.shows[0]
    assert isinstance(show_logic.shows[0]["songs"], list)

def test_delete_show(client, sample_show):
    """Test deleting a show."""
    client.post('/login', data=dict(username="Admin", password="Admin123"))
    
    show_id = sample_show["id"]
    assert len(show_logic.shows) == 1
    
    response = client.post(f'/show/{show_id}/delete', follow_redirects=True)
    
    assert response.status_code == 200
    assert len(show_logic.shows) == 0

def test_show_detail_loads(client, sample_show):
    """Test that a show detail page loads correctly."""
    client.post('/login', data=dict(username="Admin", password="Admin123"))
    
    response = client.get(f'/show/{sample_show["id"]}')
    
    assert response.status_code == 200
    assert b"Test Show" in response.data
