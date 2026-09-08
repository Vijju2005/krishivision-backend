import os
import pytest
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Explicitly set database URL
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
db_path = os.path.join(backend_dir, "krishivision.db")
os.environ["DATABASE_URL"] = f"sqlite:///{db_path}"
os.environ["JWT_SECRET_KEY"] = "test_secret_key_krishivision_123"

from app.database import engine
from app.services.agromonitoring_service import calculate_crop_satellite_analysis
from app.services.pdf_service import generate_pdf_report
from app.models.orm_models import District, Crop, CropMaster, State

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def test_satellite_available_single_source_of_truth():
    db = SessionLocal()
    try:
        dist = db.query(District).first()
        crop_master = db.query(CropMaster).first()
        test_crop = Crop(id=9999, district_id=dist.id, crop_master_id=crop_master.id, area_acres=150.0)
        test_crop.district = dist
        test_crop.crop_master = crop_master

        # Case A: Live Satellite Data Available
        mock_sat_data = {
            "ndvi": 0.68,
            "evi": 0.55,
            "observation_date": "2026-03-01",
            "image_urls": {"truecolor": "http://example.com/tc.png"},
            "statistics": {"cloud_cover": 5.0, "resolution": "10m / Sen2Cor BOA"}
        }

        with patch("app.services.agromonitoring_service.get_agromonitoring_api_key", return_value="valid_key"):
            with patch("app.services.agromonitoring_service.fetch_satellite_indices_and_images", return_value=mock_sat_data):
                with patch("app.services.agromonitoring_service.fetch_ndvi_history", return_value=[]):
                    res = calculate_crop_satellite_analysis(db, test_crop)
                    assert res["satellite_available"] is True, "satellite_available must be True when satellite observations exist"
                    assert res["health_status"] in ["Good", "Moderate"], f"Expected Good or Moderate health status, got {res['health_status']}"
                    assert res["latest_ndvi"] == 0.68
                    assert res["observation_date"] == "2026-03-01"
                    assert res["est_harvest_days"] is not None

        # Case B: Satellite Data Unavailable (API returns None / No Observations)
        with patch("app.services.agromonitoring_service.get_agromonitoring_api_key", return_value="valid_key"):
            with patch("app.services.agromonitoring_service.fetch_satellite_indices_and_images", return_value=None):
                res_unavail = calculate_crop_satellite_analysis(db, test_crop)
                assert res_unavail["satellite_available"] is False, "satellite_available must be False when no observations exist"
                assert res_unavail["health_status"] == "Satellite data unavailable"
                assert res_unavail["growth_stage"] == "Growth stage unavailable"
                assert res_unavail["est_harvest_days"] is None
                assert res_unavail["latest_ndvi"] is None
                assert res_unavail["observation_date"] is None

        # Case C: API key missing
        with patch("app.services.agromonitoring_service.get_agromonitoring_api_key", return_value=""):
            res_nokey = calculate_crop_satellite_analysis(db, test_crop)
            assert res_nokey["satellite_available"] is False, "satellite_available must be False when API key is missing"
            assert res_nokey["health_status"] == "Satellite data unavailable"
            assert res_nokey["growth_stage"] == "Growth stage unavailable"
            assert res_nokey["est_harvest_days"] is None

    finally:
        db.close()


def test_pdf_report_satellite_status_consistency(tmp_path):
    db = SessionLocal()
    try:
        pdf_path = os.path.join(tmp_path, "test_report.pdf")
        
        # Test pdf generation with satellite_available = False
        generate_pdf_report(
            file_path=pdf_path,
            farmer_name="Test Farmer",
            crop="Wheat",
            district="Betul",
            area=654354.21,
            health="Satellite data unavailable",
            stage="Growth stage unavailable",
            confidence=0.0,
            harvest_in_days=None,
            avg_ndvi=None,
            lang="en",
            state="Madhya Pradesh",
            db_session=db
        )
        assert os.path.exists(pdf_path), "PDF report must be successfully generated"
        assert os.path.getsize(pdf_path) > 1000, "PDF file must be non-empty"
    finally:
        db.close()
