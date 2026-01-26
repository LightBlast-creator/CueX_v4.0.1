"""
GDTF Share API Client
Kommuniziert mit der GDTF Share API für Fixture-Daten.

API-Dokumentation: https://github.com/mvrdevelopment/tools/blob/main/GDTF_Share_API/GDTF%20Share%20API.md
"""

import requests
from typing import List, Dict, Optional
import time

# Cache-Dauer in Sekunden (1 Stunde)
CACHE_DURATION = 3600

# GDTF Share API Base URL
GDTF_API_BASE = "https://gdtf-share.com/apis/public"

# Globaler Cache für Fixture-Liste
_fixtures_cache: Dict = {
    "data": None,
    "timestamp": 0,
    "session": None
}


def _login(username: str, password: str) -> Optional[requests.Session]:
    """
    Login bei GDTF Share mit Username und Password.
    
    Args:
        username: GDTF Share Username
        password: GDTF Share Password
        
    Returns:
        Session-Objekt bei Erfolg, None bei Fehler
    """
    session = requests.Session()
    
    try:
        response = session.post(
            f"{GDTF_API_BASE}/login.php",
            json={"user": username, "password": password},
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("result") == True:
                print(f"[GDTF] Login erfolgreich: {data.get('notice', '')}")
                return session
        
        print(f"[GDTF] Login fehlgeschlagen: {response.status_code}")
        return None
        
    except Exception as e:
        print(f"[GDTF] Login-Fehler: {e}")
        return None


def _get_all_fixtures(username: str, password: str) -> List[Dict]:
    """
    Holt alle Fixtures von GDTF Share.
    Nutzt Cache um API-Aufrufe zu minimieren.
    
    Args:
        username: GDTF Share Username
        password: GDTF Share Password
        
    Returns:
        Liste aller Fixtures mit Manufacturer, Fixture, Modes, etc.
    """
    global _fixtures_cache
    
    now = time.time()
    
    # Cache prüfen (1 Stunde gültig)
    if _fixtures_cache["data"] and (now - _fixtures_cache["timestamp"]) < CACHE_DURATION:
        return _fixtures_cache["data"]
    
    # Login
    session = _login(username, password)
    if not session:
        return []
    
    try:
        response = session.get(
            f"{GDTF_API_BASE}/getList.php",
            timeout=60
        )
        
        if response.status_code == 401:
            print("[GDTF] Nicht autorisiert - Session ungültig")
            return []
        
        if response.status_code != 200:
            print(f"[GDTF] API-Fehler: {response.status_code}")
            return []
        
        data = response.json()
        
        if not data.get("result"):
            print(f"[GDTF] API-Fehler: {data.get('error', 'Unbekannt')}")
            return []
        
        fixtures = data.get("list", [])
        
        # Cache aktualisieren
        _fixtures_cache["data"] = fixtures
        _fixtures_cache["timestamp"] = now
        _fixtures_cache["session"] = session
        
        print(f"[GDTF] {len(fixtures)} Fixtures geladen")
        return fixtures
        
    except requests.RequestException as e:
        print(f"[GDTF] Verbindungsfehler: {e}")
        return []
    except Exception as e:
        print(f"[GDTF] Fehler: {e}")
        return []


def get_manufacturers(username: str, password: str) -> List[str]:
    """
    Gibt alle verfügbaren Hersteller zurück.
    
    Args:
        username: GDTF Share Username
        password: GDTF Share Password
        
    Returns:
        Sortierte Liste der Hersteller-Namen
    """
    fixtures = _get_all_fixtures(username, password)
    manufacturers = set()
    
    for fixture in fixtures:
        manufacturer = fixture.get("manufacturer")
        if manufacturer:
            manufacturers.add(manufacturer)
    
    return sorted(manufacturers)


def get_fixtures_by_manufacturer(username: str, password: str, manufacturer: str) -> List[Dict]:
    """
    Gibt alle Fixtures eines bestimmten Herstellers zurück.
    
    Args:
        username: GDTF Share Username
        password: GDTF Share Password
        manufacturer: Name des Herstellers
        
    Returns:
        Liste der Fixtures mit Name, Modes, DMX-Footprint, etc.
    """
    fixtures = _get_all_fixtures(username, password)
    result = []
    
    manufacturer_lower = manufacturer.lower()
    
    for fixture in fixtures:
        fix_manufacturer = fixture.get("manufacturer", "")
        fix_manufacturer_lower = fix_manufacturer.lower()
        
        # Partielles Matching: "Astera" findet auch "Astera LED Technology"
        # oder "JB-Lighting" findet auch "JB Lighting GmbH"
        matches = (
            fix_manufacturer_lower == manufacturer_lower or  # Exakter Match
            manufacturer_lower in fix_manufacturer_lower or   # Hersteller enthält Suchbegriff
            fix_manufacturer_lower.startswith(manufacturer_lower.replace("-", " ").replace("-", ""))  # Start-Match
        )
        
        if matches:
            # Modes extrahieren
            modes_raw = fixture.get("modes", [])
            modes = []
            for mode_entry in modes_raw:
                if isinstance(mode_entry, dict):
                    for key, mode_data in mode_entry.items():
                        if isinstance(mode_data, dict):
                            modes.append({
                                "name": mode_data.get("name", ""),
                                "dmx_footprint": mode_data.get("dmxfootprint", 0)
                            })
                        elif isinstance(mode_data, list) and len(mode_data) >= 2:
                            modes.append({
                                "name": mode_data[0] if isinstance(mode_data[0], str) else mode_data[0].get("name", ""),
                                "dmx_footprint": mode_data[1] if isinstance(mode_data[1], int) else 0
                            })
            
            result.append({
                "fixture": fixture.get("fixture", ""),
                "manufacturer": fix_manufacturer,
                "revision": fixture.get("revision", ""),
                "rid": fixture.get("rid", 0),
                "modes": modes,
                "rating": fixture.get("rating", 0),
                "uploader": fixture.get("uploader", "")
            })
    
    # Nach Fixture-Name sortieren
    result.sort(key=lambda x: x["fixture"].lower())
    return result


def get_model_names_by_manufacturer(username: str, password: str, manufacturer: str) -> List[str]:
    """
    Gibt nur die Modell-Namen für einen Hersteller zurück (für Autocomplete).
    
    Args:
        username: GDTF Share Username
        password: GDTF Share Password
        manufacturer: Name des Herstellers
        
    Returns:
        Sortierte Liste der Fixture-Namen (ohne Duplikate)
    """
    fixtures = get_fixtures_by_manufacturer(username, password, manufacturer)
    
    # Einzigartige Namen sammeln
    names = set()
    for fixture in fixtures:
        name = fixture.get("fixture", "")
        if name:
            names.add(name)
    
    return sorted(names)


def get_modes_for_fixture(username: str, password: str, manufacturer: str, fixture_name: str) -> List[Dict]:
    """
    Gibt die verfügbaren Modes für ein spezifisches Fixture zurück.
    
    Args:
        username: GDTF Share Username
        password: GDTF Share Password
        manufacturer: Hersteller-Name
        fixture_name: Fixture-Name
        
    Returns:
        Liste der Modes mit Name und DMX-Footprint
    """
    fixtures = get_fixtures_by_manufacturer(username, password, manufacturer)
    
    for fixture in fixtures:
        if fixture.get("fixture", "").lower() == fixture_name.lower():
            return fixture.get("modes", [])
    
    return []


def clear_cache():
    """Cache leeren (z.B. nach Credential-Änderung)."""
    global _fixtures_cache
    _fixtures_cache = {"data": None, "timestamp": 0, "session": None}
    print("[GDTF] Cache geleert")
