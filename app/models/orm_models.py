from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Boolean, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from ..database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    full_name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    phone = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user") # 'user' or 'admin'
    profile_photo = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Agricultural / Farmer details
    farmer_name = Column(String, nullable=True)
    state_location = Column(String, nullable=True)
    district_location = Column(String, nullable=True)
    village_location = Column(String, nullable=True)
    farm_name = Column(String, nullable=True)
    total_farm_area = Column(Float, default=0.0)
    primary_crop = Column(String, nullable=True)
    other_crops = Column(String, nullable=True)
    soil_type = Column(String, nullable=True)
    irrigation_type = Column(String, nullable=True)
    farming_experience = Column(Integer, default=0)
    my_crops = Column(String, nullable=True)
    farming_type = Column(String, nullable=True)
    preferred_language = Column(String, default="en")
    main_farming_season = Column(String, nullable=True)

    analyses = relationship("Analysis", back_populates="owner")
    farms = relationship("Farm", back_populates="owner")
    notifications = relationship("Notification", back_populates="user")
    settings = relationship("Settings", back_populates="user", uselist=False)


class Farm(Base):
    __tablename__ = "farms"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String, nullable=False)
    boundary_geojson = Column(JSON, nullable=True)
    area_acres = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="farms")


class Analysis(Base):
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    owner_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="processing") # processing | completed | failed
    image_path = Column(String, nullable=True)
    ndvi_image_path = Column(String, nullable=True)

    crop = Column(String, nullable=True)
    district = Column(String, nullable=True)
    area_acres = Column(Float, nullable=True)
    growth_stage = Column(String, nullable=True)
    health_status = Column(String, nullable=True) # Healthy | At Risk | Unhealthy
    harvest_in_days = Column(Integer, nullable=True)
    confidence = Column(Float, nullable=True)
    crop_name = Column(String, nullable=True)
    crop_confidence = Column(Float, nullable=True)
    stage_confidence = Column(Float, nullable=True)
    disease = Column(String, default="None")
    boundary_geojson = Column(JSON, nullable=True)

    # NDVI Statistics
    avg_ndvi = Column(Float, default=0.0)
    min_ndvi = Column(Float, default=0.0)
    max_ndvi = Column(Float, default=0.0)

    created_at = Column(DateTime, default=datetime.utcnow)

    owner = relationship("User", back_populates="analyses")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    read = Column(Boolean, default=False)
    type = Column(String, default="info") # weather | disease | harvest | info
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="notifications")


class Settings(Base):
    __tablename__ = "settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    preferred_language = Column(String, default="en")
    dark_mode = Column(Boolean, default=False)
    notification_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="settings")


class State(Base):
    __tablename__ = "states"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    boundary_geojson = Column(JSON, nullable=True)

    districts = relationship("District", back_populates="state")


class District(Base):
    __tablename__ = "districts"

    id = Column(Integer, primary_key=True, index=True)
    state_id = Column(Integer, ForeignKey("states.id"), nullable=False)
    name = Column(String, nullable=False)
    boundary_geojson = Column(JSON, nullable=True)
    monitored_area_acres = Column(Float, default=0.0)

    state = relationship("State", back_populates="districts")
    crops = relationship("Crop", back_populates="district")


class CropMaster(Base):
    __tablename__ = "crop_masters"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    scientific_name = Column(String, nullable=True)
    category = Column(String, nullable=True)
    icon = Column(String, nullable=True)
    growing_season = Column(String, nullable=True)
    growth_duration = Column(String, nullable=True)
    description = Column(String, nullable=True)
    growth_stages = Column(JSON, nullable=True)

    district_mappings = relationship("Crop", back_populates="crop_master")


class Crop(Base):
    __tablename__ = "crops"

    id = Column(Integer, primary_key=True, index=True)
    district_id = Column(Integer, ForeignKey("districts.id"), nullable=False)
    crop_master_id = Column(Integer, ForeignKey("crop_masters.id"), nullable=False)
    source = Column(String, default="Ministry of Agriculture & Farmers Welfare, Govt of India")
    source_year = Column(Integer, default=2024)
    importance = Column(String, default="Major Crop") # "Major Crop" or "Minor Crop"
    
    # Localized statistics
    area_acres = Column(Float, default=0.0)
    production_tonnes = Column(Float, default=0.0)
    yield_hg_ha = Column(Float, default=0.0)
    crop_percentage = Column(Float, default=0.0)
    growth_stage = Column(String, default="Vegetative")
    health_status = Column(String, default="Major crops reported for this district")
    harvest_in_days = Column(Integer, default=60)
    fields_count = Column(Integer, default=1)
    boundary_geojson = Column(JSON, nullable=True)

    # Satellite reference metrics
    avg_ndvi = Column(Float, default=0.0)
    min_ndvi = Column(Float, default=0.0)
    max_ndvi = Column(Float, default=0.0)
    avg_evi = Column(Float, default=0.0)
    moisture_level = Column(Float, default=0.0)
    temperature = Column(Float, default=0.0)

    district = relationship("District", back_populates="crops")
    crop_master = relationship("CropMaster", back_populates="district_mappings")


class Alert(Base):
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String, nullable=False)
    message = Column(String, nullable=False)
    type = Column(String, default="info")
    read = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    analysis_id = Column(Integer, ForeignKey("analyses.id"), nullable=False)
    crop_name = Column(String, nullable=False)
    district = Column(String, nullable=False)
    state = Column(String, nullable=False)
    area_acres = Column(Float, default=0.0)
    health_status = Column(String, default="Healthy")
    growth_stage = Column(String, default="Vegetative")
    avg_ndvi = Column(Float, default=0.0)
    avg_evi = Column(Float, default=0.0)
    moisture_level = Column(Float, default=0.0)
    temperature = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.utcnow)


class WeatherData(Base):
    __tablename__ = "weather_data"

    id = Column(Integer, primary_key=True, index=True)
    temp = Column(Float, default=25.0)
    humidity = Column(Float, default=60.0)
    rain_probability = Column(Float, default=10.0)
    wind_speed = Column(Float, default=5.0)
    condition = Column(String, default="Sunny")
    created_at = Column(DateTime, default=datetime.utcnow)


class CropMasterIndia(Base):
    __tablename__ = "crop_master"

    id = Column(Integer, primary_key=True, index=True)
    crop_name = Column(String, unique=True, nullable=False)
    scientific_name = Column(String, nullable=True)
    category = Column(String, nullable=True)
    season = Column(String, nullable=True)
    growth_duration_days = Column(Integer, nullable=True)
    major_indian_states = Column(String, nullable=True)


class OTPVerification(Base):
    __tablename__ = "otp_verifications"

    id = Column(Integer, primary_key=True, index=True)
    phone_number = Column(String, nullable=False, index=True)
    hashed_otp = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False)
    attempts = Column(Integer, default=0)
    is_used = Column(Boolean, default=False)


class GovernmentCropCache(Base):
    __tablename__ = "government_crop_cache"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String, index=True, nullable=False)
    district = Column(String, index=True, nullable=False)
    data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class DistrictAnalysisCache(Base):
    __tablename__ = "district_analysis_cache"

    id = Column(Integer, primary_key=True, index=True)
    district_name = Column(String, index=True, nullable=False)
    start_date = Column(String, nullable=False)
    end_date = Column(String, nullable=False)
    dataset_version = Column(String, nullable=False)
    cropland_area_hectares = Column(Float, nullable=False)
    cropland_area_acres = Column(Float, nullable=False)
    mean_ndvi = Column(Float, nullable=False)
    min_ndvi = Column(Float, nullable=False)
    max_ndvi = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class AgroMonitoringPolygon(Base):
    __tablename__ = "agromonitoring_polygons"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String, index=True, nullable=False)
    district = Column(String, index=True, nullable=False)
    crop = Column(String, index=True, nullable=False)
    polygon_id = Column(String, unique=True, nullable=False)
    geojson = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class SatelliteAnalysisCache(Base):
    __tablename__ = "satellite_analysis_cache"

    id = Column(Integer, primary_key=True, index=True)
    state = Column(String, index=True, nullable=False)
    district = Column(String, index=True, nullable=False)
    crop = Column(String, index=True, nullable=False)
    polygon_id = Column(String, nullable=True)
    observation_date = Column(String, nullable=False)
    ndvi = Column(Float, nullable=True)
    evi = Column(Float, nullable=True)
    evi2 = Column(Float, nullable=True)
    ndwi = Column(Float, nullable=True)
    nri = Column(Float, nullable=True)
    dswi = Column(Float, nullable=True)
    image_urls = Column(JSON, nullable=True)
    statistics = Column(JSON, nullable=True)
    source = Column(String, default="AgroMonitoring")
    fetched_at = Column(DateTime, default=datetime.utcnow)


class APYCropStatistic(Base):
    __tablename__ = "apy_crop_statistics"

    id = Column(Integer, primary_key=True, index=True)
    state_name = Column(String, index=True, nullable=False)
    district_name = Column(String, index=True, nullable=False)
    crop_name = Column(String, index=True, nullable=False)
    crop_year = Column(Integer, index=True, nullable=False)
    season = Column(String, nullable=False)
    area_hectares = Column(Float, nullable=False)
    production_tonnes = Column(Float, nullable=True)
    yield_value = Column(Float, nullable=True)
    source = Column(String, default="APY Dataset")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    __table_args__ = (
        Index('idx_apy_composite', 'state_name', 'district_name', 'crop_name', 'crop_year', 'season'),
    )




