import os
import sys
import zipfile
import csv
import io
from datetime import datetime

# Add backend directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.database import Base, engine, SessionLocal
from app.models.orm_models import APYCropStatistic

ZIP_PATH = r"C:\Users\keert\Downloads\archive.zip"
DB_NAME = "krishivision.db"

def validate_numeric(val):
    if not val:
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
    if not val:
        return None
    val_str = str(val).strip().lower()
    if val_str in ["", "null", "nan", "none"]:
        return None
    try:
        return int(val_str)
    except ValueError:
        return None

def main():
    print(f"Creating database tables (if not existing)...")
    Base.metadata.create_all(bind=engine)
    
    db = SessionLocal()
    try:
        if not os.path.exists(ZIP_PATH):
            print(f"Error: Zip file not found at {ZIP_PATH}")
            sys.exit(1)
            
        print(f"Clearing old APY Dataset records from the database...")
        db.query(APYCropStatistic).filter(APYCropStatistic.source == "APY Dataset").delete()
        db.commit()
        
        print(f"Extracting and reading APY.csv from {ZIP_PATH}...")
        records = []
        batch_size = 10000
        total_rows = 0
        valid_rows = 0
        
        states = set()
        districts = set()
        crops = set()
        min_year = 9999
        max_year = 0
        karnataka_count = 0
        chikkamagaluru_count = 0
        
        with zipfile.ZipFile(ZIP_PATH, 'r') as zip_ref:
            with zip_ref.open("APY.csv") as f:
                text_stream = io.TextIOWrapper(f, encoding='utf-8')
                reader = csv.DictReader(text_stream)
                # Clean headers of trailing/leading spaces
                reader.fieldnames = [name.strip() for name in reader.fieldnames]
                
                print("Headers cleaned:", reader.fieldnames)
                
                for row in reader:
                    total_rows += 1
                    
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
                        # Exclude null area or area <= 0
                        continue
                        
                    prod = validate_numeric(prod_raw)
                    yld = validate_numeric(yield_raw)
                    
                    valid_rows += 1
                    
                    # Track statistics
                    states.add(state.lower())
                    districts.add(f"{state.lower()}:{district.lower()}")
                    crops.add(crop.lower())
                    
                    if year < min_year:
                        min_year = year
                    if year > max_year:
                        max_year = year
                        
                    if state.lower() == "karnataka":
                        karnataka_count += 1
                        if district.lower() == "chikkamagaluru":
                            chikkamagaluru_count += 1
                            
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
                        print(f"Imported {valid_rows} valid records...")
                        
                # Insert remaining
                if records:
                    db.bulk_insert_mappings(APYCropStatistic, records)
                    db.commit()
                    print(f"Imported final batch. Total valid records: {valid_rows}")
                    
        # Verification outputs
        print("\n==============================================")
        print("DATABASE IMPORT VERIFICATION RESULTS")
        print("==============================================")
        print(f"Total Rows Scanned in CSV: {total_rows}")
        print(f"Total Valid Records Imported: {valid_rows}")
        print(f"Distinct States: {len(states)}")
        print(f"Distinct Districts: {len(districts)}")
        print(f"Distinct Crops: {len(crops)}")
        print(f"Minimum Crop Year: {min_year if min_year != 9999 else 'N/A'}")
        print(f"Maximum Crop Year: {max_year if max_year != 0 else 'N/A'}")
        print(f"Total Karnataka Records: {karnataka_count}")
        print(f"Total Chikkamagaluru Records: {chikkamagaluru_count}")
        print("==============================================\n")
        
    except Exception as e:
        print(f"Error during import: {e}")
        db.rollback()
        sys.exit(1)
    finally:
        db.close()

if __name__ == "__main__":
    main()
