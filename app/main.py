import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import Base, engine
from .routers import auth, analysis, fields, weather, admin, notifications, settings, dashboard_map, district_analysis
from .services.crop_api_service import GovernmentCropDataUnavailableException

app = FastAPI(
    title="KrishiVision",
    description="Backend for smart crop monitoring using satellite images.",
    version="1.0.0",
)

@app.exception_handler(GovernmentCropDataUnavailableException)
async def gov_crop_data_unavailable_exception_handler(request, exc: GovernmentCropDataUnavailableException):
    return JSONResponse(
        status_code=503,
        content={
            "detail": exc.detail,
            "source": "data.gov.in",
            "status": "unavailable"
        }
    )

@app.on_event("startup")
def startup_db_and_import():
    # 1. Ensure database tables are created automatically on launch
    try:
        Base.metadata.create_all(bind=engine)
    except Exception as e:
        print(f"[Startup DB Init] Notice: {e}")

    # 2. Idempotent All-India database coverage audit & seeding
    try:
        import sys
        backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
        if backend_dir not in sys.path:
            sys.path.insert(0, backend_dir)

        from app.database import SessionLocal
        from app.models.orm_models import State, District, Crop
        from sqlalchemy import func

        db = SessionLocal()
        state_count = db.query(State).count()
        district_count = db.query(District).count()

        kar = db.query(State).filter(State.name.ilike('%karnataka%')).first()
        is_rectangle = False
        if kar and kar.boundary_geojson:
            bg = kar.boundary_geojson
            coords = bg.get("coordinates", [])
            if bg.get("type") == "Polygon" and len(coords) == 1 and len(coords[0]) <= 5:
                is_rectangle = True

        print(f"[Startup Coverage Audit] States: {state_count}/35, Districts: {district_count}/594, Rectangular boundary: {is_rectangle}")

        if state_count < 35 or district_count < 500 or is_rectangle:
            print("[Startup Seeding] All-India database coverage incomplete. Running idempotent boundary import...")
            if is_rectangle:
                # Clean up legacy rectangular entries if present
                db.query(Crop).delete()
                db.query(District).delete()
                db.query(State).delete()
                db.commit()

            try:
                from load_sample_data import seed_database
                seed_database()
            except Exception as e_user:
                print(f"[Startup User Seed Notice] {e_user}")

            from scripts.import_india_boundaries import import_all_india_data
            import_all_india_data(db)
        else:
            print("[Startup Coverage Audit] All-India database coverage verified complete.")
            
        # Seed APY dataset into database if not already present
        try:
            from app.services.apy_seeder import seed_apy_data_if_needed
            seed_apy_data_if_needed(db)
        except Exception as e_apy:
            print(f"[Startup APY Seeding Error] Notice: {e_apy}")
            
        db.close()
    except Exception as e:
        print(f"[Startup Seeding Error] Notice: {e}")

    # 2. Invalidate satellite analysis cache on startup to clear old stale/fake records
    try:
        from .database import SessionLocal
        from .models.orm_models import SatelliteAnalysisCache
        db = SessionLocal()
        deleted = db.query(SatelliteAnalysisCache).delete()
        db.commit()
        db.close()
        print(f"[Startup Invalidation] Purged {deleted} stale satellite analysis cache records.")
    except Exception as e:
        print(f"[Startup Invalidation] Failed to purge satellite cache: {e}")

    # 3. Add new profile/farmer columns if they don't exist
    from sqlalchemy import text
    cols_to_add = [
        ("profile_photo", "VARCHAR"),
        ("farmer_name", "VARCHAR"),
        ("state_location", "VARCHAR"),
        ("district_location", "VARCHAR"),
        ("village_location", "VARCHAR"),
        ("farm_name", "VARCHAR"),
        ("total_farm_area", "FLOAT DEFAULT 0.0"),
        ("primary_crop", "VARCHAR"),
        ("other_crops", "VARCHAR"),
        ("soil_type", "VARCHAR"),
        ("irrigation_type", "VARCHAR"),
        ("farming_experience", "INTEGER DEFAULT 0"),
        ("my_crops", "VARCHAR"),
        ("farming_type", "VARCHAR"),
        ("preferred_language", "VARCHAR DEFAULT 'en'"),
        ("main_farming_season", "VARCHAR"),
    ]
    for col_name, col_type in cols_to_add:
        try:
            with engine.begin() as conn:
                conn.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type};"))
        except Exception:
            pass

    # 4. Diagnostics & CSV Crop Master Import
    api_key = os.getenv("DATA_GOV_API_KEY", "")
    key_configured = bool(api_key and api_key.strip() and api_key != "YOUR_PERSONAL_DATA_GOV_API_KEY")
    print(f"[DATA_GOV] API key configured: {str(key_configured).lower()}")
    import csv
    from sqlalchemy import func
    from .database import SessionLocal
    from .models.orm_models import CropMasterIndia
    
    # Try finding CSV path
    base_dir = os.path.dirname(os.path.abspath(__file__))
    candidates = [
        os.path.join(base_dir, "..", "..", "..", "krishivision_india_crop_master.csv"),
        os.path.join(base_dir, "..", "..", "krishivision_india_crop_master.csv"),
        "krishivision_india_crop_master.csv",
        "../krishivision_india_crop_master.csv"
    ]
    csv_path = None
    for cand in candidates:
        abs_cand = os.path.abspath(cand)
        if os.path.exists(abs_cand):
            csv_path = abs_cand
            break
            
    if not csv_path:
        print("[CSV Import] krishivision_india_crop_master.csv not found in candidates")
        return
        
    print(f"[CSV Import] Importing crop master from: {csv_path}")
    db = SessionLocal()
    try:
        # Create table if it doesn't exist
        Base.metadata.create_all(bind=engine)
        
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            count = 0
            for row in reader:
                crop_name = row.get("crop_name", "").strip()
                if not crop_name:
                    continue
                # Case-insensitive duplicate check
                existing = db.query(CropMasterIndia).filter(
                    func.lower(CropMasterIndia.crop_name) == func.lower(crop_name)
                ).first()
                if existing:
                    continue
                
                try:
                    duration_str = row.get("growth_duration_days", "")
                    duration = int(duration_str) if duration_str else None
                except Exception:
                    duration = None
                    
                crop_entry = CropMasterIndia(
                    crop_name=crop_name,
                    scientific_name=row.get("scientific_name", "").strip(),
                    category=row.get("category", "").strip(),
                    season=row.get("season", "").strip(),
                    growth_duration_days=duration,
                    major_indian_states=row.get("major_indian_states", "").strip()
                )
                db.add(crop_entry)
                count += 1
            if count > 0:
                db.commit()
                print(f"[CSV Import] Successfully imported {count} new crops.")
            else:
                print("[CSV Import] No new crops imported.")
    except Exception as e:
        print(f"[CSV Import] Error during crop master import: {e}")
    finally:
        db.close()

# CORS setup for Flutter emulators/web
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(auth.router)
app.include_router(analysis.router)
app.include_router(fields.router)
app.include_router(weather.router)
app.include_router(admin.router)
app.include_router(notifications.router)
app.include_router(settings.router)
app.include_router(dashboard_map.router)
app.include_router(district_analysis.router)


# Mount the static uploads directory so generated NDVI maps can be served directly
UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/static", StaticFiles(directory=UPLOAD_DIR), name="static")


@app.get("/")
def root():
    return {"status": "ok", "service": "KrishiVision"}


@app.get("/health")
def health():
    print("[Backend] Health check: SUCCESS")
    return {"status": "healthy"}


@app.get("/crop-api/status")
def get_crop_api_status():
    from .database import SessionLocal
    from .models.orm_models import GovernmentCropCache
    from .services.data_gov_crop_service import get_api_key
    
    api_key = get_api_key()
    configured = bool(api_key and api_key.strip() and api_key != "YOUR_PERSONAL_DATA_GOV_API_KEY")
    
    db = SessionLocal()
    try:
        latest = db.query(GovernmentCropCache).order_by(GovernmentCropCache.created_at.desc()).first()
        last_success = latest.created_at.isoformat() if latest else "never"
        cache_records = db.query(GovernmentCropCache).count()
    finally:
        db.close()
        
    return {
        "configured": configured,
        "api": "data.gov.in",
        "last_success": last_success,
        "cache_records": cache_records,
        "status": "healthy"
    }


@app.get("/apy/status")
def get_apy_db_status():
    from .database import SessionLocal
    from .models.orm_models import APYCropStatistic
    db = SessionLocal()
    try:
        count = db.query(APYCropStatistic).count()
        return {"status": "seeded" if count > 100000 else "empty", "count": count}
    finally:
        db.close()


@app.get("/apy/seed")
def trigger_apy_db_seed():
    from .database import SessionLocal
    from .models.orm_models import APYCropStatistic
    from .services.apy_seeder import seed_apy_data_if_needed
    db = SessionLocal()
    try:
        res = seed_apy_data_if_needed(db)
        count = db.query(APYCropStatistic).count()
        return {"success": res, "count": count}
    finally:
        db.close()


@app.get("/crop-api/states")
def get_crop_api_states():
    # Return the state names actually available in the dataset
    return {
        "status": "success",
        "states": [
            "Andaman and Nicobar Islands",
            "Andhra Pradesh",
            "Arunachal Pradesh",
            "Assam",
            "Bihar",
            "Chandigarh",
            "Chhattisgarh",
            "Dadra and Nagar Haveli",
            "Daman and Diu",
            "Delhi",
            "Goa",
            "Gujarat",
            "Haryana",
            "Himachal Pradesh",
            "Jammu and Kashmir",
            "Jharkhand",
            "Karnataka",
            "Kerala",
            "Madhya Pradesh",
            "Maharashtra",
            "Manipur",
            "Meghalaya",
            "Mizoram",
            "Nagaland",
            "Odisha",
            "Puducherry",
            "Punjab",
            "Rajasthan",
            "Sikkim",
            "Tamil Nadu",
            "Telangana",
            "Tripura",
            "Uttar Pradesh",
            "Uttarakhand",
            "West Bengal"
        ]
    }


@app.get("/crop-api/districts/{state_name}")
def get_crop_api_districts(state_name: str):
    from .database import SessionLocal
    from .models.orm_models import State, District
    from .services.crop_api_service import normalize_state_name, normalize_district_name
    from sqlalchemy import func
    
    normalized_state = normalize_state_name(state_name)
    
    db = SessionLocal()
    try:
        db_state = db.query(State).filter(
            func.lower(State.name) == func.lower(normalized_state)
        ).first()
        if not db_state:
            # Fallback split check
            db_state = db.query(State).filter(
                State.name.ilike(f"%{normalized_state.split()[0]}%")
            ).first()
            
        if not db_state:
            return {
                "status": "error",
                "message": f"State '{state_name}' not found in local database."
            }
            
        districts = db.query(District).filter(District.state_id == db_state.id).all()
        normalized_districts = []
        for d in districts:
            norm = normalize_district_name(d.name)
            normalized_districts.append(norm)
            
        return {
            "status": "success",
            "state": db_state.name,
            "api_state": normalized_state,
            "districts": sorted(list(set(normalized_districts)))
        }
    finally:
        db.close()
