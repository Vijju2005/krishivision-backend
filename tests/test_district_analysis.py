import os
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.orm_models import District, State, DistrictAnalysisCache

TEST_DB_URL = "sqlite:///./test_krishivision_analysis.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

class TestDistrictAnalysis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.dependency_overrides[get_db] = override_get_db
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)
        
        # Seed test data for districts and states
        db = TestingSessionLocal()
        state = State(name="Karnataka")
        db.add(state)
        db.commit()
        db.refresh(state)
        
        dharwad = District(name="Dharwad", state_id=state.id, monitored_area_acres=150000.0)
        belagavi = District(name="Belagavi", state_id=state.id, monitored_area_acres=200000.0)
        haveri = District(name="Haveri", state_id=state.id, monitored_area_acres=100000.0)
        db.add(dharwad)
        db.add(belagavi)
        db.add(haveri)
        db.commit()
        db.close()

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=engine)
        if os.path.exists("./test_krishivision_analysis.db"):
            try:
                os.remove("./test_krishivision_analysis.db")
            except OSError:
                pass
        app.dependency_overrides.clear()

    def test_dharwad_crop_analysis(self):
        response = self.client.get("/districts/Dharwad/crop-analysis")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["district"], "Dharwad")
        self.assertEqual(data["state"], "Karnataka")
        self.assertEqual(data["cropland_area_acres"], 150000.0)
        self.assertIn("mean_ndvi", data)
        self.assertEqual(data["source"], "Satellite-derived")

    def test_belagavi_crop_analysis(self):
        response = self.client.get("/districts/Belagavi/crop-analysis")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["district"], "Belagavi")
        self.assertEqual(data["state"], "Karnataka")
        self.assertEqual(data["cropland_area_acres"], 200000.0)

    def test_haveri_crop_analysis(self):
        response = self.client.get("/districts/Haveri/crop-analysis")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["district"], "Haveri")
        self.assertEqual(data["state"], "Karnataka")
        self.assertEqual(data["cropland_area_acres"], 100000.0)

    def test_dynamic_seeding_and_analysis_for_new_district(self):
        db = TestingSessionLocal()
        state = db.query(State).first()
        new_dist = District(name="Mysuru", state_id=state.id, monitored_area_acres=80000.0)
        db.add(new_dist)
        db.commit()
        db.close()
        
        response = self.client.get("/districts/Mysuru/crop-analysis")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["district"], "Mysuru")
        self.assertEqual(data["cropland_area_acres"], 80000.0)

    def test_state_district_crops_endpoint_fallback(self):
        db = TestingSessionLocal()
        from app.models.orm_models import GovernmentCropCache
        cache_entry = GovernmentCropCache(
            state="Karnataka",
            district="DHARWAD",
            data=[
                {
                    "crop_name": "Maize",
                    "season": "Kharif",
                    "year": "2024",
                    "area": 12345.0,
                    "production": 45678.0,
                    "yield": 3.7
                }
            ]
        )
        db.add(cache_entry)
        db.commit()
        db.close()

        response = self.client.get("/states/Karnataka/districts/Dharwad/crops")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["district"], "DHARWAD")
        self.assertEqual(data["state"], "Karnataka")
        self.assertEqual(data["source"], "Cached government data")
        self.assertEqual(len(data["crops"]), 1)
        
        crop = data["crops"][0]
        self.assertEqual(crop["name"], "Maize")
        self.assertEqual(crop["area_hectares"], 12345.0)
        self.assertEqual(crop["production_tonnes"], 45678.0)
        self.assertEqual(crop["yield_kg_per_hectare"], 3700.0)
        self.assertEqual(crop["season"], "Kharif")
        self.assertEqual(crop["year"], "2024")

        # Also test GET /districts/Dharwad/crops
        response_dist = self.client.get("/districts/Dharwad/crops")
        self.assertEqual(response_dist.status_code, 200)
        data_dist = response_dist.json()
        self.assertEqual(data_dist["district"], "DHARWAD")
        self.assertEqual(data_dist["source"], "Cached government data")
        self.assertEqual(len(data_dist["crops"]), 1)

if __name__ == "__main__":
    unittest.main()
