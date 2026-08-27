import os
import logging
import urllib.request
import urllib.parse
import urllib.error
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException

from ..models.orm_models import GovernmentCropCache
from .crop_api_service import GovernmentCropDataUnavailableException

# Set up logging
logger = logging.getLogger("krishivision")

def normalize_state_name(state: str) -> str:
    if not state:
        return ""
    state = state.strip().lower()
    if state == "orissa":
        state = "odisha"
    # Title Case each word
    words = state.split()
    return " ".join(w.capitalize() for w in words)

def normalize_district_name(district: str) -> str:
    if not district:
        return ""
    district = district.strip().lower()
    if district.endswith(" district"):
        district = district[:-9].strip()
    
    # Map district names to match data.gov.in official dataset naming conventions
    mappings = {
        "belagavi": "belgaum",
        "mysuru": "mysore",
        "bengaluru urban": "bangalore",
        "bengaluru rural": "bangalore rural",
        "kalaburagi": "gulbarga",
        "shivamogga": "shimoga",
        "tumakuru": "tumkur",
        "vijayapura": "bijapur",
        "ballari": "bellary",
        "chikkamagaluru": "chikmagalur",
        "mangaluru": "south kanara"
    }
    district = mappings.get(district, district)
    # data.gov.in uses UPPERCASE for district names
    return district.upper()

def get_api_key() -> str:
    # Read strictly from environment/dot-env config
    return os.getenv("DATA_GOV_API_KEY", "")

def get_base_url() -> str:
    return os.getenv("DATA_GOV_BASE_URL", "https://api.data.gov.in/resource/35be999b-0208-4354-b557-f6ca9a5355de")

def fetch_government_crops(db: Session, state: str, district: str) -> dict:
    normalized_state = normalize_state_name(state)
    normalized_district = normalize_district_name(district)

    # Safe logging (Never log API keys or user info)
    print("[DATA_GOV] Requesting district crop data")
    print(f"[DATA_GOV] State: {normalized_state}")
    print(f"[DATA_GOV] District: {normalized_district}")

    # Cache record query (exact state and district match)
    cache_record = db.query(GovernmentCropCache).filter(
        GovernmentCropCache.state == normalized_state,
        GovernmentCropCache.district == normalized_district
    ).first()

    # Attempt live API fetch first if key is configured
    api_key = get_api_key()
    base_url = get_base_url()
    
    configured = bool(api_key and api_key.strip() and api_key != "YOUR_PERSONAL_DATA_GOV_API_KEY")
    
    if configured:
        # Fetch all pages from live API
        import time
        limit = 1000
        offset = 0
        records = []
        try:
            while True:
                query_params = {
                    "api-key": api_key,
                    "format": "json",
                    "offset": offset,
                    "limit": limit,
                    "filters[state_name]": normalized_state,
                    "filters[district_name]": normalized_district
                }
                encoded_params = urllib.parse.urlencode(query_params)
                full_url = f"{base_url}?{encoded_params}"

                req = urllib.request.Request(
                    full_url,
                    headers={
                        "Accept": "application/json",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    }
                )
                
                # Fetch with retry logic
                max_retries = 2
                retry_delay = 1.0
                page_records = None
                total = 0
                for attempt in range(max_retries):
                    try:
                        with urllib.request.urlopen(req, timeout=3.0) as response:
                            res_data = response.read().decode('utf-8')
                            res_json = json.loads(res_data)
                            page_records = res_json.get("records", [])
                            total = res_json.get("total", 0)
                            break
                    except urllib.error.HTTPError as he:
                        if he.code == 429 and attempt < max_retries - 1:
                            logger.warning(f"[DATA_GOV] Rate limited (429). Retrying in {retry_delay}s...")
                            time.sleep(retry_delay)
                            retry_delay *= 2.0
                        else:
                            raise he
                    except Exception as e:
                        raise e

                if page_records is None:
                    raise Exception("Failed to retrieve API records after retries.")

                records.extend(page_records)
                if len(records) >= total or not page_records:
                    break
                offset += limit
                time.sleep(0.5)
                
            # Map raw fields to clean response schema with safe fallbacks
            mapped_crops = []
            for r in records:
                crop_name = r.get("Crop") or r.get("crop")
                season = r.get("Season") or r.get("season")
                year_val = r.get("Crop_Year") or r.get("crop_year")
                area_val = r.get("Area") or r.get("area") or r.get("area_")
                prod_val = r.get("Production") or r.get("production") or r.get("production_")
                
                if not crop_name or not season:
                    continue

                # Handle conversions safely
                try:
                    area = float(area_val) if area_val is not None else None
                except ValueError:
                    area = None

                try:
                    production = float(prod_val) if prod_val is not None else None
                except ValueError:
                    production = None

                try:
                    year = int(float(year_val)) if year_val is not None else None
                except ValueError:
                    year = None

                mapped_crops.append({
                    "crop_name": crop_name,
                    "season": season,
                    "year": year,
                    "area": area,
                    "production": production,
                })

            # Deduplicate by (crop_name, season) keeping the latest year
            latest_crops = {}
            for item in mapped_crops:
                key = (item["crop_name"].strip().lower(), item["season"].strip().lower())
                existing = latest_crops.get(key)
                if not existing:
                    latest_crops[key] = item
                else:
                    item_year = item["year"] or 0
                    existing_year = existing["year"] or 0
                    if item_year > existing_year:
                        latest_crops[key] = item

            final_crops = list(latest_crops.values())
            
            # Compute yield dynamically for the chosen latest records
            for item in final_crops:
                area = item.get("area")
                prod = item.get("production")
                yield_val = None
                try:
                    if area is not None and prod is not None and area > 0:
                        yield_val = round(prod / area, 2)
                except Exception:
                    pass
                item["yield"] = yield_val
            
            print(f"[DATA_GOV] Live API fetch successful. Records after deduplication: {len(final_crops)}")

            # Update/Create cache record
            now = datetime.utcnow()
            if cache_record:
                cache_record.data = final_crops
                cache_record.created_at = now
            else:
                new_cache = GovernmentCropCache(
                    state=normalized_state,
                    district=normalized_district,
                    data=final_crops,
                    created_at=now
                )
                db.add(new_cache)
            db.commit()

            return {
                "state": normalized_state,
                "district": normalized_district,
                "crops": final_crops,
                "source": "Government of India – data.gov.in",
                "cached": False,
                "data_type": "government_crop_statistics"
            }

        except Exception as e:
            logger.error(f"[DATA_GOV] Live API fetch error: {e}. Falling back to cache.")

    # Fall back to exact State + District cache if available
    if cache_record:
        print(f"[DATA_GOV] Cache HIT (Fallback) for State: {normalized_state}, District: {normalized_district}")
        cache_data = cache_record.data
        if isinstance(cache_data, dict) and "crop_records" in cache_data:
            crops_list = cache_data["crop_records"]
        else:
            crops_list = cache_data
        
        # Deduplicate cache data just in case it contains duplicates
        latest_crops = {}
        for item in crops_list:
            crop_name = item.get("crop_name") or item.get("crop")
            season = item.get("season")
            year = item.get("year") or item.get("crop_year")
            area = item.get("area")
            production = item.get("production")
            
            if not crop_name or not season:
                continue
                
            key = (crop_name.strip().lower(), season.strip().lower())
            existing = latest_crops.get(key)
            if not existing:
                latest_crops[key] = {
                    "crop_name": crop_name,
                    "season": season,
                    "year": year,
                    "area": area,
                    "production": production,
                }
            else:
                item_year = year or 0
                existing_year = existing["year"] or 0
                if item_year > existing_year:
                    latest_crops[key] = {
                        "crop_name": crop_name,
                        "season": season,
                        "year": year,
                        "area": area,
                        "production": production,
                    }
                    
        final_cache_crops = list(latest_crops.values())
        for item in final_cache_crops:
            area = item.get("area")
            prod = item.get("production")
            yield_val = None
            try:
                if area is not None and prod is not None and area > 0:
                    yield_val = round(prod / area, 2)
            except Exception:
                pass
            item["yield"] = yield_val

        return {
            "state": normalized_state,
            "district": normalized_district,
            "crops": final_cache_crops,
            "source": "Cached government data",
            "cached": True,
            "data_type": "government_crop_statistics"
        }
    else:
        # Neither live API works nor cache exists
        raise GovernmentCropDataUnavailableException(
            "Government crop data temporarily unavailable"
        )

