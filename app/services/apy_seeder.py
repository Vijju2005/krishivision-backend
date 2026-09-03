import os
import sys
import zipfile
import csv
import io
import logging
from sqlalchemy.orm import Session
from ..models.orm_models import APYCropStatistic

logger = logging.getLogger("krishivision")

def validate_numeric(val):
    if val is None:
        return None
    val_str = str(val).strip().lower()
    if val_str in ["", "null", "nan", "none"]:
        return None
    try:
        f = float(val_str)
        return f if f >= 0.0 else None
    except ValueError:
        return None

def validate_int(val):
    if val is None:
        return None
    val_str = str(val).strip().lower()
    if val_str in ["", "null", "nan", "none"]:
        return None
    try:
        return int(float(val_str))
    except ValueError:
        return None

def seed_apy_data_if_needed(db: Session) -> bool:
    """
    Idempotent seeder: Checks if APY crop statistics table is populated in the database.
    If count < 100,000, seeds the dataset from data/archive.zip or candidate paths.
    """
    try:
        existing_count = db.query(APYCropStatistic).count()
        print(f"[APY Seeding Check] Current APY dataset count: {existing_count}")
        
        if existing_count >= 100000:
            print("[APY Seeding] APY statistics database already verified and seeded.")
            return True
            
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        candidates = [
            os.path.join(base_dir, "data", "archive.zip"),
            os.path.join(base_dir, "archive.zip"),
            os.path.join(base_dir, "data", "APY.csv"),
            os.path.join(base_dir, "APY.csv"),
            r"C:\Users\keert\Downloads\archive.zip",
            r"C:\Users\keert\Downloads\APY.csv"
        ]
        
        found_path = None
        for cand in candidates:
            if os.path.exists(cand):
                found_path = cand
                break
                
        if not found_path:
            print("[APY Seeding Warning] Could not locate archive.zip or APY.csv in candidate paths.")
            return False
            
        print(f"[APY Seeding] Importing APY dataset from: {found_path}...")
        
        batch_size = 10000
        records = []
        valid_rows = 0
        
        if found_path.endswith(".zip"):
            with zipfile.ZipFile(found_path, 'r') as zip_ref:
                with zip_ref.open("APY.csv") as f:
                    text_stream = io.TextIOWrapper(f, encoding='utf-8')
                    reader = csv.DictReader(text_stream)
                    reader.fieldnames = [name.strip() for name in reader.fieldnames]
                    
                    for row in reader:
                        state_raw = row.get("State")
                        district_raw = row.get("District")
                        crop_raw = row.get("Crop")
                        year_raw = row.get("Crop_Year")
                        season_raw = row.get("Season")
                        area_raw = row.get("Area")
                        prod_raw = row.get("Production")
                        yield_raw = row.get("Yield")
                        
                        if not state_raw or not district_raw or not crop_raw or not year_raw or not season_raw:
                            continue
                            
                        state = state_raw.strip()
                        district = district_raw.strip()
                        crop = crop_raw.strip()
                        season = season_raw.strip()
                        
                        if not state or not district or not crop:
                            continue
                            
                        year = validate_int(year_raw)
                        if year is None:
                            continue
                            
                        area = validate_numeric(area_raw)
                        if area is None or area <= 0.0:
                            continue
                            
                        prod = validate_numeric(prod_raw)
                        yld = validate_numeric(yield_raw)
                        
                        valid_rows += 1
                        records.append({
                            "state_name": state,
                            "district_name": district,
                            "crop_name": crop,
                            "crop_year": year,
                            "season": season,
                            "area_hectares": area,
                            "production_tonnes": prod,
                            "yield_value": yld,
                            "source": "APY Dataset"
                        })
                        
                        if len(records) >= batch_size:
                            db.bulk_insert_mappings(APYCropStatistic, records)
                            db.commit()
                            records = []
                            
                    if records:
                        db.bulk_insert_mappings(APYCropStatistic, records)
                        db.commit()
        else:
            with open(found_path, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f)
                reader.fieldnames = [name.strip() for name in reader.fieldnames]
                for row in reader:
                    state_raw = row.get("State")
                    district_raw = row.get("District")
                    crop_raw = row.get("Crop")
                    year_raw = row.get("Crop_Year")
                    season_raw = row.get("Season")
                    area_raw = row.get("Area")
                    prod_raw = row.get("Production")
                    yield_raw = row.get("Yield")
                    
                    if not state_raw or not district_raw or not crop_raw or not year_raw or not season_raw:
                        continue
                        
                    state = state_raw.strip()
                    district = district_raw.strip()
                    crop = crop_raw.strip()
                    season = season_raw.strip()
                    
                    if not state or not district or not crop:
                        continue
                        
                    year = validate_int(year_raw)
                    if year is None:
                        continue
                        
                    area = validate_numeric(area_raw)
                    if area is None or area <= 0.0:
                        continue
                        
                    prod = validate_numeric(prod_raw)
                    yld = validate_numeric(yield_raw)
                    
                    valid_rows += 1
                    records.append({
                        "state_name": state,
                        "district_name": district,
                        "crop_name": crop,
                        "crop_year": year,
                        "season": season,
                        "area_hectares": area,
                        "production_tonnes": prod,
                        "yield_value": yld,
                        "source": "APY Dataset"
                    })
                    
                    if len(records) >= batch_size:
                        db.bulk_insert_mappings(APYCropStatistic, records)
                        db.commit()
                        records = []
                        
                if records:
                    db.bulk_insert_mappings(APYCropStatistic, records)
                    db.commit()
                    
        print(f"[APY Seeding Success] Successfully imported {valid_rows} records into APYCropStatistic table.")
        return True
    except Exception as e:
        logger.error(f"[APY Seeding Error] Failed to seed APY dataset: {e}")
        db.rollback()
        return False
