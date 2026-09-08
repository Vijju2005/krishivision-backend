import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database import SessionLocal
from app.models.orm_models import User, Analysis, State, District, Crop, CropMaster
from app.services.auth import create_access_token

client = TestClient(app)

def setup_user_and_auth():
    db = SessionLocal()
    user = db.query(User).filter(User.email == "dash_test_user@example.com").first()
    if not user:
        user = User(
            email="dash_test_user@example.com",
            full_name="Dashboard Admin Test",
            hashed_password="hashed_pass_123",
            role="FARMER"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    user_id = user.id
    db.close()
    token = create_access_token({"sub": str(user_id)})
    return user_id, {"Authorization": f"Bearer {token}"}

def test_dashboard_summary_with_analyzed_crops():
    user_id, headers = setup_user_and_auth()
    db = SessionLocal()
    
    # Clear existing analysis for test user
    db.query(Analysis).filter(Analysis.owner_id == user_id).delete()
    db.commit()
    
    # 1. Add Analysis with explicit area
    a1 = Analysis(
        owner_id=user_id,
        status="completed",
        crop="Wheat",
        crop_name="Wheat",
        district="Betul, Madhya Pradesh",
        area_acres=654353.81,
        health_status="Healthy",
        harvest_in_days=45,
        avg_ndvi=0.72
    )
    # 2. Add Analysis with satellite data unavailable
    a2 = Analysis(
        owner_id=user_id,
        status="completed",
        crop="Soybean",
        crop_name="Soybean",
        district="Sangli, Maharashtra",
        area_acres=105533.60,
        health_status="Satellite data unavailable",
        harvest_in_days=30,
        avg_ndvi=None
    )
    db.add_all([a1, a2])
    db.commit()
    db.close()

    res = client.get("/dashboard/summary", headers=headers)
    assert res.status_code == 200
    data = res.json()

    # Total Monitored Area = 654,353.81 + 105,533.60 = 759,887.41 acres
    assert data["total_monitored_area"] == 759887.41, f"Expected 759887.41, got {data['total_monitored_area']}"
    
    # Healthy Area = 654,353.81 (a1)
    assert data["healthy_area"] == 654353.81, f"Expected 654353.81, got {data['healthy_area']}"
    
    # At Risk Area = 0.0 (because a2 satellite is unavailable!)
    assert data["at_risk_area"] == 0.0, f"Expected 0.0 for satellite unavailable, got {data['at_risk_area']}"
    
    assert data["total_crops"] == 2
    assert data["upcoming_harvest"] == 2


def test_dashboard_alerts_formatting():
    user_id, headers = setup_user_and_auth()
    res = client.get("/dashboard/alerts", headers=headers)
    assert res.status_code == 200
    alerts = res.json()
    assert len(alerts) >= 2
    
    for alert in alerts:
        message = alert.get("message", "")
        # Must not contain 'Area: 0 acres'
        assert "Area: 0 acres" not in message, f"Alert must not display 0 acres for valid analysis: {message}"
        assert "acres" in message or "Area unavailable" in message
