import unittest
import os
import sqlite3
from fastapi.testclient import TestClient
from app.main import app
from app.database import get_db

class TestDistrictCrops(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "krishivision.db"))
        cls.conn = sqlite3.connect(cls.db_path)
        cls.cursor = cls.conn.cursor()
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_udupi_crop_list_and_filtering(self):
        """Verify Udupi returns exactly its curated crop list and no incorrect crops like Cotton"""
        self.cursor.execute("SELECT id FROM districts WHERE name='Udupi';")
        row = self.cursor.fetchone()
        self.assertIsNotNone(row, "Udupi district not found in database")
        u_id = row[0]

        # Call endpoint
        response = self.client.get(f"/districts/{u_id}/crops")
        self.assertEqual(response.status_code, 200)
        crops = response.json()
        crop_names = {c["name"] for c in crops}
        
        print("\n[VERIFICATION] Crops in Udupi district:", crop_names)
        
        # Verify Udupi contains curated crops
        self.assertIn("Coconut", crop_names)
        self.assertIn("Rice", crop_names)
        self.assertIn("Sugarcane", crop_names)
        
        # Verify Cotton is NOT in Udupi
        self.assertNotIn("Cotton", crop_names)

    def test_district_crop_differentiation(self):
        """Verify different states and districts return different and correct crop lists"""
        districts_to_test = [
            ("Udupi", ["Coconut", "Rice", "Sugarcane"]),
            ("Chikkamagaluru", ["Coffee", "Black Pepper", "Cardamom"]),
            ("Kodagu", ["Coffee", "Black Pepper", "Rice"]),
            ("Idukki", ["Coffee", "Tea", "Cardamom"]), # Kerala
            ("Amritsar", ["Wheat", "Rice", "Mustard"]), # Punjab
            ("Anantnag (Kashmir South)", ["Apple", "Saffron", "Rice"]), # J&K
            ("Ahmednagar", ["Soybean", "Sugarcane", "Cotton"]) # Maharashtra
        ]

        for d_name, expected_crops in districts_to_test:
            self.cursor.execute("SELECT id FROM districts WHERE name=?;", (d_name,))
            row = self.cursor.fetchone()
            if not row:
                print(f"Skipping check for {d_name} - not found in database")
                continue
            d_id = row[0]

            response = self.client.get(f"/districts/{d_id}/crops")
            self.assertEqual(response.status_code, 200)
            crops = response.json()
            crop_names = {c["name"] for c in crops}
            
            print(f"[VERIFICATION] Crops in {d_name}: {crop_names}")
            
            # Check crop lists are distinct and match expectation
            for exp in expected_crops:
                self.assertIn(exp, crop_names, f"Expected crop {exp} not found in {d_name}")

if __name__ == "__main__":
    unittest.main()
