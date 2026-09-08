import os
import pytest
from fastapi.testclient import TestClient

os.environ["JWT_SECRET_KEY"] = "testsecretkeyforunit testing12345"

from app.main import app
from app.database import SessionLocal
from app.services.agromonitoring_service import (
    get_district_obj,
    create_or_get_polygon,
    calculate_crop_satellite_analysis,
    CROP_PHENOLOGY_DEFAULTS
)
from app.services.crop_api_service import fetch_district_crops_from_api

client = TestClient(app)

def test_gulbarga_district_resolution():
    db = SessionLocal()
    try:
        d_obj = get_district_obj(db, "Karnataka", "Gulbarga")
        assert d_obj is not None
        assert d_obj.name.lower() in ["gulbarga", "kalaburagi"]
    finally:
        db.close()

def test_arhar_tur_crop_phenology():
    assert "arhar / tur" in CROP_PHENOLOGY_DEFAULTS
    conf = CROP_PHENOLOGY_DEFAULTS["arhar / tur"]
    assert conf["duration"] == 180
    assert "Planting" in conf["stages"]
    assert "Harvest" in conf["stages"]

def test_gulbarga_arhar_tur_crops_fetch():
    db = SessionLocal()
    try:
        res = fetch_district_crops_from_api(db, "Karnataka", "Gulbarga")
        assert res is not None
        crops = res.get("crops", [])
        assert len(crops) > 0
        arhar_crop = next((c for c in crops if "Arhar" in c.get("name", "") or "Tur" in c.get("name", "")), None)
        assert arhar_crop is not None
        assert arhar_crop["id"] is not None
    finally:
        db.close()

def test_gulbarga_arhar_tur_overview_endpoint():
    db = SessionLocal()
    try:
        res = fetch_district_crops_from_api(db, "Karnataka", "Gulbarga")
        arhar_crop = next(c for c in res["crops"] if "Arhar" in c.get("name", "") or "Tur" in c.get("name", ""))
        crop_id = arhar_crop["id"]
        
        response = client.get(f"/crops/{crop_id}/overview/growth/health")
        assert response.status_code == 200
        data = response.json()
        
        assert data["id"] == crop_id
        assert "Arhar" in data["name"] or "Tur" in data["name"]
        assert data["district"] in ["Gulbarga", "Kalaburagi"]
        assert data["state_name"] == "Karnataka"
        assert "health" in data
        assert "growth" in data
        assert "satellite_status" in data
        
        # When satellite is unavailable, health and growth should show unavailable cleanly without fake data
        if not data.get("satellite_available"):
            assert data["satellite_status"] == "SATELLITE DATA UNAVAILABLE"
            assert data["ndvi"] is None
            assert data["growth"]["current_stage"] == "Growth stage unavailable"
            assert data["growth"]["next_stage"] == "Growth stage unavailable"
    finally:
        db.close()

def test_multiple_crops_and_districts_isolation():
    db = SessionLocal()
    try:
        test_cases = [
            ("Karnataka", "Gulbarga", "Arhar / Tur"),
            ("Karnataka", "Dharwad", "Maize"),
            ("Karnataka", "Belagavi", "Soybean"),
            ("Madhya Pradesh", "Betul", "Wheat"),
            ("Madhya Pradesh", "Betul", "Soyabean"),
            ("Madhya Pradesh", "Dewas", "Potato"),
            ("Maharashtra", "Solapur", "Maize"),
            ("Maharashtra", "Sangli", "Soybean"),
            ("Madhya Pradesh", "Morena", "Wheat"),
            ("Rajasthan", "Bikaner", "Wheat"),
        ]
        for state, district, crop in test_cases:
            d_obj = get_district_obj(db, state, district)
            assert d_obj is not None, f"Failed to resolve district {district} in {state}"
    finally:
        db.close()
