import json
from core import show_logic

def test_rig_sync_deletion(client, sample_show):
    """
    Verifies that adding a fixture generates a UID and 
    deleting it removes it from the visual_plan.
    """
    # 1. Login
    client.post('/login', data=dict(username="Admin", password="Admin123"))
    
    show_id = sample_show["id"]
    
    # 2. Add a Strobe via update_rig
    # We simulate the form submission from show_rig_tab.html
    # For a new row, the UID is empty, and the backend generates one.
    payload = {
        "rig_strobes__count[]": ["1"],
        "rig_strobes__manufacturer[]": ["Martin"],
        "rig_strobes__model[]": ["Atomic 3000"],
        "rig_strobes__uid[]": [""], # Empty as if just added via "+" button
    }
    
    response = client.post(f'/show/{show_id}/update_rig', data=payload, follow_redirects=True)
    assert response.status_code == 200
    
    # Check that the show now has a strobe with a UID
    show = show_logic.find_show(show_id)
    rig = show["rig_setup"]
    assert len(rig["strobes_items"]) == 1
    strobe_uid = rig["strobes_items"][0]["uid"]
    assert strobe_uid is not None
    assert len(strobe_uid) > 0

    # 3. Simulate placing the strobe on the Stage Plan (visual_plan)
    # The key in visual_plan is {uid}_{instance_index}
    fixture_key = f"{strobe_uid}_0"
    rig["visual_plan"] = {
        fixture_key: {"left": 100, "top": 100}
    }
    show_logic.save_data()
    
    # Verify it's there
    show = show_logic.find_show(show_id)
    assert fixture_key in show["rig_setup"]["visual_plan"]

    # 4. Delete the strobe row
    # We send empty lists or empty values for that category
    # According to our new logic in show_details.py, if the row is empty, it gets filtered out.
    payload_delete = {
        "rig_strobes__count[]": [""],
        "rig_strobes__manufacturer[]": [""],
        "rig_strobes__model[]": [""],
        "rig_strobes__uid[]": [strobe_uid],
    }
    
    response = client.post(f'/show/{show_id}/update_rig', data=payload_delete, follow_redirects=True)
    assert response.status_code == 200
    
    # 5. Verify it's gone from both the patch and the visual_plan
    show = show_logic.find_show(show_id)
    rig = show["rig_setup"]
    
    # Should be empty because we filtered out the empty row
    assert len(rig.get("strobes_items", [])) == 0
    
    # Visual plan must be cleaned up!
    assert fixture_key not in rig.get("visual_plan", {})
    assert len(rig.get("visual_plan", {})) == 0
