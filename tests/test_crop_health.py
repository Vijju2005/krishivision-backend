import unittest
from app.services.agromonitoring_service import classify_crop_health_score

class TestCropHealthClassification(unittest.TestCase):
    def test_good_metrics_returns_good(self):
        """Verify that high NDVI, EVI, and NDWI result in a 'Good' health status classification."""
        # NDVI=0.78, EVI=0.72, NDWI=0.45
        status, score = classify_crop_health_score(ndvi=0.78, evi=0.72, ndwi=0.45)
        self.assertEqual(status, "Good")
        self.assertGreaterEqual(score, 75)
        print(f"\n[Health Test] Good Metrics: Score={score}, Status={status}")

    def test_moderate_metrics_returns_moderate(self):
        """Verify that mid-range NDVI, EVI, and NDWI result in a 'Moderate' health status classification."""
        # NDVI=0.52, EVI=0.48, NDWI=0.10
        status, score = classify_crop_health_score(ndvi=0.52, evi=0.48, ndwi=0.10)
        self.assertEqual(status, "Moderate")
        self.assertTrue(50 <= score < 75)
        print(f"[Health Test] Moderate Metrics: Score={score}, Status={status}")

    def test_poor_metrics_returns_poor(self):
        """Verify that low NDVI, EVI, and NDWI result in a 'Poor' health status classification."""
        # NDVI=0.25, EVI=0.20, NDWI=-0.25
        status, score = classify_crop_health_score(ndvi=0.25, evi=0.20, ndwi=-0.25)
        self.assertEqual(status, "Poor")
        self.assertLess(score, 50)
        print(f"[Health Test] Poor Metrics: Score={score}, Status={status}")

    def test_no_observation_returns_unavailable(self):
        """Verify that missing or invalid NDVI values result in a 'Satellite data unavailable' status."""
        status, score = classify_crop_health_score(ndvi=None)
        self.assertEqual(status, "Satellite data unavailable")
        self.assertEqual(score, 0)

        status_zero, score_zero = classify_crop_health_score(ndvi=0.0)
        self.assertEqual(status_zero, "Satellite data unavailable")
        self.assertEqual(score_zero, 0)

        status_neg, score_neg = classify_crop_health_score(ndvi=-0.1)
        self.assertEqual(status_neg, "Satellite data unavailable")
        self.assertEqual(score_neg, 0)
        print(f"[Health Test] No Observation: Score={score}, Status={status}")

    def test_different_crops_receive_different_classifications(self):
        """Verify that two crops with different metrics receive distinct health classifications."""
        # Crop A (Bajra) has good metrics
        status_a, score_a = classify_crop_health_score(ndvi=0.82, evi=0.75, ndwi=0.38)
        # Crop B (Soybean) has poor metrics
        status_b, score_b = classify_crop_health_score(ndvi=0.31, evi=0.25, ndwi=-0.12)

        self.assertEqual(status_a, "Good")
        self.assertEqual(status_b, "Poor")
        self.assertNotEqual(status_a, status_b)
        print(f"[Health Test] Multi-Crop: Crop A={status_a} ({score_a}), Crop B={status_b} ({score_b})")

if __name__ == "__main__":
    unittest.main()
