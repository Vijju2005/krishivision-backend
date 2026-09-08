import os
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Explicitly set database URL if not set
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
db_path = os.path.join(backend_dir, "krishivision.db")
os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
os.environ["JWT_SECRET_KEY"] = "test_secret_key_krishivision_123"

from app.database import get_db, engine
from app.routers.dashboard_map import get_district_monitored_area_acres, override_crop_with_apy_stats_if_needed
from app.models.orm_models import District, Crop, CropMaster, State

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_district_monitored_area_scoping():
    db = SessionLocal()
    try:
        # 1. Betul Monitored Area (~1,926,244 Acres)
        betul_area = get_district_monitored_area_acres(db, "Madhya Pradesh", "Betul")
        assert 1900000 <= betul_area <= 1950000, f"Expected ~1,926,244 acres for Betul, got {betul_area}"

        # 2. Dewas Monitored Area (~2,090,382 Acres)
        dewas_area = get_district_monitored_area_acres(db, "Madhya Pradesh", "Dewas")
        assert 2000000 <= dewas_area <= 2150000, f"Expected ~2,090,382 acres for Dewas, got {dewas_area}"

        # 3. Solapur Monitored Area (~2,456,093 Acres)
        solapur_area = get_district_monitored_area_acres(db, "Maharashtra", "Solapur")
        assert 2400000 <= solapur_area <= 2500000, f"Expected ~2,456,093 acres for Solapur, got {solapur_area}"
    finally:
        db.close()

def test_crop_cultivated_area_scoping():
    db = SessionLocal()
    try:
        # Test Betul Wheat vs Betul Soybean
        betul_dist = db.query(District).filter(District.name == "Betul").first()
        if not betul_dist:
            state_mp = db.query(State).filter(State.name == "Madhya Pradesh").first()
            if not state_mp:
                state_mp = State(name="Madhya Pradesh")
                db.add(state_mp)
                db.commit()
            betul_dist = District(name="Betul", state_id=state_mp.id)
            db.add(betul_dist)
            db.commit()

        wheat_master = db.query(CropMaster).filter(CropMaster.name == "Wheat").first()
        if not wheat_master:
            wheat_master = CropMaster(name="Wheat", category="Cereal")
            db.add(wheat_master)
            db.commit()

        soybean_master = db.query(CropMaster).filter(CropMaster.name == "Soybean").first()
        if not soybean_master:
            soybean_master = CropMaster(name="Soybean", category="Oilseed")
            db.add(soybean_master)
            db.commit()

        crop_betul_wheat = Crop(district_id=betul_dist.id, crop_master_id=wheat_master.id)
        crop_betul_wheat.district = betul_dist
        crop_betul_wheat.crop_master = wheat_master

        crop_betul_wheat = override_crop_with_apy_stats_if_needed(db, crop_betul_wheat)
        assert 650000 <= crop_betul_wheat.area_acres <= 660000, f"Expected ~654,354 acres for Betul Wheat, got {crop_betul_wheat.area_acres}"

        crop_betul_soybean = Crop(district_id=betul_dist.id, crop_master_id=soybean_master.id)
        crop_betul_soybean.district = betul_dist
        crop_betul_soybean.crop_master = soybean_master

        crop_betul_soybean = override_crop_with_apy_stats_if_needed(db, crop_betul_soybean)
        assert 480000 <= crop_betul_soybean.area_acres <= 490000, f"Expected ~486,285 acres for Betul Soybean, got {crop_betul_soybean.area_acres}"

        # Verify crop area is strictly smaller than district total monitored area
        betul_monitored = get_district_monitored_area_acres(db, "Madhya Pradesh", "Betul")
        assert crop_betul_wheat.area_acres < betul_monitored, "Crop cultivated area must be strictly less than total district monitored area"
        assert crop_betul_soybean.area_acres < betul_monitored, "Crop cultivated area must be strictly less than total district monitored area"

    finally:
        db.close()

def test_fetch_district_crops_semantics():
    db = SessionLocal()
    try:
        from app.services.crop_api_service import fetch_district_crops_from_api
        res = fetch_district_crops_from_api(db, "Madhya Pradesh", "Betul")
        assert res["status"] == "success"
        assert res["monitored_area_label"] == "Total APY Crop Area Reported"
        assert res["monitored_area_source"] == "APY Dataset (Gross Cropped Area)"
        assert res["monitored_area_scope"] == "district_total_crop_area"
        assert res["crop_year"] == 2019
        
        crops = res["crops"]
        assert len(crops) > 0
        first_crop = crops[0]
        assert "crop_year" in first_crop
        assert "season" in first_crop
        assert first_crop["area_scope"] == "crop_in_district"
        assert first_crop["source"] == "APY Dataset"
    finally:
        db.close()

