import os
import unittest
from datetime import datetime, timedelta
from jose import jwt
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.main import app
from app.database import Base, get_db
from app.services.auth import SECRET_KEY, ALGORITHM
from app.models.orm_models import User

TEST_DB_URL = "sqlite:///./test_auth_jwt.db"
engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


class TestJWTAuthentication(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        app.dependency_overrides[get_db] = override_get_db
        Base.metadata.create_all(bind=engine)
        cls.client = TestClient(app)
        
        # Seed test user
        cls.db = TestingSessionLocal()
        cls.user = User(
            full_name="JWT Tester",
            email="jwttester@example.com",
            phone="+91 9999900000",
            hashed_password="somehashedpwd",
            role="user"
        )
        cls.db.add(cls.user)
        cls.db.commit()
        cls.db.refresh(cls.user)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()
        Base.metadata.drop_all(bind=engine)
        if os.path.exists("./test_auth_jwt.db"):
            try:
                os.remove("./test_auth_jwt.db")
            except OSError:
                pass
        app.dependency_overrides.clear()

    def test_login_returns_valid_token(self):
        # Seed a login-friendly user
        from app.services.auth import hash_password
        login_user = User(
            full_name="Login Tester",
            email="logintester@example.com",
            phone="+91 9999911111",
            hashed_password=hash_password("loginpassword123"),
            role="user"
        )
        self.db.add(login_user)
        self.db.commit()

        response = self.client.post("/auth/login", json={
            "email": "logintester@example.com",
            "password": "loginpassword123"
        })
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("access_token", data)

    def test_valid_jwt_access_auth_me(self):
        # Generate valid token
        expire = datetime.utcnow() + timedelta(minutes=15)
        valid_token = jwt.encode({"sub": str(self.user.id), "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)
        
        response = self.client.get("/auth/me", headers={"Authorization": f"Bearer {valid_token}"})
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["email"], "jwttester@example.com")

    def test_expired_jwt_returns_401(self):
        # Generate expired token
        expire = datetime.utcnow() - timedelta(minutes=10)
        expired_token = jwt.encode({"sub": str(self.user.id), "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)
        
        response = self.client.get("/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Invalid or expired token")

    def test_invalid_jwt_signature_returns_401(self):
        # Generate token with wrong secret
        expire = datetime.utcnow() + timedelta(minutes=15)
        invalid_token = jwt.encode({"sub": str(self.user.id), "exp": expire}, "wrong_secret_key_123", algorithm=ALGORITHM)
        
        response = self.client.get("/auth/me", headers={"Authorization": f"Bearer {invalid_token}"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Invalid or expired token")

    def test_missing_jwt_returns_401(self):
        response = self.client.get("/auth/me")
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Missing or invalid Authorization header")

    def test_malformed_jwt_returns_401(self):
        response = self.client.get("/auth/me", headers={"Authorization": "Bearer malformed_token_string"})
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json()["detail"], "Invalid or expired token")

    def test_protected_analysis_history_with_valid_token(self):
        expire = datetime.utcnow() + timedelta(minutes=15)
        valid_token = jwt.encode({"sub": str(self.user.id), "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)
        
        response = self.client.get("/analysis/history", headers={"Authorization": f"Bearer {valid_token}"})
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)


if __name__ == "__main__":
    unittest.main()
