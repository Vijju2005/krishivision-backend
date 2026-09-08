import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_morena_district_acreage_and_wheat_scoping():
    # Test GET /states/Madhya Pradesh/districts/Morena/crops
    response = client.get("/states/Madhya%20Pradesh/districts/Morena/crops")
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"
    
    data = response.json()
    assert data["state"] == "Madhya Pradesh"
    assert data["district"].lower() == "morena"
    
    monitored_area = data.get("monitored_area_acres")
    assert monitored_area is not None, "monitored_area_acres must be present"
    # Morena total APY reported crop area is 1,261,977.59 acres
    assert monitored_area > 1000000.0, f"Morena total area should be > 1M acres, got {monitored_area}"
    
    crops = data.get("crops", [])
    assert len(crops) > 0, "Morena should have crops"
    
    crop_names = [c["name"] for c in crops]
    
    # 1. Verify Wheat is present and scoped strictly to Morena Wheat (~305,837 acres)
    wheat = next((c for c in crops if c["name"].lower() == "wheat"), None)
    assert wheat is not None, f"Wheat must be present in Morena crops: {crop_names}"
    wheat_acres = wheat["area_acres"]
    # Wheat area in Morena 2019 APY is 305,836.92 acres
    assert 300000.0 <= wheat_acres <= 315000.0, f"Morena Wheat area must be ~305,837 acres, got {wheat_acres}"
    
    # Wheat acreage MUST NOT exceed total district monitored area
    assert wheat_acres < monitored_area, f"Wheat area ({wheat_acres}) cannot exceed district total ({monitored_area})"
    
    # 2. Verify Rapeseed & Mustard crop name formatting
    rapeseed = next((c for c in crops if "rapeseed" in c["name"].lower() or "mustard" in c["name"].lower()), None)
    assert rapeseed is not None, "Rapeseed & Mustard must be present in Morena"
    assert rapeseed["name"] == "Rapeseed & Mustard", f"Crop name must be formatted cleanly as 'Rapeseed & Mustard', got '{rapeseed['name']}'"
    assert rapeseed["area_acres"] > 350000.0, f"Rapeseed area should be ~366,143 acres, got {rapeseed['area_acres']}"

    # 3. Verify Map Endpoints for Morena return ~1,261,977.59 acres
    # Find Madhya Pradesh state ID from /map/states
    states_res = client.get("/map/states")
    assert states_res.status_code == 200
    states_data = states_res.json()
    mp_state = next((s for s in states_data if "madhya pradesh" in s["name"].lower()), None)
    assert mp_state is not None, "Madhya Pradesh state must exist in /map/states"
    mp_id = mp_state["id"]

    map_dists_res = client.get(f"/map/districts/{mp_id}")
    assert map_dists_res.status_code == 200
    map_dists = map_dists_res.json()
    morena_map = next((d for d in map_dists if d["name"].lower() == "morena"), None)
    assert morena_map is not None, "Morena must exist in /map/districts/{state_id}"
    map_area = morena_map["monitored_area"]
    assert abs(map_area - 1261977.59) < 10.0, f"Map endpoint monitored_area for Morena must be ~1,261,977.59, got {map_area}"

    detail_res = client.get(f"/map/districts/detail/{morena_map['id']}")
    assert detail_res.status_code == 200
    detail_data = detail_res.json()
    assert abs(detail_data["monitored_area"] - 1261977.59) < 10.0, f"Detail endpoint monitored_area for Morena must be ~1,261,977.59, got {detail_data['monitored_area']}"


def test_district_isolation_target_districts():
    target_districts = [
        ("Madhya Pradesh", "Betul", "Wheat", 600000.0),
        ("Madhya Pradesh", "Dewas", "Potato", 20000.0),
        ("Maharashtra", "Solapur", "Maize", 180000.0),
        ("Maharashtra", "Sangli", "Soybean", 100000.0),
        ("Uttar Pradesh", "Lakhimpur Kheri", "Sugarcane", 500000.0),
        ("Karnataka", "Dharwad", "Maize", 100000.0),
        ("Karnataka", "Belagavi", "Sugarcane", 400000.0),
        ("Rajasthan", "Bikaner", "Wheat", 250000.0),
    ]

    for state, district, crop_name, min_expected_acres in target_districts:
        url = f"/states/{state.replace(' ', '%20')}/districts/{district.replace(' ', '%20')}/crops"
        res = client.get(url)
        assert res.status_code == 200, f"Failed for {state} -> {district}"
        d_data = res.json()
        
        monitored = d_data.get("monitored_area_acres")
        assert monitored is not None and monitored > 0.0, f"Missing monitored area for {district}"
        
        crops = d_data.get("crops", [])
        assert len(crops) > 0, f"No crops for {district}"
        
        found_crop = next((c for c in crops if crop_name.lower() in c["name"].lower()), None)
        assert found_crop is not None, f"Crop {crop_name} missing in {district}"
        
        crop_acres = found_crop["area_acres"]
        assert crop_acres >= min_expected_acres, f"Expected >={min_expected_acres} acres for {crop_name} in {district}, got {crop_acres}"
        assert crop_acres < monitored, f"Crop acres ({crop_acres}) exceeds district total ({monitored}) in {district}"
