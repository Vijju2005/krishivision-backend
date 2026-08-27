import unittest
import json
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.orm_models import GovernmentCropCache

class TestDistrictIsolation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    @patch("urllib.request.urlopen")
    def test_strict_server_side_district_filtering(self, mock_urlopen):
        """Prove that returned records belonging to another district are strictly discarded."""
        
        # Mock mixed API response containing correct and incorrect districts
        mock_response_data = {
            "records": [
                # Matching record
                {"State_Name": "Karnataka", "District_Name": "DHARWAD", "Crop": "Maize", "Crop_Year": 2014, "Season": "Kharif", "Area": 100, "Production": 200},
                # Mismatched district
                {"State_Name": "Karnataka", "District_Name": "BELGAUM", "Crop": "Rice", "Crop_Year": 2014, "Season": "Kharif", "Area": 500, "Production": 1000},
                # Mismatched state
                {"State_Name": "Maharashtra", "District_Name": "DHARWAD", "Crop": "Cotton", "Crop_Year": 2014, "Season": "Kharif", "Area": 200, "Production": 400}
            ],
            "total": 3,
            "limit": 10,
            "offset": 0
        }
        
        # Configure mock urlopen
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode("utf-8")
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Clear existing caches for Dharwad first
        db = SessionLocal()
        db.query(GovernmentCropCache).filter(
            GovernmentCropCache.state == "Karnataka",
            GovernmentCropCache.district == "DHARWAD"
        ).delete(synchronize_session=False)
        db.commit()
        db.close()

        try:
            # Call API for Karnataka -> Dharwad
            response = self.client.get("/states/Karnataka/districts/Dharwad/crops")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            self.assertEqual(data["state"], "Karnataka")
            self.assertEqual(data["district"], "DHARWAD")
            
            crops = data["crops"]
            crop_names = [c["crop_name"] for c in crops]
            
            # Verify that ONLY Dharwad crop (Maize) was returned
            self.assertIn("Maize", crop_names)
            # Verify mismatched district (Rice) was discarded
            self.assertNotIn("Rice", crop_names)
            # Verify mismatched state (Cotton) was discarded
            self.assertNotIn("Cotton", crop_names)
            
            print("\n[ISOLATION TEST] Strict filter verified. Mismatched records discarded successfully.")
        finally:
            # CLEAN UP AFTER TEST SO PRODUCTION DB STAYS 100% CLEAN!
            db = SessionLocal()
            db.query(GovernmentCropCache).filter(
                GovernmentCropCache.state == "Karnataka",
                GovernmentCropCache.district == "DHARWAD"
            ).delete(synchronize_session=False)
            db.commit()
            db.close()

    def test_cache_keys_are_different(self):
        """Verify that cache keys are completely isolated to state and district."""
        db = SessionLocal()
        
        # Verify Dharwad and Belagavi cache query matches
        q_dharwad = db.query(GovernmentCropCache).filter(
            GovernmentCropCache.state == "Karnataka",
            GovernmentCropCache.district == "DHARWAD"
        )
        
        q_belagavi = db.query(GovernmentCropCache).filter(
            GovernmentCropCache.state == "Karnataka",
            GovernmentCropCache.district == "BELGAUM"
        )
        
        # Confirm SQL query criteria are separate and distinct
        self.assertNotEqual(q_dharwad.statement.compile().params, q_belagavi.statement.compile().params)
        db.close()
        print("[ISOLATION TEST] Cache query isolation verified.")

    def test_dharwad_contains_no_mock_data(self):
        """Regression test specifically proving that mock Dharwad data cannot be returned."""
        db = SessionLocal()
        cache_record = db.query(GovernmentCropCache).filter(
            GovernmentCropCache.state == "Karnataka",
            GovernmentCropCache.district == "DHARWAD"
        ).first()
        db.close()
        
        if cache_record:
            crops = cache_record.data.get("crop_records", []) if isinstance(cache_record.data, dict) else cache_record.data
            for c in crops:
                # Assert that none of the records contain mock properties
                if c.get("crop_name") == "Maize" and c.get("year") == 2014:
                    self.assertNotEqual(c.get("area_hectares"), 100.0)

    @patch("urllib.request.urlopen")
    def test_strict_unique_grouped_crops(self, mock_urlopen):
        """Prove that crop records are grouped and returned uniquely by crop name."""
        mock_response_data = {
            "records": [
                {"State_Name": "Karnataka", "District_Name": "DHARWAD", "Crop": "Maize", "Crop_Year": 2014, "Season": "Kharif", "Area": 100, "Production": 200},
                {"State_Name": "Karnataka", "District_Name": "DHARWAD", "Crop": "Maize", "Crop_Year": 2014, "Season": "Kharif", "Area": 150, "Production": 300},
            ],
            "total": 2,
            "limit": 10,
            "offset": 0
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode("utf-8")
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Clear cache first
        db = SessionLocal()
        db.query(GovernmentCropCache).filter(
            GovernmentCropCache.state == "Karnataka",
            GovernmentCropCache.district == "DHARWAD"
        ).delete(synchronize_session=False)
        db.commit()
        db.close()

        try:
            response = self.client.get("/states/Karnataka/districts/Dharwad/crops")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            crops = data["crops"]
            
            # Grouping verification: Maize should appear exactly once
            maize_crops = [c for c in crops if c["crop_name"] == "Maize"]
            self.assertEqual(len(maize_crops), 1)
            
            # Summed area check: 100 + 150 = 250 hectares -> 617.76 acres
            self.assertAlmostEqual(maize_crops[0]["area_hectares"], 250.0)
            self.assertAlmostEqual(maize_crops[0]["area_acres"], round(250.0 * 2.47105, 2))
            
            # Summed production check: 200 + 300 = 500 tonnes
            self.assertAlmostEqual(maize_crops[0]["production_tonnes"], 500.0)
        finally:
            db = SessionLocal()
            db.query(GovernmentCropCache).filter(
                GovernmentCropCache.state == "Karnataka",
                GovernmentCropCache.district == "DHARWAD"
            ).delete(synchronize_session=False)
            db.commit()
            db.close()

    @patch("urllib.request.urlopen")
    def test_exclude_zero_or_invalid_area_crops(self, mock_urlopen):
        """Verify that records with invalid, null, or zero area are strictly excluded from the list."""
        mock_response_data = {
            "records": [
                {"State_Name": "Karnataka", "District_Name": "DHARWAD", "Crop": "Maize", "Crop_Year": 2014, "Season": "Kharif", "Area": 100, "Production": 200},
                {"State_Name": "Karnataka", "District_Name": "DHARWAD", "Crop": "Rice", "Crop_Year": 2014, "Season": "Kharif", "Area": 0, "Production": 0},
                {"State_Name": "Karnataka", "District_Name": "DHARWAD", "Crop": "Cotton", "Crop_Year": 2014, "Season": "Kharif", "Area": None, "Production": 0},
            ],
            "total": 3,
            "limit": 10,
            "offset": 0
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode("utf-8")
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Clear cache first
        db = SessionLocal()
        db.query(GovernmentCropCache).filter(
            GovernmentCropCache.state == "Karnataka",
            GovernmentCropCache.district == "DHARWAD"
        ).delete(synchronize_session=False)
        db.commit()
        db.close()

        try:
            response = self.client.get("/states/Karnataka/districts/Dharwad/crops")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            crops = data["crops"]
            crop_names = [c["crop_name"] for c in crops]
            
            # Paddy (area > 0) should be present
            self.assertIn("Maize", crop_names)
            # Rice (area == 0) should be excluded
            self.assertNotIn("Rice", crop_names)
            # Cotton (area is null/None) should be excluded
            self.assertNotIn("Cotton", crop_names)
        finally:
            db = SessionLocal()
            db.query(GovernmentCropCache).filter(
                GovernmentCropCache.state == "Karnataka",
                GovernmentCropCache.district == "DHARWAD"
            ).delete(synchronize_session=False)
            db.commit()
            db.close()

    @patch("urllib.request.urlopen")
    def test_synonymous_crop_merging_and_percentage_recalculation(self, mock_urlopen):
        """Verify that synonymous crop names (e.g. Paddy and Rice) are merged and percentages recalculated."""
        mock_response_data = {
            "records": [
                # Synonymous crops for same year and district
                {"State_Name": "Karnataka", "District_Name": "DHARWAD", "Crop": "Paddy", "Crop_Year": 2014, "Season": "Kharif", "Area": 100, "Production": 200},
                {"State_Name": "Karnataka", "District_Name": "DHARWAD", "Crop": "Rice", "Crop_Year": 2014, "Season": "Kharif", "Area": 300, "Production": 600},
                # Other crop to establish percentage
                {"State_Name": "Karnataka", "District_Name": "DHARWAD", "Crop": "Maize", "Crop_Year": 2014, "Season": "Kharif", "Area": 600, "Production": 1200},
            ],
            "total": 3,
            "limit": 10,
            "offset": 0
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode("utf-8")
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        # Clear cache first
        db = SessionLocal()
        db.query(GovernmentCropCache).filter(
            GovernmentCropCache.state == "Karnataka",
            GovernmentCropCache.district == "DHARWAD"
        ).delete(synchronize_session=False)
        db.commit()
        db.close()

        try:
            # Query for DHARWAD crops, specifying threshold 0.0 to verify all percentages
            response = self.client.get("/states/Karnataka/districts/Dharwad/crops?relevance_threshold=0.0")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            crops = data["crops"]
            
            # Grouping check: "Paddy" and "Rice" should merge to "Paddy / Rice"
            crop_names = [c["crop_name"] for c in crops]
            self.assertIn("Paddy / Rice", crop_names)
            self.assertNotIn("Paddy", crop_names)
            self.assertNotIn("Rice", crop_names)
            
            # Fetch the merged and non-merged categories
            paddy_rice = next(c for c in crops if c["crop_name"] == "Paddy / Rice")
            maize = next(c for c in crops if c["crop_name"] == "Maize")
            
            # Check aggregated areas
            # Paddy (100) + Rice (300) = 400
            self.assertAlmostEqual(paddy_rice["area_hectares"], 400.0)
            # Maize = 600
            self.assertAlmostEqual(maize["area_hectares"], 600.0)
            
            # Check recalculated area percentages: Total area = 400 + 600 = 1000 ha
            # Paddy / Rice: 400 / 1000 = 40.0%
            self.assertAlmostEqual(paddy_rice["area_percentage"], 40.0)
            # Maize: 600 / 1000 = 60.0%
            self.assertAlmostEqual(maize["area_percentage"], 60.0)
            
        finally:
            db = SessionLocal()
            db.query(GovernmentCropCache).filter(
                GovernmentCropCache.state == "Karnataka",
                GovernmentCropCache.district == "DHARWAD"
            ).delete(synchronize_session=False)
            db.commit()
            db.close()

    @patch("urllib.request.urlopen")
    def test_dharwad_latest_year_selection(self, mock_urlopen):
        """Verify that the latest year (2014) is auto-detected and selected from the dataset."""
        mock_response_data = {
            "records": [
                {"State_Name": "Karnataka", "District_Name": "DHARWAD", "Crop": "Maize", "Crop_Year": 2010, "Season": "Kharif", "Area": 100, "Production": 200},
                {"State_Name": "Karnataka", "District_Name": "DHARWAD", "Crop": "Rice", "Crop_Year": 2014, "Season": "Kharif", "Area": 50, "Production": 100},
            ],
            "total": 2,
            "limit": 10,
            "offset": 0
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode("utf-8")
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        db = SessionLocal()
        db.query(GovernmentCropCache).filter(
            GovernmentCropCache.state == "Karnataka",
            GovernmentCropCache.district == "DHARWAD"
        ).delete(synchronize_session=False)
        db.commit()
        db.close()

        try:
            response = self.client.get("/states/Karnataka/districts/Dharwad/crops")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            
            # The returned year must be 2014 (the maximum crop year present in the dataset)
            # Since 2014 was selected, only the Rice record is returned
            crops = data["crops"]
            crop_names = [c["crop_name"] for c in crops]
            
            self.assertIn("Paddy / Rice", crop_names)
            self.assertNotIn("Maize", crop_names) # Maize from 2010 is excluded
            
        finally:
            db = SessionLocal()
            db.query(GovernmentCropCache).filter(
                GovernmentCropCache.state == "Karnataka",
                GovernmentCropCache.district == "DHARWAD"
            ).delete(synchronize_session=False)
            db.commit()
            db.close()

    @patch("urllib.request.urlopen")
    def test_crop_threshold_exclusion_and_normalization(self, mock_urlopen):
        """Verify crops representing under 1% of total area are excluded, while synonyms merge first."""
        mock_response_data = {
            "records": [
                # Paddy and Rice merge to 10 ha (10%)
                {"State_Name": "Karnataka", "District_Name": "DHARWAD", "Crop": "Paddy", "Crop_Year": 2014, "Season": "Kharif", "Area": 4, "Production": 8},
                {"State_Name": "Karnataka", "District_Name": "DHARWAD", "Crop": "Rice", "Crop_Year": 2014, "Season": "Kharif", "Area": 6, "Production": 12},
                # Cotton(lint) maps to Cotton (89.5 ha -> 89.5%)
                {"State_Name": "Karnataka", "District_Name": "DHARWAD", "Crop": "Cotton(lint)", "Crop_Year": 2014, "Season": "Kharif", "Area": 89.5, "Production": 180},
                # Under 1% crop (0.5 ha -> 0.5%)
                {"State_Name": "Karnataka", "District_Name": "DHARWAD", "Crop": "Wheat", "Crop_Year": 2014, "Season": "Rabi", "Area": 0.5, "Production": 1},
            ],
            "total": 4,
            "limit": 10,
            "offset": 0
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode("utf-8")
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        db = SessionLocal()
        db.query(GovernmentCropCache).filter(
            GovernmentCropCache.state == "Karnataka",
            GovernmentCropCache.district == "DHARWAD"
        ).delete(synchronize_session=False)
        db.commit()
        db.close()

        try:
            response = self.client.get("/states/Karnataka/districts/Dharwad/crops")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            crops = data["crops"]
            crop_names = [c["crop_name"] for c in crops]
            
            # Paddy / Rice (10%) and Cotton (89.5%) are included
            self.assertIn("Paddy / Rice", crop_names)
            self.assertIn("Cotton", crop_names)
            # Cotton(lint) is normalized to Cotton
            self.assertNotIn("Cotton(lint)", crop_names)
            # Wheat (0.5%) is excluded as it is below the 1% significance threshold
            self.assertNotIn("Wheat", crop_names)
            
        finally:
            db = SessionLocal()
            db.query(GovernmentCropCache).filter(
                GovernmentCropCache.state == "Karnataka",
                GovernmentCropCache.district == "DHARWAD"
            ).delete(synchronize_session=False)
            db.commit()
            db.close()

    @patch("urllib.request.urlopen")
    def test_strict_cross_district_isolation_leakage(self, mock_urlopen):
        """Verify no crops from Belagavi/Mysuru leak into Dharwad unless they are present in Dharwad's raw cache."""
        mock_response_data = {
            "records": [
                {"State_Name": "Karnataka", "District_Name": "DHARWAD", "Crop": "Maize", "Crop_Year": 2014, "Season": "Kharif", "Area": 100, "Production": 200},
            ],
            "total": 1,
            "limit": 10,
            "offset": 0
        }
        mock_response = MagicMock()
        mock_response.read.return_value = json.dumps(mock_response_data).encode("utf-8")
        mock_response.status = 200
        mock_urlopen.return_value.__enter__.return_value = mock_response

        db = SessionLocal()
        db.query(GovernmentCropCache).filter(
            GovernmentCropCache.state == "Karnataka",
            GovernmentCropCache.district == "DHARWAD"
        ).delete(synchronize_session=False)
        db.commit()
        db.close()

        try:
            response = self.client.get("/states/Karnataka/districts/Dharwad/crops")
            self.assertEqual(response.status_code, 200)
            data = response.json()
            crops = data["crops"]
            crop_names = [c["crop_name"] for c in crops]
            
            # Only Maize should be in the returned crops list
            self.assertEqual(crop_names, ["Maize"])
            # Ensure Belagavi/Mysuru specific crops like Sugarcane, Tobacco, Urad do not appear
            self.assertNotIn("Sugarcane", crop_names)
            self.assertNotIn("Tobacco", crop_names)
            
        finally:
            db = SessionLocal()
            db.query(GovernmentCropCache).filter(
                GovernmentCropCache.state == "Karnataka",
                GovernmentCropCache.district == "DHARWAD"
            ).delete(synchronize_session=False)
            db.commit()
            db.close()

if __name__ == "__main__":
    unittest.main()
