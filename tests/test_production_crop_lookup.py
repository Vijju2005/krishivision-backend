import unittest
import os
import sys
from fastapi.testclient import TestClient

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app
from app.database import SessionLocal
from app.services.apy_seeder import seed_apy_data_if_needed
from app.services.crop_api_service import normalize_state_name, resolve_canonical_district

class TestProductionCropLookup(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        os.environ["JWT_SECRET_KEY"] = "testsecretkey123"
        cls.client = TestClient(app)
        cls.db = SessionLocal()
        # Ensure APY data is seeded in test DB
        seed_apy_data_if_needed(cls.db)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_lakhimpur_kheri_crop_lookup(self):
        """Verify Uttar Pradesh -> Lakhimpur Kheri retrieves real APY crops."""
        response = self.client.get("/states/Uttar%20Pradesh/districts/Lakhimpur%20Kheri/crops")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertEqual(data.get("source"), "APY Dataset")
        self.assertIn("Lakhimpur", data.get("district", "") or "Kheri")
        crops = data.get("crops", [])
        self.assertGreater(len(crops), 0)
        
        crop_names = [c.get("name") for c in crops]
        self.assertIn("Sugarcane", crop_names)
        self.assertIn("Wheat", crop_names)
        
        # Verify real non-zero area_acres
        sugarcane = next(c for c in crops if c.get("name") == "Sugarcane")
        self.assertGreater(sugarcane.get("area_acres", 0), 100000.0)

    def test_sangli_crop_lookup(self):
        """Verify Maharashtra -> Sangli retrieves real APY crops."""
        response = self.client.get("/states/Maharashtra/districts/Sangli/crops")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("source"), "APY Dataset")
        self.assertGreater(len(data.get("crops", [])), 0)

    def test_dharwad_crop_lookup(self):
        """Verify Karnataka -> Dharwad retrieves real APY crops."""
        response = self.client.get("/states/Karnataka/districts/Dharwad/crops")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("source"), "APY Dataset")
        self.assertGreater(len(data.get("crops", [])), 0)

    def test_bikaner_crop_lookup(self):
        """Verify Rajasthan -> Bikaner retrieves real APY crops."""
        response = self.client.get("/states/Rajasthan/districts/Bikaner/crops")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data.get("source"), "APY Dataset")
        self.assertGreater(len(data.get("crops", [])), 0)

    def test_state_district_normalization(self):
        """Verify uppercase, lowercase, and alias state/district normalization."""
        # Lowercase
        res_lower = self.client.get("/states/uttar%20pradesh/districts/lakhimpur%20kheri/crops")
        self.assertEqual(res_lower.status_code, 200)
        
        # Uppercase
        res_upper = self.client.get("/states/UTTAR%20PRADESH/districts/LAKHIMPUR%20KHERI/crops")
        self.assertEqual(res_upper.status_code, 200)
        
        # Canonical district mapping test (Lakhimpur Kheri -> KHERI)
        canon_dist = resolve_canonical_district(self.db, "Uttar Pradesh", "Lakhimpur Kheri")
        self.assertEqual(canon_dist.upper(), "KHERI")

    def test_cache_isolation(self):
        """Verify district crop cache isolation between different states/districts."""
        res_kheri = self.client.get("/states/Uttar%20Pradesh/districts/Lakhimpur%20Kheri/crops")
        res_dharwad = self.client.get("/states/Karnataka/districts/Dharwad/crops")
        
        self.assertEqual(res_kheri.status_code, 200)
        self.assertEqual(res_dharwad.status_code, 200)
        
        crops_kheri = [c.get("name") for c in res_kheri.json().get("crops", [])]
        crops_dharwad = [c.get("name") for c in res_dharwad.json().get("crops", [])]
        
        self.assertNotEqual(crops_kheri, crops_dharwad)

    def test_invalid_district_404(self):
        """Verify non-existent district returns 404 with structured JSON response."""
        res = self.client.get("/states/Uttar%20Pradesh/districts/NonExistentDistrictXYZ/crops")
        self.assertEqual(res.status_code, 404)

if __name__ == "__main__":
    unittest.main()
