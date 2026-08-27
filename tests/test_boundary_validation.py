import unittest
import os
import json
import sqlite3

class TestBoundaryValidation(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Locate the database path relative to workspace or backend folder
        cls.db_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "krishivision.db"))
        cls.conn = sqlite3.connect(cls.db_path)
        cls.cursor = cls.conn.cursor()

    @classmethod
    def tearDownClass(cls):
        cls.conn.close()

    def test_database_exists(self):
        """Verify that krishivision.db exists and has State and District tables"""
        self.assertTrue(os.path.exists(self.db_path), f"Database not found at {self.db_path}")
        
        self.cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in self.cursor.fetchall()]
        self.assertIn("states", tables)
        self.assertIn("districts", tables)
        self.assertIn("crops", tables)

    def _is_ring_closed(self, ring):
        if not ring or len(ring) < 4:
            return False
        # A ring is closed if the first coordinate matches the last coordinate
        first = ring[0]
        last = ring[-1]
        return abs(first[0] - last[0]) < 1e-6 and abs(first[1] - last[1]) < 1e-6

    def _validate_coordinates_in_india(self, ring):
        for coord in ring:
            lng, lat = coord[0], coord[1]
            # India coordinate bounds check: lon [68, 98], lat [6, 38]
            self.assertTrue(68.0 <= lng <= 98.0, f"Longitude {lng} outside India bounds [68, 98]")
            self.assertTrue(6.0 <= lat <= 38.0, f"Latitude {lat} outside India bounds [6, 38]")

    def test_state_boundaries_integrity(self):
        """Verify every state polygon/multipolygon has closed rings and valid coordinates within India bounds"""
        self.cursor.execute("SELECT id, name, boundary_geojson FROM states WHERE boundary_geojson IS NOT NULL")
        states = self.cursor.fetchall()
        self.assertGreater(len(states), 0, "No state boundaries found in database")

        for state_id, name, geom_str in states:
            geom = json.loads(geom_str)
            geom_type = geom.get("type")
            coords = geom.get("coordinates")
            
            self.assertIn(geom_type, ["Polygon", "MultiPolygon"], f"Invalid geometry type for state {name}")
            self.assertIsNotNone(coords, f"Coordinates missing for state {name}")

            if geom_type == "Polygon":
                for ring in coords:
                    self.assertTrue(self._is_ring_closed(ring), f"Unclosed ring in Polygon state: {name} (id: {state_id})")
                    self._validate_coordinates_in_india(ring)
            elif geom_type == "MultiPolygon":
                for poly in coords:
                    for ring in poly:
                        self.assertTrue(self._is_ring_closed(ring), f"Unclosed ring in MultiPolygon state: {name} (id: {state_id})")
                        self._validate_coordinates_in_india(ring)

    def test_district_boundaries_integrity(self):
        """Verify every district polygon/multipolygon has closed rings and valid coordinates within India bounds"""
        self.cursor.execute("SELECT id, name, boundary_geojson, state_id FROM districts WHERE boundary_geojson IS NOT NULL")
        districts = self.cursor.fetchall()
        self.assertGreater(len(districts), 0, "No district boundaries found in database")

        for dist_id, name, geom_str, state_id in districts:
            geom = json.loads(geom_str)
            geom_type = geom.get("type")
            coords = geom.get("coordinates")
            
            self.assertIn(geom_type, ["Polygon", "MultiPolygon"], f"Invalid geometry type for district {name}")
            self.assertIsNotNone(coords, f"Coordinates missing for district {name}")

            if geom_type == "Polygon":
                for ring in coords:
                    self.assertTrue(self._is_ring_closed(ring), f"Unclosed ring in Polygon district: {name} (id: {dist_id})")
                    self._validate_coordinates_in_india(ring)
            elif geom_type == "MultiPolygon":
                for poly in coords:
                    for ring in poly:
                        self.assertTrue(self._is_ring_closed(ring), f"Unclosed ring in MultiPolygon district: {name} (id: {dist_id})")
                        self._validate_coordinates_in_india(ring)

    def _get_center(self, geom):
        geom_type = geom.get("type")
        coords = geom.get("coordinates")
        lats, lngs = [], []
        if geom_type == "Polygon":
            for ring in coords:
                for pt in ring:
                    lngs.append(pt[0])
                    lats.append(pt[1])
        elif geom_type == "MultiPolygon":
            for poly in coords:
                for ring in poly:
                    for pt in ring:
                        lngs.append(pt[0])
                        lats.append(pt[1])
        if lats and lngs:
            return sum(lngs) / len(lngs), sum(lats) / len(lats)
        return None

    def test_district_state_containment(self):
        """Verify district center falls roughly inside India's general geographic bounding box of parent state or is nearby"""
        self.cursor.execute("""
            SELECT d.id, d.name, d.boundary_geojson, s.name, s.boundary_geojson
            FROM districts d
            JOIN states s ON d.state_id = s.id
            WHERE d.boundary_geojson IS NOT NULL AND s.boundary_geojson IS NOT NULL
        """)
        records = self.cursor.fetchall()
        self.assertGreater(len(records), 0, "No state-district joins found in database")

        for dist_id, dist_name, dist_geom_str, state_name, state_geom_str in records:
            dist_geom = json.loads(dist_geom_str)
            state_geom = json.loads(state_geom_str)
            
            dist_center = self._get_center(dist_geom)
            self.assertIsNotNone(dist_center, f"Could not determine center for district {dist_name}")
            
            # Simple bounding box overlap test to ensure state and district are in the same general region
            state_coords = []
            state_geom_type = state_geom.get("type")
            state_coords_raw = state_geom.get("coordinates")
            if state_geom_type == "Polygon":
                for ring in state_coords_raw:
                    state_coords.extend(ring)
            elif state_geom_type == "MultiPolygon":
                for poly in state_coords_raw:
                    for ring in poly:
                        state_coords.extend(ring)

            min_lng = min(pt[0] for pt in state_coords)
            max_lng = max(pt[0] for pt in state_coords)
            min_lat = min(pt[1] for pt in state_coords)
            max_lat = max(pt[1] for pt in state_coords)

            dlng, dlat = dist_center
            # We allow 1.5 degrees of buffer for geographic simplification or enclave boundaries
            self.assertTrue(min_lng - 1.5 <= dlng <= max_lng + 1.5, f"District {dist_name} longitude {dlng} is far outside state {state_name} bounds [{min_lng}, {max_lng}]")
            self.assertTrue(min_lat - 1.5 <= dlat <= max_lat + 1.5, f"District {dist_name} latitude {dlat} is far outside state {state_name} bounds [{min_lat}, {max_lat}]")

if __name__ == "__main__":
    unittest.main()
