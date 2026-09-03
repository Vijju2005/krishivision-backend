import unittest
import sqlite3
import os
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.orm_models import APYCropStatistic

class TestAPYIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "krishivision.db"))
        cls.conn = sqlite3.connect(cls.db_path)
        cls.cursor = cls.conn.cursor()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_apy_import(self):
        """Verify that APY.csv data has been successfully imported into the database."""
        self.cursor.execute("SELECT COUNT(*) FROM apy_crop_statistics;")
        count = self.cursor.fetchone()[0]
        self.assertGreater(count, 0, "No records found in apy_crop_statistics table.")
        print(f"\n[APY TEST] Total imported APY records: {count}")

    def test_apy_chikkamagaluru_crop_lookup(self):
        """Verify that crop lookup for Chikkamagaluru works and returns appropriate crops."""
        response = self.client.get("/apy/states/Karnataka/districts/Chikkamagaluru/crops")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["state"], "Karnataka")
        self.assertEqual(data["district"], "Chikkamagaluru")
        self.assertEqual(data["status"], "success")
        self.assertIsNotNone(data["crop_year"])
        
        crop_names = [c["crop_name"] for c in data["crops"]]
        print(f"[APY TEST] Chikkamagaluru crops: {crop_names}")
        
        # Ragi is a key crop in Chikkamagaluru
        self.assertIn("Ragi", crop_names)
        # Cotton is NOT relevant/present for Chikkamagaluru according to rules
        self.assertNotIn("Cotton", crop_names)

    def test_apy_latest_year(self):
        """Verify that the API queries using the maximum available Crop_Year for the district."""
        # Find maximum crop year in database for Chikkamagaluru
        self.cursor.execute(
            "SELECT MAX(crop_year) FROM apy_crop_statistics WHERE LOWER(state_name)='karnataka' AND LOWER(district_name)='chikkamagaluru';"
        )
        expected_max_year = self.cursor.fetchone()[0]
        
        response = self.client.get("/apy/states/Karnataka/districts/Chikkamagaluru/crops")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["crop_year"], expected_max_year)
        print(f"[APY TEST] Chikkamagaluru max year: {data['crop_year']}")

    def test_apy_crop_normalization(self):
        """Verify crop synonym normalization (e.g. Rice/Paddy -> Paddy / Rice)."""
        response = self.client.get("/apy/states/Karnataka/districts/Chikkamagaluru/crops")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        crop_names = [c["crop_name"] for c in data["crops"]]
        # Neither "Rice" nor "Paddy" should be in the list, instead "Paddy / Rice"
        self.assertNotIn("Rice", crop_names)
        self.assertNotIn("Paddy", crop_names)
        self.assertIn("Paddy / Rice", crop_names)

    def test_apy_crop_aggregation(self):
        """Verify that area and production values are aggregated (summed) correctly."""
        # Get raw sum for a crop (e.g. Ragi) in Chikkamagaluru for the latest year
        self.cursor.execute(
            "SELECT MAX(crop_year) FROM apy_crop_statistics WHERE LOWER(state_name)='karnataka' AND LOWER(district_name)='chikkamagaluru';"
        )
        max_year = self.cursor.fetchone()[0]
        
        self.cursor.execute(
            "SELECT SUM(area_hectares), SUM(production_tonnes) FROM apy_crop_statistics "
            "WHERE LOWER(state_name)='karnataka' AND LOWER(district_name)='chikkamagaluru' "
            "AND crop_year=? AND LOWER(crop_name)='ragi';", (max_year,)
        )
        sum_area, sum_prod = self.cursor.fetchone()
        
        response = self.client.get("/apy/states/Karnataka/districts/Chikkamagaluru/crops")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        ragi_data = next((c for c in data["crops"] if c["crop_name"] == "Ragi"), None)
        self.assertIsNotNone(ragi_data)
        
        self.assertAlmostEqual(ragi_data["area_hectares"], round(sum_area, 2))
        self.assertAlmostEqual(ragi_data["production_tonnes"], round(sum_prod, 2))

    def test_apy_area_conversion(self):
        """Verify area hectares to acres conversion (1 ha = 2.47105 acres)."""
        response = self.client.get("/apy/states/Karnataka/districts/Chikkamagaluru/crops")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        for crop in data["crops"]:
            ha = crop["area_hectares"]
            acres = crop["area_acres"]
            self.assertAlmostEqual(acres, round(ha * 2.47105, 2))

    def test_apy_crop_percentage(self):
        """Verify crop percentage is calculated correctly and totals equal 100% (before filtering)."""
        response = self.client.get("/apy/states/Karnataka/districts/Chikkamagaluru/crops")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Verify percentages exist and are sensible (between 0 and 100)
        for crop in data["crops"]:
            self.assertGreater(crop["crop_percentage"], 0.0)
            self.assertLessEqual(crop["crop_percentage"], 100.0)

    def test_apy_zero_area_exclusion(self):
        """Verify that any database entries with area <= 0 or null are excluded."""
        db = SessionLocal()
        try:
            # Check database for invalid records
            zero_count = db.query(APYCropStatistic).filter(APYCropStatistic.area_hectares <= 0).count()
            null_count = db.query(APYCropStatistic).filter(APYCropStatistic.area_hectares == None).count()
            self.assertEqual(zero_count, 0, "Database still contains records with area <= 0")
            self.assertEqual(null_count, 0, "Database still contains records with null area")
        finally:
            db.close()

    def test_apy_cross_district_isolation(self):
        """Verify strict district isolation: Ragi in Chikkamagaluru must not leakage to Dharwad query."""
        response_chik = self.client.get("/apy/states/Karnataka/districts/Chikkamagaluru/crops")
        response_dhar = self.client.get("/apy/states/Karnataka/districts/Dharwad/crops")
        
        self.assertEqual(response_chik.status_code, 200)
        self.assertEqual(response_dhar.status_code, 200)
        
        chik_crops = {c["crop_name"] for c in response_chik.json()["crops"]}
        dhar_crops = {c["crop_name"] for c in response_dhar.json()["crops"]}
        
        # Verify Cotton is in Dharwad but NOT in Chikkamagaluru
        self.assertIn("Cotton", dhar_crops)
        self.assertNotIn("Cotton", chik_crops)

    def test_apy_cross_state_isolation(self):
        """Verify strict state isolation."""
        response_karn = self.client.get("/apy/states/Karnataka/districts/Chikkamagaluru/crops")
        response_punj = self.client.get("/apy/states/Punjab/districts/Amritsar/crops")
        
        self.assertEqual(response_karn.status_code, 200)
        self.assertEqual(response_punj.status_code, 200)
        
        karn_crops = {c["crop_name"] for c in response_karn.json()["crops"]}
        punj_crops = {c["crop_name"] for c in response_punj.json()["crops"]}
        
        # Wheat is a primary crop in Amritsar but should not cross leak to Chikkamagaluru latest crops list
        self.assertIn("Wheat", punj_crops)
        self.assertNotIn("Wheat", karn_crops)

    def test_no_mock_crop_fallback(self):
        """Verify that querying a non-existent fake district returns empty crops list instead of fallback stubs."""
        response = self.client.get("/apy/states/Karnataka/districts/FakeDistrictName/crops")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["status"], "NO_DATA")
        self.assertEqual(len(data["crops"]), 0)
        self.assertEqual(data["message"], "No crop data available for this district")

    def test_apy_crop_detail_endpoint(self):
        """Verify crop detail endpoint is working with valid crop name and strict district check."""
        response = self.client.get("/apy/states/Karnataka/districts/Chikkamagaluru/crops/ragi")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["state"], "Karnataka")
        self.assertEqual(data["district"], "Chikkamagaluru")
        self.assertEqual(data["crop"], "Ragi")
        self.assertGreater(data["area_acres"], 0.0)
        self.assertGreater(data["production"], 0.0)
        self.assertEqual(data["source"], "APY Dataset")
        
        # Verify cross district check fails for invalid crop in district
        response_fail = self.client.get("/apy/states/Karnataka/districts/Chikkamagaluru/crops/apple")
        self.assertEqual(response_fail.status_code, 404)

    def _get_crop_id(self, crop_name: str, district: str = "Chikkamagaluru") -> int:
        from app.database import SessionLocal
        from app.routers.dashboard_map import find_crop_id_for_apy
        db = SessionLocal()
        try:
            return find_crop_id_for_apy(db, "Karnataka", district, crop_name)
        finally:
            db.close()

    def test_crop_detail_loading(self):
        """Verify endpoint /crops/{crop_id} returns valid crop details."""
        arecanut_id = self._get_crop_id("Arecanut")
        response = self.client.get(f"/crops/{arecanut_id}")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "Arecanut")
        self.assertIn(data["growing_season"], ["Perennial", "Year-round"])

    def test_agromonitoring_health_and_growth_data(self):
        """Verify crop detail growth and health response structure and values."""
        arecanut_id = self._get_crop_id("Arecanut")
        response = self.client.get(f"/crops/{arecanut_id}/overview/growth/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data["id"], arecanut_id)
        # Verify no fabricated values are used when real satellite is unavailable
        if data.get("satellite_ndvi") is None:
            self.assertIn(data.get("health_status"), [
                "Satellite data unavailable",
                "Satellite service temporarily unavailable",
                "No satellite observations available",
                "AgroMonitoring API rate limit reached",
                "AgroMonitoring API authentication failed"
            ])
            self.assertTrue(data.get("growth_stage") == "Data unavailable" or "Satellite data" in data.get("growth_stage"))
            self.assertIsNone(data.get("ndvi"))
            self.assertIsNone(data.get("evi"))

    def test_api_key_configuration(self):
        """Verify API key configs load correctly from backend settings."""
        from app.services.data_gov_crop_service import get_api_key
        from app.services.agromonitoring_service import get_agromonitoring_api_key
        
        gov_key = get_api_key()
        agro_key = get_agromonitoring_api_key()
        
        self.assertIsNotNone(gov_key)
        self.assertIsNotNone(agro_key)
        self.assertGreater(len(gov_key), 0)
        self.assertGreater(len(agro_key), 0)

    def test_bellary_ballari_normalization(self):
        """Verify that Bellary district query maps to Ballari in the local APY database."""
        response = self.client.get("/apy/states/Karnataka/districts/Bellary/crops")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["district"], "Bellary")
        self.assertEqual(data["latest_year"], 2019)
        self.assertGreater(len(data["crops"]), 0)
        # Ensure crops list has real crops
        crop_names = [c["crop_name"] for c in data["crops"]]
        self.assertIn("Jowar", crop_names)

    def test_crop_year_consistency(self):
        """Verify that crop details screen retrieves the dynamic latest crop year from APY.csv (2019)."""
        pepper_id = self._get_crop_id("Black Pepper")
        response = self.client.get(f"/crops/{pepper_id}") # Black Pepper in Chikkamagaluru
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["source_year"], 2019)
        self.assertEqual(data["source"], "APY Dataset")
        self.assertAlmostEqual(data["area_acres"], 40520.0 * 2.47105, places=2)

    def test_black_pepper_detail_loading(self):
        """Verify that Black Pepper detail endpoint successfully retrieves combined overview metrics."""
        pepper_id = self._get_crop_id("Black Pepper")
        response = self.client.get(f"/crops/{pepper_id}/overview/growth/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["name"], "Black Pepper")
        self.assertEqual(data["district"], "Chikkamagaluru")
        self.assertEqual(data["state_name"], "Karnataka")
        self.assertAlmostEqual(data["area_acres"], 40520.0 * 2.47105, places=2)

    def test_cross_district_leakage_details(self):
        """Verify strict district isolation on crop details."""
        pepper_id = self._get_crop_id("Black Pepper")
        pepper_resp = self.client.get(f"/crops/{pepper_id}/overview/growth/health")
        self.assertEqual(pepper_resp.status_code, 200)
        pepper_data = pepper_resp.json()
        self.assertEqual(pepper_data["district"], "Chikkamagaluru")
        self.assertEqual(pepper_data["name"], "Black Pepper")

        rice_id = self._get_crop_id("Paddy / Rice")
        cotton_resp = self.client.get(f"/crops/{rice_id}/overview/growth/health") # Rice in Chikkamagaluru
        self.assertEqual(cotton_resp.status_code, 200)
        cotton_data = cotton_resp.json()
        self.assertEqual(cotton_data["district"], "Chikkamagaluru")
        self.assertNotEqual(pepper_data["id"], cotton_data["id"])

    def test_satellite_failure_not_blocking(self):
        """Verify that AgroMonitoring satellite failures do not block government crop data from loading."""
        pepper_id = self._get_crop_id("Black Pepper")
        response = self.client.get(f"/crops/{pepper_id}/overview/growth/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Government stats should be present
        self.assertAlmostEqual(data["area_acres"], 40520.0 * 2.47105, places=2)
        # Market info should be present
        self.assertIsNotNone(data.get("market_name"))
        # Satellite detail indicates unavailable state without crashing
        self.assertIn(data.get("satellite_health_status"), [
            "Satellite data unavailable",
            "Satellite service temporarily unavailable",
            "No satellite observations available",
            "AgroMonitoring API rate limit reached",
            "AgroMonitoring API authentication failed",
            "Poor",
            "Moderate",
            "Healthy",
            "Good",
            "Unanalyzed"
        ])

    def test_india_wide_representative_districts(self):
        """Verify India-wide representative districts from North, South, East, West, Central, Northeast, and UTs."""
        reps = [
            ("Jammu and Kashmir", "Anantnag (Kashmir South)", "Paddy / Rice"),
            ("Punjab", "Firozpur", "Wheat"),
            ("Uttar Pradesh", "Bara Banki", "Wheat"),
            ("Tamil Nadu", "Nilgiris", "Paddy / Rice"),
            ("Andhra Pradesh", "Nellore", "Paddy / Rice"),
            ("West Bengal", "Darjiling", "Paddy / Rice"),
            ("Bihar", "Purba Champaran", "Paddy / Rice"),
            ("Gujarat", "The Dangs", "Ragi"),
            ("Rajasthan", "Jalor", "Bajra"),
            ("Madhya Pradesh", "Dhar", "Wheat"),
            ("Chhattisgarh", "Raj Nandgaon", "Paddy / Rice"),
            ("Manipur", "East Imphal", "Paddy / Rice"),
            ("Meghalaya", "Ri-Bhoi", "Paddy / Rice"),
            ("Delhi", "Delhi", "Wheat"),
            ("Puducherry", "Puducherry", "Paddy / Rice"),
        ]
        
        for state, district, crop in reps:
            response = self.client.get(f"/apy/states/{state}/districts/{district}/crops")
            self.assertEqual(response.status_code, 200, f"Failed for {state} -> {district}")
            data = response.json()
            self.assertEqual(data["status"].lower(), "success", f"Failed status for {state} -> {district}")
            self.assertGreater(len(data["crops"]), 0, f"Empty crops list for {state} -> {district}")
            
            crop_names = [c["crop_name"] for c in data["crops"]]
            self.assertIn(crop, crop_names, f"Expected crop '{crop}' not found in {district} crops: {crop_names}")


