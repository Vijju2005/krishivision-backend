import os
import unittest
import json
import urllib.error
from unittest.mock import patch, MagicMock
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.orm_models import District, State, Crop, CropMaster, AgroMonitoringPolygon, SatelliteAnalysisCache
from app.services.agromonitoring_service import (
    create_or_get_polygon,
    fetch_satellite_indices_and_images,
    fetch_ndvi_history,
    get_agromonitoring_api_key,
    calculate_centroid,
    extract_flat_coordinates
)

TEST_DB_URL = "sqlite:///./test_agromonitoring.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class TestAgroMonitoringIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        Base.metadata.create_all(bind=engine)
        cls.db = TestingSessionLocal()
        
        # Seed test state and district
        cls.state = State(name="Karnataka", boundary_geojson={"type": "Polygon", "coordinates": [[[74.0, 12.0], [77.0, 12.0], [77.0, 15.0], [74.0, 15.0], [74.0, 12.0]]]})
        cls.db.add(cls.state)
        cls.db.commit()
        cls.db.refresh(cls.state)
        
        # Large district boundary (>3000 hectares)
        large_coords = [[[75.0, 15.0], [75.5, 15.0], [75.5, 15.5], [75.0, 15.5], [75.0, 15.0]]]
        cls.district = District(
            state_id=cls.state.id,
            name="Dharwad",
            boundary_geojson={"type": "Polygon", "coordinates": large_coords},
            monitored_area_acres=100000.0
        )
        cls.db.add(cls.district)
        cls.db.commit()
        cls.db.refresh(cls.district)
        
        cls.crop_master = CropMaster(name="Cotton")
        cls.db.add(cls.crop_master)
        cls.db.commit()
        cls.db.refresh(cls.crop_master)
        
        cls.crop = Crop(
            district_id=cls.district.id,
            crop_master_id=cls.crop_master.id,
            boundary_geojson={"type": "Polygon", "coordinates": large_coords}
        )
        cls.db.add(cls.crop)
        cls.db.commit()

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        Base.metadata.drop_all(bind=engine)
        if os.path.exists("./test_agromonitoring.db"):
            try:
                os.remove("./test_agromonitoring.db")
            except OSError:
                pass

    def setUp(self):
        # Clear tables before each test
        self.db.query(AgroMonitoringPolygon).delete()
        self.db.query(SatelliteAnalysisCache).delete()
        self.db.commit()

    @patch("app.services.agromonitoring_service.get_agromonitoring_api_key", return_value="TEST_AGROMONITORING_KEY")
    @patch("urllib.request.urlopen")
    def test_agromonitoring_auth_failure(self, mock_urlopen, mock_key):
        # Mock 401/403 authentication error
        resp = MagicMock()
        resp.read.return_value = b'{"message": "Unauthorized"}'
        err = urllib.error.HTTPError("http://test.api", 401, "Unauthorized", resp.headers, resp)
        mock_urlopen.side_effect = err
        
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as ctx:
            create_or_get_polygon(self.db, "Karnataka", "Dharwad", "Cotton")
        self.assertEqual(ctx.exception.status_code, 503)
        self.assertEqual(ctx.exception.detail, "AgroMonitoring API authentication failed")

    @patch("app.services.agromonitoring_service.get_agromonitoring_api_key", return_value="TEST_AGROMONITORING_KEY")
    @patch("urllib.request.urlopen")
    def test_agromonitoring_api_rate_limiting(self, mock_urlopen, mock_key):
        # Mock 429 rate limiting error
        resp = MagicMock()
        resp.read.return_value = b'{"message": "Rate limit exceeded"}'
        err = urllib.error.HTTPError("http://test.api", 429, "Too Many Requests", resp.headers, resp)
        mock_urlopen.side_effect = err
        
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as ctx:
            create_or_get_polygon(self.db, "Karnataka", "Dharwad", "Cotton")
        self.assertEqual(ctx.exception.status_code, 429)
        self.assertEqual(ctx.exception.detail, "AgroMonitoring API rate limit reached")

    @patch("app.services.agromonitoring_service.get_agromonitoring_api_key", return_value="TEST_AGROMONITORING_KEY")
    @patch("urllib.request.urlopen")
    def test_agromonitoring_api_timeout(self, mock_urlopen, mock_key):
        # Mock timeout error
        mock_urlopen.side_effect = Exception("timeout")
        
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as ctx:
            create_or_get_polygon(self.db, "Karnataka", "Dharwad", "Cotton")
        self.assertEqual(ctx.exception.status_code, 503)
        self.assertEqual(ctx.exception.detail, "Satellite service temporarily unavailable")

    @patch("os.getenv")
    def test_api_key_security(self, mock_getenv):
        # Verify the API key is not printed or returned in exception details
        mock_getenv.side_effect = lambda key, default="": "TEST_AGROMONITORING_KEY" if key == "AGROMONITORING_API_KEY" else default
        
        # Test key redaction in logging helper
        from app.services.agromonitoring_service import make_agromonitoring_request
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as ctx:
            # Passes invalid URL containing API key to trigger request error
            make_agromonitoring_request("http://api.agromonitoring.com/agro/1.0/polygons?appid=TEST_AGROMONITORING_KEY", method="POST")
        self.assertNotIn("TEST_AGROMONITORING_KEY", str(ctx.exception.detail))

    @patch("app.services.agromonitoring_service.get_agromonitoring_api_key", return_value="TEST_AGROMONITORING_KEY")
    @patch("urllib.request.urlopen")
    def test_polygon_caching_and_scaling(self, mock_urlopen, mock_key):
        # Mock success creation response
        resp = MagicMock()
        resp.getcode.return_value = 201
        resp.read.return_value = b'{"id": "poly12345", "area": 1000.0}'
        mock_urlopen.return_value.__enter__.return_value = resp
        
        # 1. First call creates the polygon on AgroMonitoring
        poly_id = create_or_get_polygon(self.db, "Karnataka", "Dharwad", "Cotton")
        self.assertEqual(poly_id, "poly12345")
        
        # Verify it created a record in DB
        db_rec = self.db.query(AgroMonitoringPolygon).filter_by(polygon_id="poly12345").first()
        self.assertIsNotNone(db_rec)
        self.assertEqual(db_rec.district, "Dharwad")
        self.assertEqual(db_rec.crop, "Cotton")
        
        # Verify coordinates were downscaled to ~1000 hectares square centered on centroid
        geojson = db_rec.geojson
        coords = geojson["geometry"]["coordinates"][0]
        # Dharwad centroid is around (75.25, 15.25)
        # Bounding box width/height should be 0.028 degrees
        width = abs(coords[1][0] - coords[0][0])
        self.assertAlmostEqual(width, 0.028, places=4)
        
        # 2. Second call should retrieve it from local cache (urlopen should not be called again)
        mock_urlopen.reset_mock()
        cached_poly_id = create_or_get_polygon(self.db, "Karnataka", "Dharwad", "Cotton")
        self.assertEqual(cached_poly_id, "poly12345")
        mock_urlopen.assert_not_called()

    @patch("app.services.agromonitoring_service.get_agromonitoring_api_key", return_value="TEST_AGROMONITORING_KEY")
    @patch("urllib.request.urlopen")
    def test_ndvi_retrieval_and_satellite_cache(self, mock_urlopen, mock_key):
        # Mock responses:
        # 1. create_or_get_polygon (not needed if we seed)
        poly = AgroMonitoringPolygon(state="Karnataka", district="Dharwad", crop="Cotton", polygon_id="poly999")
        self.db.add(poly)
        self.db.commit()
        
        # Mock urlopen calls:
        # Call 1: Search images -> returns scene array
        # Call 2: Stats ndvi -> returns stats object
        # Call 3: Stats evi -> returns stats object
        # Call 4-7: stats for evi2, ndwi, nri, dswi
        
        resp_search = MagicMock()
        resp_search.getcode.return_value = 200
        resp_search.read.return_value = b'''
        [
            {
                "dt": 1724000000,
                "type": "s2",
                "cl": 1.5,
                "image": {
                    "truecolor": "http://api.agromonitoring.com/tile/truecolor",
                    "falsecolor": "http://api.agromonitoring.com/tile/falsecolor"
                },
                "stats": {
                    "ndvi": "https://api.agromonitoring.com/stats/ndvi",
                    "evi": "https://api.agromonitoring.com/stats/evi",
                    "evi2": "https://api.agromonitoring.com/stats/evi2",
                    "ndwi": "https://api.agromonitoring.com/stats/ndwi",
                    "nri": "https://api.agromonitoring.com/stats/nri",
                    "dswi": "https://api.agromonitoring.com/stats/dswi"
                }
            }
        ]
        '''
        resp_stats = MagicMock()
        resp_stats.getcode.return_value = 200
        resp_stats.read.return_value = b'{"mean": 0.72, "median": 0.73, "min": 0.35, "max": 0.88, "std": 0.08, "p25": 0.68, "p75": 0.78}'
        
        mock_urlopen.side_effect = [
            MagicMock(__enter__=MagicMock(return_value=resp_search)), # image search
            MagicMock(__enter__=MagicMock(return_value=resp_stats)),  # ndvi stats
            MagicMock(__enter__=MagicMock(return_value=resp_stats)),  # evi stats
            MagicMock(__enter__=MagicMock(return_value=resp_stats)),  # evi2 stats
            MagicMock(__enter__=MagicMock(return_value=resp_stats)),  # ndwi stats
            MagicMock(__enter__=MagicMock(return_value=resp_stats)),  # nri stats
            MagicMock(__enter__=MagicMock(return_value=resp_stats))   # dswi stats
        ]
        
        # Run retrieval
        data = fetch_satellite_indices_and_images(self.db, "Karnataka", "Dharwad", "Cotton")
        self.assertEqual(data["polygon_id"], "poly999")
        self.assertEqual(data["ndvi"], 0.72)
        self.assertEqual(data["evi"], 0.72)
        self.assertEqual(data["image_urls"]["truecolor"], "http://api.agromonitoring.com/tile/truecolor")
        self.assertEqual(data["statistics"]["ndvi"]["mean"], 0.72)
        
        # Verify it created a cache record
        cache_rec = self.db.query(SatelliteAnalysisCache).filter_by(polygon_id="poly999").first()
        self.assertIsNotNone(cache_rec)
        self.assertEqual(cache_rec.ndvi, 0.72)
        
        # Run fetch again (should HIT cache and not call urlopen again)
        mock_urlopen.reset_mock()
        data_cached = fetch_satellite_indices_and_images(self.db, "Karnataka", "Dharwad", "Cotton")
        self.assertEqual(data_cached["ndvi"], 0.72)
        mock_urlopen.assert_not_called()

    @patch("app.services.agromonitoring_service.get_agromonitoring_api_key", return_value="TEST_AGROMONITORING_KEY")
    @patch("urllib.request.urlopen")
    def test_missing_satellite_data(self, mock_urlopen, mock_key):
        # Seed polygon
        poly = AgroMonitoringPolygon(state="Karnataka", district="Dharwad", crop="Cotton", polygon_id="poly999")
        self.db.add(poly)
        self.db.commit()
        
        # Search returns empty list
        resp_search = MagicMock()
        resp_search.getcode.return_value = 200
        resp_search.read.return_value = b'[]'
        mock_urlopen.return_value.__enter__.return_value = resp_search
        
        from fastapi import HTTPException
        with self.assertRaises(HTTPException) as ctx:
            fetch_satellite_indices_and_images(self.db, "Karnataka", "Dharwad", "Cotton")
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertEqual(ctx.exception.detail, "Satellite data unavailable")
