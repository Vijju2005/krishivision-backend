import os
import unittest
import hashlib
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.models.orm_models import OTPVerification, User

TEST_DB_URL = "sqlite:///./test_krishivision_otp.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

class TestKrishiVisionOTP(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.dependency_overrides[get_db] = override_get_db
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)

    @classmethod
    def tearDownClass(cls):
        Base.metadata.drop_all(bind=engine)
        if os.path.exists("./test_krishivision_otp.db"):
            try:
                os.remove("./test_krishivision_otp.db")
            except OSError:
                pass
        app.dependency_overrides.clear()

    def setUp(self):
        # Clear database tables before each test to have isolated tests
        db = TestingSessionLocal()
        db.query(OTPVerification).delete()
        db.query(User).delete()
        db.commit()
        db.close()

    def test_invalid_phone_number(self):
        # Invalid length
        response = self.client.post("/auth/otp/request", json={"phone_number": "12345"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid Indian mobile number", response.json()["detail"])

        # Invalid start digit for Indian numbers (must start with 6-9)
        response = self.client.post("/auth/otp/request", json={"phone_number": "5555555555"})
        self.assertEqual(response.status_code, 400)
        self.assertIn("Invalid Indian mobile number", response.json()["detail"])

    def test_otp_request_and_rate_limiting(self):
        # Request OTP
        response = self.client.post("/auth/otp/request", json={"phone_number": "9876543210"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "success")

        # Rate limiting: request again immediately
        response2 = self.client.post("/auth/otp/request", json={"phone_number": "9876543210"})
        self.assertEqual(response2.status_code, 429)
        self.assertIn("Please wait", response2.json()["detail"])

    def test_otp_verification_flow(self):
        # Request OTP
        self.client.post("/auth/otp/request", json={"phone_number": "9876543210"})

        # Get plain OTP from log or db for verification
        db = TestingSessionLocal()
        otp_rec = db.query(OTPVerification).filter(OTPVerification.phone_number == "+919876543210").first()
        self.assertIsNotNone(otp_rec)
        hashed_val = otp_rec.hashed_otp
        db.close()

        # Let's override/re-generate OTP hash so we know the plain code for test verification
        # or we can inspect the db. Let's just create a known OTP entry in the DB to test verify.
        db = TestingSessionLocal()
        known_otp = "123456"
        known_hash = hashlib.sha256(known_otp.encode("utf-8")).hexdigest()
        
        # update record
        otp_rec = db.query(OTPVerification).filter(OTPVerification.phone_number == "+919876543210").first()
        otp_rec.hashed_otp = known_hash
        db.commit()
        db.close()

        # Verify with wrong OTP
        verify_resp = self.client.post("/auth/otp/verify", json={"phone_number": "9876543210", "otp": "000000"})
        self.assertEqual(verify_resp.status_code, 400)
        self.assertIn("Incorrect verification code", verify_resp.json()["detail"])

        # Verify with correct OTP
        verify_resp2 = self.client.post("/auth/otp/verify", json={"phone_number": "9876543210", "otp": "123456"})
        self.assertEqual(verify_resp2.status_code, 200)
        self.assertIn("access_token", verify_resp2.json())

        # Verify auto-registration: check if user exists
        db = TestingSessionLocal()
        user = db.query(User).filter(User.phone == "+919876543210").first()
        self.assertIsNotNone(user)
        self.assertEqual(user.full_name, "Farmer 3210")
        db.close()

    def test_otp_brute_force_prevention(self):
        # Create a verification record with attempts = 4
        db = TestingSessionLocal()
        known_otp = "123456"
        known_hash = hashlib.sha256(known_otp.encode("utf-8")).hexdigest()
        expires_at = datetime.utcnow() + timedelta(minutes=5)
        rec = OTPVerification(
            phone_number="+919876543210",
            hashed_otp=known_hash,
            expires_at=expires_at,
            attempts=4,
            is_used=False
        )
        db.add(rec)
        db.commit()
        db.close()

        # Verify with wrong OTP (this is the 5th attempt, increments attempts to 5)
        resp = self.client.post("/auth/otp/verify", json={"phone_number": "9876543210", "otp": "000000"})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Remaining attempts: 0", resp.json()["detail"])

        # Try to verify again (this is the 6th attempt, exceeds 5)
        resp2 = self.client.post("/auth/otp/verify", json={"phone_number": "9876543210", "otp": "123456"})
        self.assertEqual(resp2.status_code, 400)
        self.assertIn("Maximum verification attempts exceeded", resp2.json()["detail"])

    def test_otp_expiration(self):
        # Create an expired verification record
        db = TestingSessionLocal()
        known_otp = "123456"
        known_hash = hashlib.sha256(known_otp.encode("utf-8")).hexdigest()
        expires_at = datetime.utcnow() - timedelta(seconds=1)
        rec = OTPVerification(
            phone_number="+919876543210",
            hashed_otp=known_hash,
            expires_at=expires_at,
            attempts=0,
            is_used=False
        )
        db.add(rec)
        db.commit()
        db.close()

        # Try to verify
        resp = self.client.post("/auth/otp/verify", json={"phone_number": "9876543210", "otp": "123456"})
        self.assertEqual(resp.status_code, 400)
        self.assertIn("Verification code has expired", resp.json()["detail"])
