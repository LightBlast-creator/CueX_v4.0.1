def test_home_page(client):
    """Test that the home page loads (redirects to login)."""
    response = client.get('/', follow_redirects=True)
    assert response.status_code == 200
    assert b"Login" in response.data

def test_login_successful(client):
    """Test logging in with correct credentials."""
    response = client.post('/login', data=dict(
        username="Admin",
        password="Admin123"
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b"Dashboard" in response.data

def test_login_invalid(client):
    """Test logging in with incorrect credentials."""
    response = client.post('/login', data=dict(
        username="Wrong",
        password="User"
    ), follow_redirects=True)
    assert response.status_code == 200
    assert b"Login fehlgeschlagen" in response.data
