from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..models.orm_models import User, Settings, OTPVerification
from ..models.schemas import RegisterRequest, LoginRequest, TokenResponse
from ..services.auth import hash_password, verify_password, create_access_token
from datetime import datetime, timedelta
from ..services.sms_service import get_sms_provider

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == payload.email).first()
    if existing:
        raise HTTPException(status_code=400, detail="Email already registered")

    # Grant admin permissions to the first user registered in the system for testing
    user_count = db.query(User).count()
    role = "admin" if user_count == 0 else "user"

    user = User(
        full_name=payload.full_name,
        email=payload.email,
        phone=payload.phone,
        hashed_password=hash_password(payload.password),
        role=role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    # Initialize default user settings
    user_settings = Settings(user_id=user.id)
    db.add(user_settings)
    db.commit()

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        full_name=user.full_name,
        role=user.role
    )


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        full_name=user.full_name,
        role=user.role
    )


from ..deps import get_current_user
from pydantic import BaseModel, EmailStr
from typing import Optional

class UpdateProfileRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: str
    farmer_name: Optional[str] = None
    state_location: Optional[str] = None
    district_location: Optional[str] = None
    village_location: Optional[str] = None
    farm_name: Optional[str] = None
    total_farm_area: Optional[float] = 0.0
    primary_crop: Optional[str] = None
    other_crops: Optional[str] = None
    soil_type: Optional[str] = None
    irrigation_type: Optional[str] = None
    farming_experience: Optional[int] = 0
    my_crops: Optional[str] = None
    farming_type: Optional[str] = None
    preferred_language: Optional[str] = "en"
    main_farming_season: Optional[str] = None

@router.get("/me")
def get_me(current_user: User = Depends(get_current_user)):
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "role": current_user.role,
        "profile_photo": current_user.profile_photo,
        "farmer_name": current_user.farmer_name,
        "state_location": current_user.state_location,
        "district_location": current_user.district_location,
        "village_location": current_user.village_location,
        "farm_name": current_user.farm_name,
        "total_farm_area": current_user.total_farm_area or 0.0,
        "primary_crop": current_user.primary_crop,
        "other_crops": current_user.other_crops,
        "soil_type": current_user.soil_type,
        "irrigation_type": current_user.irrigation_type,
        "farming_experience": current_user.farming_experience or 0,
        "my_crops": current_user.my_crops,
        "farming_type": current_user.farming_type,
        "preferred_language": current_user.preferred_language or "en",
        "main_farming_season": current_user.main_farming_season,
    }

@router.post("/update")
def update_profile(
    payload: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if payload.email != current_user.email:
        conflict = db.query(User).filter(User.email == payload.email).first()
        if conflict:
            raise HTTPException(status_code=400, detail="Email already registered")
            
    current_user.full_name = payload.full_name
    current_user.email = payload.email
    current_user.phone = payload.phone
    current_user.farmer_name = payload.farmer_name
    current_user.state_location = payload.state_location
    current_user.district_location = payload.district_location
    current_user.village_location = payload.village_location
    current_user.farm_name = payload.farm_name
    current_user.total_farm_area = payload.total_farm_area if payload.total_farm_area is not None else 0.0
    current_user.primary_crop = payload.primary_crop
    current_user.other_crops = payload.other_crops
    current_user.soil_type = payload.soil_type
    current_user.irrigation_type = payload.irrigation_type
    current_user.farming_experience = payload.farming_experience if payload.farming_experience is not None else 0
    current_user.my_crops = payload.my_crops
    current_user.farming_type = payload.farming_type
    current_user.preferred_language = payload.preferred_language if payload.preferred_language is not None else "en"
    current_user.main_farming_season = payload.main_farming_season
    
    db.commit()
    db.refresh(current_user)
    
    return {
        "id": current_user.id,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "phone": current_user.phone,
        "role": current_user.role,
        "profile_photo": current_user.profile_photo,
        "farmer_name": current_user.farmer_name,
        "state_location": current_user.state_location,
        "district_location": current_user.district_location,
        "village_location": current_user.village_location,
        "farm_name": current_user.farm_name,
        "total_farm_area": current_user.total_farm_area or 0.0,
        "primary_crop": current_user.primary_crop,
        "other_crops": current_user.other_crops,
        "soil_type": current_user.soil_type,
        "irrigation_type": current_user.irrigation_type,
        "farming_experience": current_user.farming_experience or 0,
        "my_crops": current_user.my_crops,
        "farming_type": current_user.farming_type,
        "preferred_language": current_user.preferred_language or "en",
        "main_farming_season": current_user.main_farming_season,
    }


class SocialLoginRequest(BaseModel):
    provider: str
    email: EmailStr
    full_name: str
    id: str

@router.post("/social-login", response_model=TokenResponse)
def social_login(payload: SocialLoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email).first()
    if not user:
        import uuid
        from ..services.auth import hash_password
        user = User(
            full_name=payload.full_name,
            email=payload.email,
            phone="+91 98765 43210",
            hashed_password=hash_password(str(uuid.uuid4())),
            role="user"
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        user_settings = Settings(user_id=user.id)
        db.add(user_settings)
        db.commit()

    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        full_name=user.full_name,
        role=user.role
    )


import os
import uuid
from fastapi import UploadFile, File

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))

@router.post("/profile-photo")
async def upload_profile_photo(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    ext = os.path.splitext(file.filename or "")[1] or ".png"
    profile_photos_dir = os.path.join(UPLOAD_DIR, "profile_photos")
    os.makedirs(profile_photos_dir, exist_ok=True)
    
    saved_name = f"user_{current_user.id}_{uuid.uuid4().hex}{ext}"
    saved_path = os.path.join(profile_photos_dir, saved_name)
    
    if current_user.profile_photo:
        old_filename = current_user.profile_photo.split("/")[-1]
        old_path = os.path.join(profile_photos_dir, old_filename)
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except OSError:
                pass
                
    with open(saved_path, "wb") as f:
        f.write(await file.read())
        
    relative_url = f"/static/profile_photos/{saved_name}"
    current_user.profile_photo = relative_url
    db.commit()
    db.refresh(current_user)
    
    return {
        "status": "success",
        "profile_photo": relative_url
    }

@router.delete("/profile-photo")
def delete_profile_photo(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.profile_photo:
        profile_photos_dir = os.path.join(UPLOAD_DIR, "profile_photos")
        old_filename = current_user.profile_photo.split("/")[-1]
        old_path = os.path.join(profile_photos_dir, old_filename)
        if os.path.exists(old_path):
            try:
                os.remove(old_path)
            except OSError:
                pass
                
    current_user.profile_photo = None
    db.commit()
    db.refresh(current_user)
    return {
        "status": "success",
        "message": "Profile photo removed successfully"
    }


import hashlib
import random
import string
import re
import uuid

class OTPRequest(BaseModel):
    phone_number: str

class OTPVerifyRequest(BaseModel):
    phone_number: str
    otp: str

def normalize_phone_number(phone: str) -> str:
    cleaned = re.sub(r"[\s\-\(\)]", "", phone)
    match = re.match(r"^(?:\+?91)?[6-9]\d{9}$", cleaned)
    if not match:
        raise ValueError("Invalid Indian mobile number")
    if cleaned.startswith("+91"):
        return cleaned
    elif cleaned.startswith("91") and len(cleaned) == 12:
        return f"+{cleaned}"
    else:
        if cleaned.startswith("0"):
            cleaned = cleaned[1:]
        return f"+91{cleaned}"

@router.post("/otp/request")
def request_otp(payload: OTPRequest, db: Session = Depends(get_db)):
    try:
        phone = normalize_phone_number(payload.phone_number)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Resend rate limiting: check last requested OTP for this phone
    last_verification = db.query(OTPVerification).filter(
        OTPVerification.phone_number == phone
    ).order_by(OTPVerification.created_at.desc()).first()

    if last_verification:
        elapsed = (datetime.utcnow() - last_verification.created_at).total_seconds()
        if elapsed < 60:
            raise HTTPException(
                status_code=429, 
                detail=f"Please wait {int(60 - elapsed)} seconds before requesting another OTP"
            )

    # Generate 6-digit OTP
    otp = "".join(random.choices(string.digits, k=6))
    hashed_otp = hashlib.sha256(otp.encode("utf-8")).hexdigest()
    expires_at = datetime.utcnow() + timedelta(minutes=5)

    verification = OTPVerification(
        phone_number=phone,
        hashed_otp=hashed_otp,
        expires_at=expires_at,
        attempts=0,
        is_used=False
    )
    db.add(verification)
    db.commit()

    # Dispatch SMS
    provider = get_sms_provider()
    message = f"Your KrishiVision verification code is {otp}. Valid for 5 minutes."
    success = provider.send_sms(phone, message)
    if not success:
        raise HTTPException(status_code=500, detail="Failed to send SMS code. Please try again.")

    return {"status": "success", "message": "OTP sent successfully"}

@router.post("/otp/verify", response_model=TokenResponse)
def verify_otp(payload: OTPVerifyRequest, db: Session = Depends(get_db)):
    try:
        phone = normalize_phone_number(payload.phone_number)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Retrieve the latest verification record
    record = db.query(OTPVerification).filter(
        OTPVerification.phone_number == phone
    ).order_by(OTPVerification.created_at.desc()).first()

    if not record:
        raise HTTPException(status_code=400, detail="No verification requested for this phone number")

    if record.is_used:
        raise HTTPException(status_code=400, detail="This verification code has already been used")

    if datetime.utcnow() > record.expires_at:
        raise HTTPException(status_code=400, detail="Verification code has expired. Please request a new one.")

    if record.attempts >= 5:
        raise HTTPException(status_code=400, detail="Maximum verification attempts exceeded. Please request a new OTP.")

    # Increment verification attempts
    record.attempts += 1
    db.commit()

    # Check OTP
    input_hash = hashlib.sha256(payload.otp.encode("utf-8")).hexdigest()
    if input_hash != record.hashed_otp:
        remaining = 5 - record.attempts
        raise HTTPException(
            status_code=400, 
            detail=f"Incorrect verification code. Remaining attempts: {remaining}"
        )

    # Success: mark as used
    record.is_used = True
    db.commit()

    # Find or auto-register the user
    user = db.query(User).filter(User.phone == phone).first()
    if not user:
        user_count = db.query(User).count()
        role = "admin" if user_count == 0 else "user"
        
        user = User(
            full_name=f"Farmer {phone[-4:]}",
            email=f"{phone[1:]}@krishivision.com",
            phone=phone,
            hashed_password=hash_password(uuid.uuid4().hex),
            role=role
        )
        db.add(user)
        db.commit()
        db.refresh(user)

        # Initialize default user settings
        settings = Settings(user_id=user.id)
        db.add(settings)
        db.commit()

    # Return JWT token
    token = create_access_token({"sub": str(user.id)})
    return TokenResponse(
        access_token=token,
        user_id=user.id,
        full_name=user.full_name,
        role=user.role
    )
