import os
import unittest
import numpy as np
import cv2
import app.services.crop_model

from app.services.crop_model import predict_crop_and_stage, _CENTROIDS

class TestCropClassifier(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Create temp folder for test images
        cls.temp_dir = os.path.abspath("./test_images_temp")
        os.makedirs(cls.temp_dir, exist_ok=True)
        
        cls.green_img_path = os.path.join(cls.temp_dir, "test_vegetative.png")
        cls.brown_img_path = os.path.join(cls.temp_dir, "test_germination.png")
        cls.yellow_img_path = os.path.join(cls.temp_dir, "test_maturity.png")
        cls.grey_img_path = os.path.join(cls.temp_dir, "test_non_agri.png")

        # Create empty placeholder files
        for p in [cls.green_img_path, cls.brown_img_path, cls.yellow_img_path, cls.grey_img_path]:
            with open(p, "w") as f:
                f.write("placeholder")

        # Mock extract_features
        cls.original_extract_features = app.services.crop_model.extract_features
        
        def mock_extract_features(path: str) -> np.ndarray:
            if path == cls.green_img_path:
                # Sugarcane Vegetative
                return np.array(_CENTROIDS[("Sugarcane", "Vegetative")], dtype=np.float32)
            elif path == cls.brown_img_path:
                # Cotton Germination
                return np.array(_CENTROIDS[("Cotton", "Germination")], dtype=np.float32)
            elif path == cls.yellow_img_path:
                # Rice Maturity
                return np.array(_CENTROIDS[("Rice", "Maturity")], dtype=np.float32)
            else:
                # Non-Agri / Grey
                return np.zeros(14, dtype=np.float32)

        app.services.crop_model.extract_features = mock_extract_features

    @classmethod
    def tearDownClass(cls):
        # Restore mock
        app.services.crop_model.extract_features = cls.original_extract_features
        
        # Clean up files
        for filename in ["test_vegetative.png", "test_germination.png", "test_maturity.png", "test_non_agri.png"]:
            path = os.path.join(cls.temp_dir, filename)
            if os.path.exists(path):
                os.remove(path)
        if os.path.exists(cls.temp_dir):
            os.rmdir(cls.temp_dir)

    def test_vegetative_classification(self):
        """Verify lush green image is classified in the Vegetative stage with high confidence"""
        res = predict_crop_and_stage(self.green_img_path)
        print(f"[TEST Vegetative] Result: {res}")
        self.assertEqual(res["crop_name"], "Sugarcane")
        self.assertEqual(res["growth_stage"], "Vegetative")
        self.assertGreaterEqual(res["crop_confidence"], 60.0)

    def test_germination_classification(self):
        """Verify soil brown image is classified in the Germination stage with high confidence"""
        res = predict_crop_and_stage(self.brown_img_path)
        print(f"[TEST Germination] Result: {res}")
        self.assertEqual(res["crop_name"], "Cotton")
        self.assertEqual(res["growth_stage"], "Germination")
        self.assertGreaterEqual(res["crop_confidence"], 60.0)

    def test_maturity_classification(self):
        """Verify golden/yellow image is classified in the Maturity stage with high confidence"""
        res = predict_crop_and_stage(self.yellow_img_path)
        print(f"[TEST Maturity] Result: {res}")
        self.assertEqual(res["crop_name"], "Rice")
        self.assertEqual(res["growth_stage"], "Maturity")
        self.assertGreaterEqual(res["crop_confidence"], 60.0)

    def test_non_agri_low_confidence(self):
        """Verify a non-agricultural image is correctly flagged as Unknown and low confidence"""
        res = predict_crop_and_stage(self.grey_img_path)
        print(f"\n[TEST Non-Agri] Result: {res}")
        self.assertEqual(res["crop_name"], "Unknown")
        self.assertEqual(res["growth_stage"], "Needs better image")
        self.assertEqual(res["crop_confidence"], 0.0)
        self.assertEqual(res["stage_confidence"], 0.0)
        self.assertEqual(res["health_status"], "Unhealthy")
        self.assertEqual(res["disease"], "Non-Agricultural/Unknown")


if __name__ == "__main__":
    unittest.main()
