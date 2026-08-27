from pydantic import BaseModel, EmailStr, Field
from typing import Optional, Any, List
from datetime import datetime


# ---- Auth ----
class RegisterRequest(BaseModel):
    full_name: str
    email: EmailStr
    phone: Optional[str] = None
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: int
    full_name: str
    role: str = "user"


class UserRoleUpdate(BaseModel):
    role: str


# ---- Analysis ----
class AnalysisStatusResponse(BaseModel):
    job_id: int
    status: str # processing | completed | failed
    progress: int # 0-100, mocked based on time elapsed


class AnalysisResultResponse(BaseModel):
    id: int
    job_id: int = Field(validation_alias="id")
    crop: Optional[str] = None
    crop_name: Optional[str] = None
    district: Optional[str] = None
    area_acres: Optional[float] = None
    growth_stage: Optional[str] = None
    health_status: Optional[str] = None
    harvest_in_days: Optional[int] = None
    confidence: Optional[float] = None
    crop_confidence: Optional[float] = None
    stage_confidence: Optional[float] = None
    disease: Optional[str] = None
    image_path: Optional[str] = None
    ndvi_image_path: Optional[str] = None
    avg_ndvi: Optional[float] = 0.0
    min_ndvi: Optional[float] = 0.0
    max_ndvi: Optional[float] = 0.0
    boundary_geojson: Optional[Any] = None
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


class AnalysisHistoryItem(BaseModel):
    id: int
    job_id: int = Field(validation_alias="id")
    crop: Optional[str] = None
    crop_name: Optional[str] = None
    district: Optional[str] = None
    area_acres: Optional[float] = None
    growth_stage: Optional[str] = None
    health_status: Optional[str] = None
    crop_confidence: Optional[float] = None
    stage_confidence: Optional[float] = None
    disease: Optional[str] = None
    image_path: Optional[str] = None
    ndvi_image_path: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
        populate_by_name = True


# ---- Notifications ----
class NotificationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    message: str
    read: bool
    type: str
    created_at: datetime

    class Config:
        from_attributes = True


# ---- Settings ----
class SettingsResponse(BaseModel):
    preferred_language: str
    dark_mode: bool
    notification_enabled: bool

    class Config:
        from_attributes = True


class SettingsUpdate(BaseModel):
    preferred_language: Optional[str] = None
    dark_mode: Optional[bool] = None
    notification_enabled: Optional[bool] = None


# ---- Weather ----
class WeatherResponse(BaseModel):
    temp: float
    humidity: float
    rain_probability: float
    wind_speed: float
    condition: str


# ---- Dashboard ----
class DashboardSummaryResponse(BaseModel):
    total_monitored_area: float
    healthy_area: float
    at_risk_area: float
    total_crops: int
    upcoming_harvest: int


class DashboardAlertResponse(BaseModel):
    crop: str
    district: str
    state: str
    health: str
    area_acres: float
