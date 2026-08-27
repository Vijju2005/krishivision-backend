import os
import unittest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

# Use a separate SQLite database for testing to avoid modifying production/dev data
TEST_DB_URL = "sqlite:///./test_krishivision.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


class TestKrishiVisionAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.dependency_overrides[get_db] = override_get_db
        # Create database schema
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        # Clean up database schema and delete test db file
        Base.metadata.drop_all(bind=engine)
        if os.path.exists("./test_krishivision.db"):
            try:
                os.remove("./test_krishivision.db")
            except OSError:
                pass
        app.dependency_overrides.clear()

    def test_read_root(self):
        # Verify the root endpoint displays the updated app name "KrishiVision"
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "ok", "service": "KrishiVision"})

    def test_health_check(self):
        response = self.client.get("/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"status": "healthy"})

    def test_auth_registration_and_login(self):
        # 1. Test register user
        payload = {
            "full_name": "Test Farmer",
            "email": "testfarmer@example.com",
            "phone": "+91 9900000000",
            "password": "securepassword123",
        }
        response = self.client.post("/auth/register", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["full_name"], "Test Farmer")
        self.assertEqual(data["role"], "admin") # First registered user gets admin role for testing

        # Register a second user to test standard user registration
        payload_user = {
            "full_name": "Regular Farmer",
            "email": "regularfarmer@example.com",
            "phone": "+91 9900000001",
            "password": "securepassword123",
        }
        response_user = self.client.post("/auth/register", json=payload_user)
        self.assertEqual(response_user.status_code, 200)
        data_user = response_user.json()
        self.assertEqual(data_user["role"], "user")

        # 2. Test duplicate register fails
        response = self.client.post("/auth/register", json=payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("detail", response.json())

        # 3. Test login with correct credentials
        login_payload = {
            "email": "testfarmer@example.com",
            "password": "securepassword123",
        }
        response = self.client.post("/auth/login", json=login_payload)
        self.assertEqual(response.status_code, 200)
        login_data = response.json()
        self.assertIn("access_token", login_data)
        self.assertEqual(login_data["full_name"], "Test Farmer")
        self.assertEqual(login_data["role"], "admin")

        # 4. Test login with wrong password fails
        wrong_payload = {
            "email": "testfarmer@example.com",
            "password": "wrongpassword",
        }
        response = self.client.post("/auth/login", json=wrong_payload)
        self.assertEqual(response.status_code, 401)

    def test_social_login(self):
        # 1. Register a new user via social login
        payload = {
            "provider": "google",
            "email": "socialfarmer@example.com",
            "full_name": "Social Google Farmer",
            "id": "google123456"
        }
        response = self.client.post("/auth/social-login", json=payload)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["full_name"], "Social Google Farmer")
        self.assertEqual(data["role"], "user")

        # 2. Login again with the same social details (verifying it logs in existing user)
        response_login = self.client.post("/auth/social-login", json=payload)
        self.assertEqual(response_login.status_code, 200)
        data_login = response_login.json()
        self.assertIn("access_token", data_login)
        self.assertEqual(data_login["user_id"], data["user_id"])

    def test_combined_crop_details(self):
        db = TestingSessionLocal()
        from app.models.orm_models import State, District, Crop, CropMaster
        state = State(name="KarnatakaTest", boundary_geojson={"type": "Polygon", "coordinates": []})
        db.add(state)
        db.commit()
        
        district = District(state_id=state.id, name="BelagaviTest", boundary_geojson={"type": "Polygon", "coordinates": []}, monitored_area_acres=100.0)
        db.add(district)
        db.commit()
        
        crop_master = CropMaster(
            name="SugarcaneTest",
            scientific_name="Saccharum officinarum",
            category="Commercial",
            growing_season="Kharif",
            growth_duration="12 Months",
            description="Sugarcane test"
        )
        db.add(crop_master)
        db.commit()
        
        crop = Crop(
            district_id=district.id,
            crop_master_id=crop_master.id,
            area_acres=50.0,
            crop_percentage=10.0,
            growth_stage="Vegetative",
            health_status="Healthy",
            harvest_in_days=60,
            fields_count=2,
            boundary_geojson={"type": "Polygon", "coordinates": []},
            avg_ndvi=0.75,
            avg_evi=0.60,
            moisture_level=30.0,
            temperature=27.0
        )
        db.add(crop)
        db.commit()
        crop_id = crop.id
        db.close()
        
        response = self.client.get(f"/crops/{crop_id}/overview/growth/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "SugarcaneTest")
        self.assertEqual(data["district"], "BelagaviTest")
        self.assertEqual(data["health_index"], 70)
        self.assertEqual(data["total_fields"], 2)

    def test_profile_photo_upload_and_delete(self):
        # 1. Login to get token
        login_payload = {
            "email": "testfarmer@example.com",
            "password": "securepassword123",
        }
        login_resp = self.client.post("/auth/login", json=login_payload)
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 2. Upload photo
        import io
        file_data = io.BytesIO(b"fake image data")
        response = self.client.post(
            "/auth/profile-photo",
            files={"file": ("test.png", file_data, "image/png")},
            headers=headers
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        profile_photo_path = data["profile_photo"]
        self.assertTrue(profile_photo_path.startswith("/static/profile_photos/user_"))

        # 3. Check /auth/me returns the profile photo
        me_resp = self.client.get("/auth/me", headers=headers)
        self.assertEqual(me_resp.status_code, 200)
        self.assertEqual(me_resp.json()["profile_photo"], profile_photo_path)

        # 4. Delete photo
        del_resp = self.client.delete("/auth/profile-photo", headers=headers)
        self.assertEqual(del_resp.status_code, 200)
        self.assertEqual(del_resp.json()["status"], "success")

        # 5. Check /auth/me has no profile photo
        me_resp2 = self.client.get("/auth/me", headers=headers)
        self.assertEqual(me_resp2.status_code, 200)
        self.assertIsNone(me_resp2.json()["profile_photo"])

    def test_dashboard_summary_scenarios(self):
        # 1. Register User A and User B
        user_a_payload = {
            "full_name": "Farmer A",
            "email": "farmer_a@example.com",
            "phone": "+91 9900000100",
            "password": "password123",
        }
        resp_a = self.client.post("/auth/register", json=user_a_payload)
        self.assertEqual(resp_a.status_code, 200)
        token_a = resp_a.json()["access_token"]
        user_a_id = resp_a.json()["user_id"]
        headers_a = {"Authorization": f"Bearer {token_a}"}

        user_b_payload = {
            "full_name": "Farmer B",
            "email": "farmer_b@example.com",
            "phone": "+91 9900000200",
            "password": "password123",
        }
        resp_b = self.client.post("/auth/register", json=user_b_payload)
        self.assertEqual(resp_b.status_code, 200)
        token_b = resp_b.json()["access_token"]
        headers_b = {"Authorization": f"Bearer {token_b}"}

        # 2. Check User A starts with 0 for all summary stats
        summary_resp = self.client.get("/dashboard/summary", headers=headers_a)
        self.assertEqual(summary_resp.status_code, 200)
        summary_data = summary_resp.json()
        self.assertEqual(summary_data["total_monitored_area"], 0.0)
        self.assertEqual(summary_data["healthy_area"], 0.0)
        self.assertEqual(summary_data["at_risk_area"], 0.0)
        self.assertEqual(summary_data["total_crops"], 0)
        self.assertEqual(summary_data["upcoming_harvest"], 0)

        # 3. Add 4 analyses for User A with known acreage and health statuses
        db = override_get_db().__next__()
        from app.models.orm_models import Analysis
        
        # Crop 1: Healthy (via health_status), 10.0 acres, harvest in 10 days
        a1 = Analysis(
            owner_id=user_a_id,
            status="completed",
            crop="Rice",
            district="Davanagere",
            area_acres=10.0,
            growth_stage="Maturity",
            health_status="Healthy",
            harvest_in_days=10,
            avg_ndvi=0.70
        )
        # Crop 2: At Risk (via health_status), 5.0 acres, harvest in 40 days
        a2 = Analysis(
            owner_id=user_a_id,
            status="completed",
            crop="Maize",
            district="Haveri",
            area_acres=5.0,
            growth_stage="Flowering",
            health_status="At Risk",
            harvest_in_days=40,
            avg_ndvi=0.45
        )
        # Crop 3: Generic health (will fallback to avg_ndvi >= 0.55 -> Healthy), 12.0 acres, harvest in 60 days (estimated/planting)
        a3 = Analysis(
            owner_id=user_a_id,
            status="completed",
            crop="Cotton",
            district="Dharwad",
            area_acres=12.0,
            growth_stage="Vegetative",
            health_status="Major crops reported for this district",
            harvest_in_days=None,  # Will estimate as 60 -> not upcoming
            avg_ndvi=0.60
        )
        # Crop 4: Generic health (will fallback to avg_ndvi < 0.55 -> At Risk), 8.0 acres, harvest in 30 days (estimated/silking)
        a4 = Analysis(
            owner_id=user_a_id,
            status="completed",
            crop="Groundnut",
            district="Gadag",
            area_acres=8.0,
            growth_stage="Silking",
            health_status="Major crops reported for this district",
            harvest_in_days=None,  # Will estimate as 30 -> upcoming
            avg_ndvi=0.40
        )
        
        db.add_all([a1, a2, a3, a4])
        db.commit()
        db.close()

        # 4. Check User A dashboard summary totals
        # Total area = 10 + 5 + 12 + 8 = 35.0
        # Healthy Area = Rice (10.0) + Cotton (12.0) = 22.0
        # At Risk Area = Maize (5.0) + Groundnut (8.0) = 13.0
        # Total Crops = Rice, Maize, Cotton, Groundnut = 4
        # Upcoming Harvest = Rice (10 <= 50) + Maize (40 <= 50) + Groundnut (estimated 30 <= 50) = 3
        summary_resp = self.client.get("/dashboard/summary", headers=headers_a)
        self.assertEqual(summary_resp.status_code, 200)
        summary_data = summary_resp.json()
        self.assertEqual(summary_data["total_monitored_area"], 35.0)
        self.assertEqual(summary_data["healthy_area"], 22.0)
        self.assertEqual(summary_data["at_risk_area"], 13.0)
        self.assertEqual(summary_data["total_crops"], 4)
        self.assertEqual(summary_data["upcoming_harvest"], 3)

        # 5. Check User B dashboard summary remains 0 (different users isolation)
        summary_resp_b = self.client.get("/dashboard/summary", headers=headers_b)
        self.assertEqual(summary_resp_b.status_code, 200)
        self.assertEqual(summary_resp_b.json()["total_monitored_area"], 0.0)

        # 6. Add another analysis to verify it updates immediately
        db = override_get_db().__next__()
        a5 = Analysis(
            owner_id=user_a_id,
            status="completed",
            crop="Rice",  # Same crop, total crops should remain 4
            district="Davanagere",
            area_acres=5.0,
            growth_stage="Maturity",
            health_status="Healthy",
            harvest_in_days=10,
            avg_ndvi=0.75
        )
        db.add(a5)
        db.commit()
        db.close()

        summary_resp = self.client.get("/dashboard/summary", headers=headers_a)
        self.assertEqual(summary_resp.status_code, 200)
        summary_data = summary_resp.json()
        self.assertEqual(summary_data["total_monitored_area"], 40.0)
        self.assertEqual(summary_data["healthy_area"], 27.0)
        self.assertEqual(summary_data["total_crops"], 4)
        self.assertEqual(summary_data["upcoming_harvest"], 4)

    @patch("app.services.data_gov_crop_service.get_api_key", return_value="dummy-key-for-test")
    @patch("urllib.request.urlopen")
    def test_data_gov_integration(self, mock_urlopen, mock_get_api_key):
        import json
        
        # Setup Punjab and Mansa in the test DB
        db = override_get_db().__next__()
        from app.models.orm_models import State, District
        # Check if already exists to avoid conflict
        state_obj = db.query(State).filter(State.name == "Punjab").first()
        if not state_obj:
            state_obj = State(id=20, name="Punjab", boundary_geojson={"type": "Polygon", "coordinates": []})
            db.add(state_obj)
            db.commit()
            db.refresh(state_obj)
            
        district_obj = db.query(District).filter(District.name == "Mansa").first()
        if not district_obj:
            district_obj = District(id=200, state_id=state_obj.id, name="Mansa", boundary_geojson={"type": "Polygon", "coordinates": []})
            db.add(district_obj)
            db.commit()
        db.close()

        user_payload = {
            "full_name": "Test India Farmer",
            "email": "india_farmer@example.com",
            "phone": "+91 9900000300",
            "password": "password123",
        }
        resp = self.client.post("/auth/register", json=user_payload)
        self.assertEqual(resp.status_code, 200)
        token = resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        
        # 2. Mock successful response from data.gov.in
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        
        mock_json_str = json.dumps({
            "records": [
                {
                    "state_name": "Punjab",
                    "district_name": "MANSA",
                    "crop_year": "2023",
                    "season": "Kharif",
                    "crop": "Maize",
                    "area_": "1200.0",
                    "production_": "4800.0"
                },
                {
                    "state_name": "Punjab",
                    "district_name": "MANSA",
                    "crop_year": "2022",
                    "season": "Kharif",
                    "crop": "Maize",
                    "area_": "1000.0",
                    "production_": "3000.0"
                },
                {
                    "state_name": "Punjab",
                    "district_name": "MANSA",
                    "crop_year": "2023",
                    "season": "Rabi",
                    "crop": "Wheat",
                    "area_": "3000.0",
                    "production_": "12000.0"
                }
            ]
        })
        mock_response.read.return_value = mock_json_str.encode('utf-8')
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # 3. Call endpoint GET /crops/india/district?state=Punjab&district=Mansa
        resp = self.client.get("/crops/india/district?state=Punjab&district=Mansa", headers=headers)
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        
        # Verify normalization and results
        self.assertEqual(data["state"], "Punjab")
        self.assertEqual(data["district"], "MANSA")
        self.assertEqual(len(data["crops"]), 2)
        
        # Crop 1: Maize (yield = 4800 / 1200 = 4.0, latest year 2023 selected)
        # Maize can be in any order, so find it
        c1 = next(c for c in data["crops"] if c["crop_name"] == "Maize")
        self.assertEqual(c1["yield"], 4.0)
        self.assertEqual(c1["area"], 1200.0)
        self.assertEqual(c1["production"], 4800.0)
        self.assertEqual(c1["season"], "Kharif")
        self.assertEqual(c1["year"], 2023)
        self.assertIsNotNone(c1["id"])

        # Check district cache saved
        db = override_get_db().__next__()
        from app.models.orm_models import GovernmentCropCache
        cache_rec = db.query(GovernmentCropCache).filter(
            GovernmentCropCache.state == "Punjab",
            GovernmentCropCache.district == "MANSA"
        ).first()
        self.assertIsNotNone(cache_rec)
        db.close()

        # 4. Check cached response fallback on HTTP error (e.g. 500)
        mock_urlopen.side_effect = Exception("API error")
        resp_cached = self.client.get("/crops/india/district?state=Punjab&district=Mansa", headers=headers)
        self.assertEqual(resp_cached.status_code, 200)
        self.assertTrue(resp_cached.json()["cached"])

        # 5. Check empty cache and HTTP 503 when API is down
        resp_error = self.client.get("/crops/india/district?state=Haryana&district=Sirsa", headers=headers)
        self.assertEqual(resp_error.status_code, 503)

    def test_api_status_endpoint(self):
        # Test status endpoint when configured and reachable
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200

        with patch("urllib.request.urlopen") as mock_urlopen:
            mock_urlopen.return_value.__enter__.return_value = mock_response
            with patch("app.services.data_gov_crop_service.get_api_key", return_value="some-key"):
                resp = self.client.get("/crops/india/api-status")
                self.assertEqual(resp.status_code, 200)
                data = resp.json()
                self.assertTrue(data["configured"])
                self.assertTrue(data["reachable"])
                self.assertEqual(data["source"], "data.gov.in")

        # Test when not configured
        with patch("app.services.data_gov_crop_service.get_api_key", return_value=""):
            resp = self.client.get("/crops/india/api-status")
            self.assertEqual(resp.status_code, 200)
            data = resp.json()
            self.assertFalse(data["configured"])
            self.assertFalse(data["reachable"])


if __name__ == "__main__":
    unittest.main()
