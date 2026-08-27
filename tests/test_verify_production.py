import os
import io
import time
import unittest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db

# Use a separate test database URL
TEST_DB_URL = "sqlite:///./test_krishivision_production.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


class TestProductionVerification(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.dependency_overrides[get_db] = override_get_db
        # 1. Clean Database Setup: drop existing and create fresh tables
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        # Clean up database and remove db file
        Base.metadata.drop_all(bind=engine)
        if os.path.exists("./test_krishivision_production.db"):
            try:
                os.remove("./test_krishivision_production.db")
            except OSError:
                pass
        app.dependency_overrides.clear()

    def test_01_swagger_docs(self):
        """Verify Swagger/OpenAPI documentation endpoint is active"""
        response = self.client.get("/docs")
        self.assertEqual(response.status_code, 200)
        self.assertIn("swagger-ui", response.text.lower())

    def test_02_e2e_user_flow_and_rbac(self):
        """Verify complete end-to-end user flow, JWT auth, input validation, and RBAC"""

        # A. Register first user (should automatically get 'admin' role)
        admin_payload = {
            "full_name": "Admin Tester",
            "email": "admin@krishivision.com",
            "phone": "+91 9999999999",
            "password": "AdminSecurePassword123"
        }
        res = self.client.post("/auth/register", json=admin_payload)
        self.assertEqual(res.status_code, 200)
        admin_data = res.json()
        self.assertEqual(admin_data["role"], "admin")
        admin_token = admin_data["access_token"]

        # B. Register second user (should get 'user' role)
        user_payload = {
            "full_name": "User Farmer",
            "email": "farmer@krishivision.com",
            "phone": "+91 8888888888",
            "password": "FarmerSecurePassword123"
        }
        res = self.client.post("/auth/register", json=user_payload)
        self.assertEqual(res.status_code, 200)
        user_data = res.json()
        self.assertEqual(user_data["role"], "user")
        user_token = user_data["access_token"]

        # C. JWT Login Verification
        login_res = self.client.post("/auth/login", json={
            "email": "farmer@krishivision.com",
            "password": "FarmerSecurePassword123"
        })
        self.assertEqual(login_res.status_code, 200)
        self.assertIn("access_token", login_res.json())

        # JWT Negative testing (wrong password)
        login_fail = self.client.post("/auth/login", json={
            "email": "farmer@krishivision.com",
            "password": "WrongPassword123"
        })
        self.assertEqual(login_fail.status_code, 401)

        # JWT protected route verification without token
        protected_fail = self.client.get("/analysis/history")
        self.assertEqual(protected_fail.status_code, 401)

        # D. Role-Based Access Control (RBAC) Verification
        # User tries to access admin stats -> should return 403 Forbidden
        rbac_fail = self.client.get("/admin/stats", headers={"Authorization": f"Bearer {user_token}"})
        self.assertEqual(rbac_fail.status_code, 403)
        self.assertEqual(rbac_fail.json()["detail"], "Forbidden. Admin privilege required.")

        # Admin accesses admin stats -> should succeed
        rbac_success = self.client.get("/admin/stats", headers={"Authorization": f"Bearer {admin_token}"})
        self.assertEqual(rbac_success.status_code, 200)
        stats = rbac_success.json()
        self.assertEqual(stats["total_users"], 2)

        # E. Upload Image E2E (Multi-part file upload)
        from PIL import Image
        img = Image.new("RGB", (100, 100), color="green")
        dummy_file = io.BytesIO()
        img.save(dummy_file, format="PNG")
        dummy_file.seek(0)
        
        upload_res = self.client.post(
            "/analysis/upload",
            headers={"Authorization": f"Bearer {user_token}"},
            files={"file": ("test_satellite.png", dummy_file, "image/png")}
        )
        self.assertEqual(upload_res.status_code, 200)
        upload_data = upload_res.json()
        self.assertIn("job_id", upload_data)
        job_id = upload_data["job_id"]

        # F. Process / Status check E2E
        status_res = self.client.get(
            f"/analysis/{job_id}/status",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        self.assertEqual(status_res.status_code, 200)
        self.assertIn("status", status_res.json())

        # G. Results check E2E
        time.sleep(5.1)
        # Check status again to verify it has transitioned to completed
        status_res_after = self.client.get(
            f"/analysis/{job_id}/status",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        self.assertEqual(status_res_after.status_code, 200)
        self.assertEqual(status_res_after.json()["status"], "completed")

        results_res = self.client.get(
            f"/analysis/{job_id}/results",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        self.assertEqual(results_res.status_code, 200)
        results = results_res.json()
        self.assertIsNotNone(results["crop"])
        self.assertIsNotNone(results["avg_ndvi"])

        # H. Generate and Download PDF Report E2E
        pdf_res = self.client.get(
            f"/analysis/{job_id}/report",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        self.assertEqual(pdf_res.status_code, 200)
        self.assertEqual(pdf_res.headers["content-type"], "application/pdf")
        self.assertTrue(len(pdf_res.content) > 1000) # PDF should contain data

        # I. Fetch History E2E
        history_res = self.client.get(
            "/analysis/history",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        self.assertEqual(history_res.status_code, 200)
        history = history_res.json()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["job_id"], job_id)

        # J. Delete Analysis History Record E2E
        delete_res = self.client.delete(
            f"/analysis/{job_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        self.assertEqual(delete_res.status_code, 200)
        self.assertEqual(delete_res.json()["status"], "success")

        # K. Verify history is clean after deletion
        history_res_after = self.client.get(
            "/analysis/history",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        self.assertEqual(history_res_after.status_code, 200)
        self.assertEqual(len(history_res_after.json()), 0)


if __name__ == "__main__":
    unittest.main()
