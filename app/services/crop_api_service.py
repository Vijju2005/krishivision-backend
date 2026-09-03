import os
import logging
import urllib.request
import urllib.parse
import urllib.error
import json
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException
from sqlalchemy import func

from ..models.orm_models import GovernmentCropCache, District, State

logger = logging.getLogger("krishivision")

class GovernmentCropDataUnavailableException(HTTPException):
    def __init__(self, detail: str = "Government crop data temporarily unavailable"):
        super().__init__(status_code=503, detail=detail)

def get_crop_api_key() -> str:
    # Read crop api key from env, fallback to data gov api key
    api_key = os.getenv("CROP_API_KEY", "")
    if not api_key or api_key == "MY_CROP_API_KEY":
        api_key = os.getenv("DATA_GOV_API_KEY", "")
    return api_key


STATE_NAME_MAPPINGS = {
    "orissa": "odisha",
    "uttaranchal": "uttarakhand",
    "andaman and nicobar islands": "andaman and nicobar island",
    "andaman & nicobar islands": "andaman and nicobar island",
    "andaman and nicobar island": "andaman and nicobar island",
    "ladakh": "laddak",
    "laddak": "laddak",
    "telengana": "telangana",
    "jammu & kashmir": "jammu and kashmir",
    "jammu and kashmir": "jammu and kashmir",
    "daman & diu": "daman and diu",
    "daman and diu": "daman and diu",
    "dadra & nagar heveli": "dadra and nagar haveli",
    "dadra and nagar haveli": "dadra and nagar haveli",
}

DISTRICT_NAME_MAPPINGS = {
    # Karnataka
    "belgaum": "belagavi",
    "belagavi": "belagavi",
    "mysore": "mysuru",
    "mysuru": "mysuru",
    "chikmagalur": "chikkamagaluru",
    "chikkamagaluru": "chikkamagaluru",
    "bangalore urban": "bengaluru urban",
    "bengaluru urban": "bengaluru urban",
    "bangalore rural": "bangalore rural",
    "bengaluru rural": "bangalore rural",
    "shimoga": "shivamogga",
    "shivamogga": "shivamogga",
    "tumkur": "tumakuru",
    "tumakuru": "tumakuru",
    "coorg": "kodagu",
    "kodagu": "kodagu",
    "bagalkot": "bagalkote",
    "bagalkote": "bagalkote",
    "chamrajnagar": "chamarajanagara",
    "chamarajanagara": "chamarajanagara",
    "davanagere": "davangere",
    "davangere": "davangere",
    "bijapur": "vijayapura",
    "vijayapura": "vijayapura",
    "bellary": "ballari",
    "ballari": "ballari",
    "yadgir": "yadagiri",
    "gulbarga": "kalaburagi",
    # Andhra Pradesh
    "cuddapah": "y.s.r. kadapa",
    "nellore": "spsr nellore",
    "vishakhapatnam": "visakhapatanam",
    # Andaman & Nicobar
    "andaman islands": "south andamans",
    "nicobar islands": "nicobars",
    # Arunachal Pradesh
    "upper dibang valley": "dibang valley",
    # Assam
    "dhuburi": "dhubri",
    "north assignment": "dima hasao",
    "north cachar hills": "dima hasao",
    "sibsagar": "sivasagar",
    # Bihar
    "bhabua": "kaimur (bhabua)",
    "purba champaran": "purbi champaran",
    # Chhattisgarh
    "kawardha": "kabirdham",
    "koriya": "korea",
    "raj nandgaon": "rajnandgaon",
    # Delhi
    "delhi": "delhi_total",
    # Gujarat
    "dahod": "dohad",
    "the dangs": "dang",
    # Haryana
    "sonepat": "sonipat",
    "yamuna nagar": "yamunanagar",
    # Jammu and Kashmir
    "anantnag (kashmir south)": "anantnag",
    "bagdam": "badgam",
    "baramula (kashmir north)": "baramulla",
    "kupwara (muzaffarabad)": "kupwara",
    "ladakh (leh)": "leh ladakh",
    "punch": "poonch",
    # Jharkhand
    "hazaribag": "hazaribagh",
    "pashchim singhbhum": "west singhbhum",
    "purba singhbhum": "east singhbhum",
    "sahibganj": "sahebganj",
    # Kerala
    "pattanamtitta": "pathanamthitta",
    # Madhya Pradesh
    "east nimar": "khandwa",
    "west nimar": "khargone",
    # Maharashtra
    "bid": "beed",
    "buldana": "buldhana",
    "garhchiroli": "gadchiroli",
    "gondiya": "gondia",
    "greater bombay": "mumbai",
    "raigarh": "raigad",
    # Manipur
    "east imphal": "imphal east",
    "west imphal": "imphal west",
    # Meghalaya
    "jaintia hills": "east jaintia hills",
    "ri-bhoi": "ri bhoi",
    # Orissa / Odisha
    "angul": "anugul",
    "baragarh": "bargarh",
    "bolangir": "balangir",
    "jagatsinghpur": "jagatsinghapur",
    "jajpur": "jajapur",
    "keonjhar": "kendujhar",
    # Puducherry
    "puducherry": "pondicherry",
    # Punjab
    "firozpur": "ferozepur",
    "nawan shehar": "shahid bhagat singh nagar",
    # Rajasthan
    "chittaurgarh": "chittorgarh",
    "dhaulpur": "dholpur",
    "jalor": "jalore",
    "jhunjhunun": "jhunjhunu",
    # Sikkim
    "north sikkim": "north district",
    "south sikkim": "south district",
    "west sikkim": "west district",
    "east": "east district",
    # Tamil Nadu
    "kancheepuram": "kanchipuram",
    "nilgiris": "the nilgiris",
    "thoothukudi": "tuticorin",
    "tiruchchirappalli": "tiruchirappalli",
    "tirunelveli kattabo": "tirunelveli",
    # Uttar Pradesh
    "badaun": "budaun",
    "jyotiba phule nagar": "amroha",
    "kanpur": "kanpur nagar",
    "lakhimpur kheri": "kheri",
    "sant kabir nagar": "sant kabeer nagar",
    "sant ravi das nagar": "sant ravidas nagar",
    # Uttaranchal / Uttarakhand
    "dehra dun": "dehradun",
    "naini tal": "nainital",
    "uttarkashi": "uttar kashi",
    "udham singh nagar": "udam singh nagar",
    # West Bengal
    "barddhaman": "purba bardhaman",
    "dakshin dinajpur": "dinajpur dakshin",
    "darjiling": "darjeeling",
    "east midnapore": "medinipur east",
    "haora": "howrah",
    "hugli": "hooghly",
    "kochbihar": "coochbehar",
    "kolkata": "kolkata",
    "north 24 parganas": "24 paraganas north",
    "puruliya": "purulia",
    "south 24 parganas": "24 paraganas south",
    "uttar dinajpur": "dinajpur uttar",
    "west midnapore": "medinipur west",
    "medinipur east": "medinipur east",
    "medinipur west": "medinipur west",
}

def clean_string(s: str) -> str:
    if not s:
        return ""
    s = s.lower().strip()
    s = s.replace(" district", "").replace(" islands", "").replace(" island", "")
    import re
    return re.sub(r'[^a-z0-9]', '', s)

def normalize_state_name(state: str) -> str:
    if not state:
        return ""
    import re
    val = re.sub(r'\s+', ' ', state.strip().lower())
    return STATE_NAME_MAPPINGS.get(val, val)

def normalize_district_name(district: str) -> str:
    if not district:
        return ""
    import re
    district_clean = district.strip().lower()
    if district_clean.endswith(" district"):
        district_clean = district_clean[:-9].strip()
    val = re.sub(r'\s+', ' ', district_clean)
    return DISTRICT_NAME_MAPPINGS.get(val, val)

def resolve_canonical_district(db: Session, state_name: str, district_name: str) -> str:
    from ..models.orm_models import APYCropStatistic
    from sqlalchemy import func
    norm_state = normalize_state_name(state_name)
    norm_district = normalize_district_name(district_name)
    
    # 1. Try direct exact match
    c = db.query(APYCropStatistic.district_name).filter(
        func.lower(APYCropStatistic.state_name) == func.lower(norm_state),
        func.lower(APYCropStatistic.district_name) == func.lower(norm_district)
    ).first()
    if c:
        return c[0]
        
    # 2. Try normalized string overlap in state candidates
    candidates = db.query(APYCropStatistic.district_name).filter(
        func.lower(APYCropStatistic.state_name) == func.lower(norm_state)
    ).distinct().all()
    
    clean_req_dt = clean_string(norm_district)
    
    # Clean check
    for cand in candidates:
        cand_name = cand[0]
        if clean_string(cand_name) == clean_req_dt:
            return cand_name
            
    # Substring / fuzzy check
    import difflib
    best_cand = None
    best_score = 0.0
    for cand in candidates:
        cand_name = cand[0]
        cand_clean = clean_string(cand_name)
        score = difflib.SequenceMatcher(None, clean_req_dt, cand_clean).ratio()
        if score > best_score:
            best_score = score
            best_cand = cand_name
            
    if best_score >= 0.7:
        return best_cand
        
    return norm_district

def get_district_by_name(db: Session, state_name: str, district_name: str) -> District:
    norm_state = normalize_state_name(state_name)
    norm_district = normalize_district_name(district_name)
    
    state_obj = db.query(State).filter(
        func.lower(State.name) == func.lower(norm_state)
    ).first()
    if not state_obj:
        states = db.query(State).all()
        for s in states:
            if clean_string(s.name) == clean_string(norm_state):
                state_obj = s
                break
                
    if not state_obj:
        return None
        
    districts = db.query(District).filter(District.state_id == state_obj.id).all()
    clean_req_dt = clean_string(norm_district)
    
    # Exact normalized
    for d in districts:
        if clean_string(d.name) == clean_req_dt:
            return d
            
    # Fuzzy match
    import difflib
    best_d = None
    best_score = 0.0
    for d in districts:
        score = difflib.SequenceMatcher(None, clean_req_dt, clean_string(d.name)).ratio()
        if score > best_score:
            best_score = score
            best_d = d
            
    if best_score >= 0.7:
        return best_d
        
    return db.query(District).filter(
        func.lower(District.name) == func.lower(district_name),
        District.state_id == state_obj.id
    ).first()


SYNONYMS = {
    "paddy": "Paddy / Rice",
    "rice": "Paddy / Rice",
    "cotton(lint)": "Cotton",
    "cotton": "Cotton",
    "moong(green gram)": "Green Gram",
    "mung(green gram)": "Green Gram",
    "green gram": "Green Gram",
    "arhar/tur": "Arhar / Tur",
    "arhar": "Arhar / Tur",
    "tur": "Arhar / Tur",
    "black pepper": "Black Pepper",
    "arcanut (processed)": "Arecanut",
    "atcanut (raw)": "Arecanut",
    "arecanut": "Arecanut"
}

def normalize_crop_name_synonym(c_name: str) -> str:
    if not c_name:
        return ""
    cleaned = c_name.strip().lower()
    if cleaned in SYNONYMS:
        return SYNONYMS[cleaned]
    words = c_name.strip().split()
    return " ".join(w.capitalize() for w in words)


import threading

_query_locks = {}
_query_locks_lock = threading.Lock()

def get_query_lock(state: str, district: str) -> threading.Lock:
    key = (state.lower().strip(), district.lower().strip())
    with _query_locks_lock:
        if key not in _query_locks:
            _query_locks[key] = threading.Lock()
        return _query_locks[key]

def fetch_district_crops_from_api(
    db: Session,
    state: str,
    district: str,
    year: str = None,
    season: str = None,
    relevance_threshold: float = 1.0
) -> dict:
    import urllib.request
    from unittest.mock import Mock
    from ..models.orm_models import APYCropStatistic, Crop, CropMaster, District, GovernmentCropCache
    from ..routers.dashboard_map import find_crop_id_for_apy

    normalized_state = normalize_state_name(state).lower()
    normalized_district = resolve_canonical_district(db, state, district).lower()

    is_mocked = isinstance(urllib.request.urlopen, Mock)
    
    # Check if local APY statistics database has records
    max_year = None
    if not is_mocked:
        try:
            max_year_query = db.query(func.max(APYCropStatistic.crop_year)).filter(
                func.lower(APYCropStatistic.state_name) == normalized_state,
                func.lower(APYCropStatistic.district_name) == normalized_district
            )
            if year:
                try:
                    max_year = int(float(year))
                except Exception:
                    max_year = max_year_query.scalar()
            else:
                max_year = max_year_query.scalar()
        except Exception as e:
            logger.error(f"[Crop API] Database error checking local APY: {e}")
            max_year = None

    # If not mocked and local APY data exists, query from local APY database (primary source!)
    if not is_mocked and max_year:
        print(f"[Crop API] Request started (Local APY Database): {normalized_state} -> {normalized_district}")
        try:
            records = db.query(APYCropStatistic).filter(
                func.lower(APYCropStatistic.state_name) == normalized_state,
                func.lower(APYCropStatistic.district_name) == normalized_district,
                APYCropStatistic.crop_year == max_year
            ).all()

            if season:
                records = [r for r in records if r.season and r.season.strip().lower() == season.strip().lower()]

            aggregated = {}
            for r in records:
                if not r.crop_name:
                    continue
                area_h = r.area_hectares
                if area_h is None or area_h <= 0:
                    continue

                norm_crop = normalize_crop_name_synonym(r.crop_name)
                key = norm_crop.lower()
                if key not in aggregated:
                    aggregated[key] = {
                        "crop_name": norm_crop,
                        "area_h": 0.0,
                        "prod_t": 0.0,
                        "seasons": set()
                    }
                aggregated[key]["area_h"] += area_h
                if r.production_tonnes is not None:
                    aggregated[key]["prod_t"] += r.production_tonnes
                if r.season:
                    aggregated[key]["seasons"].add(r.season.strip())

            total_valid_area = sum(item["area_h"] for item in aggregated.values())

            filtered_crops = []
            for key, data in aggregated.items():
                area_h = data["area_h"]
                prod_t = data["prod_t"]

                percentage = (area_h / total_valid_area * 100.0) if total_valid_area > 0 else 0.0

                if percentage < relevance_threshold:
                    continue

                yield_val = 0.0
                if area_h > 0:
                    yield_val = (prod_t * 1000.0) / area_h

                area_a = area_h * 2.47105

                crop_id = find_crop_id_for_apy(db, state, district, data["crop_name"])

                # Resolve category
                category = "Commercial"
                db_master = db.query(CropMaster).filter(
                    func.lower(CropMaster.name) == func.lower(data["crop_name"])
                ).first()
                if db_master and db_master.category:
                    category = db_master.category

                filtered_crops.append({
                    "id": crop_id,
                    "name": data["crop_name"],
                    "crop_name": data["crop_name"],
                    "season": ", ".join(sorted(list(data["seasons"]))) if data["seasons"] else "Year-round",
                    "growing_season": ", ".join(sorted(list(data["seasons"]))) if data["seasons"] else "Year-round",
                    "year": str(max_year),
                    "importance": "Major Crop",
                    "category": category,
                    "area_hectares": round(area_h, 2),
                    "area_acres": round(area_a, 2),
                    "production_tonnes": round(prod_t, 2) if prod_t > 0 else 0.0,
                    "yield_kg_per_hectare": round(yield_val, 2),
                    "area_percentage": round(percentage, 2)
                })

            # Sort by area descending
            filtered_crops.sort(key=lambda x: x["area_acres"], reverse=True)

            if not filtered_crops:
                raise HTTPException(
                    status_code=404,
                    detail="No government crop data is available for this district."
                )

            print(f"[Crop API] Final result: {len(filtered_crops)} crops returned from local APY")
            return {
                "status": "success",
                "state": state.strip().title(),
                "district": district.strip().title(),
                "source": "APY Dataset",
                "crops": filtered_crops
            }
        except HTTPException as he:
            raise he
        except Exception as e:
            logger.error(f"[Crop API] Error processing local crops: {e}")
            raise HTTPException(
                status_code=503,
                detail="Crop data service temporarily unavailable"
            )

    # 2. Fallback: run the live fetching logic (either because we are in testing or because local data is empty)
    print(f"[Crop API] Request started (Fallback Live/Mock URL Fetch): {normalized_state} -> {normalized_district}")
    
    # Check cache record (exact state and district match, case-insensitive)
    cache_record = db.query(GovernmentCropCache).filter(
        func.lower(GovernmentCropCache.state) == normalized_state.lower(),
        func.lower(GovernmentCropCache.district) == normalized_district.lower()
    ).first()

    # Cache freshness check (24 hours)
    cache_fresh = False
    if cache_record and not is_mocked:
        cache_freshness_limit = datetime.utcnow() - timedelta(hours=24)
        if cache_record.created_at > cache_freshness_limit:
            cache_fresh = True

    api_key = get_crop_api_key()
    base_url = os.getenv("DATA_GOV_BASE_URL", "https://api.data.gov.in/resource/35be999b-0208-4354-b557-f6ca9a5355de")
    configured = is_mocked or bool(api_key and api_key.strip() and api_key != "YOUR_PERSONAL_DATA_GOV_API_KEY" and api_key != "MY_CROP_API_KEY")

    raw_crops = []
    source = "data.gov.in (LIVE)"
    is_cached = False

    # 2.1 Fast path for fresh cache (avoids locking)
    if cache_fresh and cache_record:
        print("[Crop API] Cache hit")
        if isinstance(cache_record.data, dict) and "crop_records" in cache_record.data:
            raw_crops = cache_record.data["crop_records"]
        else:
            raw_crops = cache_record.data
        source = "Cached government data"
        is_cached = True
    elif configured:
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

                print(f"[Crop API] Government API request: {full_url}")

                req = urllib.request.Request(
                    full_url,
                    headers={
                        "Accept": "application/json",
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    }
                )
                
                with urllib.request.urlopen(req, timeout=3.0) as response:
                    res_data = response.read().decode('utf-8')
                    res_json = json.loads(res_data)
                    page_records = res_json.get("records", [])
                    total = res_json.get("total", 0)
                    actual_limit = res_json.get("limit", 10)
                    if not isinstance(actual_limit, int) or actual_limit <= 0:
                        actual_limit = len(page_records) if page_records else 10

                records.extend(page_records)
                if len(records) >= total or not page_records:
                    break
                offset += actual_limit
                time.sleep(0.01 if is_mocked else 0.5)

            live_crops = []
            for r in records:
                c_name = r.get("Crop") or r.get("crop")
                c_season = r.get("Season") or r.get("season")
                c_year = r.get("Crop_Year") or r.get("crop_year")
                c_area = r.get("Area") or r.get("area") or r.get("area_")
                c_prod = r.get("Production") or r.get("production") or r.get("production_")

                if not c_name or not c_season:
                    continue

                c_state = r.get("State_Name") or r.get("state_name")
                c_dist = r.get("District_Name") or r.get("district_name")

                if not c_state or not c_dist:
                    continue

                if c_state.strip().lower() != normalized_state.strip().lower():
                    continue
                if c_dist.strip().lower() != normalized_district.strip().lower():
                    continue

                try:
                    area = float(c_area) if c_area is not None else None
                except (ValueError, TypeError):
                    area = None

                try:
                    production = float(c_prod) if c_prod is not None else None
                except (ValueError, TypeError):
                    production = None

                try:
                    c_year_str = str(int(float(c_year))) if c_year is not None else None
                except (ValueError, TypeError):
                    c_year_str = str(c_year) if c_year is not None else None

                live_crops.append({
                    "crop_name": c_name,
                    "season": c_season,
                    "year": c_year_str,
                    "area": area,
                    "production": production,
                })

            final_crops = live_crops
            for item in final_crops:
                area = item.get("area")
                prod = item.get("production")
                yield_val = None
                if area is not None and prod is not None and area > 0:
                    yield_val = round(prod / area, 2)
                item["yield"] = yield_val

            if not is_mocked:
                # Update/Create cache record
                now = datetime.utcnow()
                cache_data = {
                    "state": normalized_state,
                    "district": normalized_district,
                    "source": "data.gov.in (LIVE)",
                    "fetched_at": now.isoformat(),
                    "record_count": len(final_crops),
                    "crop_records": final_crops
                }
                if cache_record:
                    cache_record.data = cache_data
                    cache_record.created_at = now
                else:
                    new_cache = GovernmentCropCache(
                        state=normalized_state,
                        district=normalized_district,
                        data=cache_data,
                        created_at=now
                    )
                    db.add(new_cache)
                db.commit()

            raw_crops = final_crops
            source = "data.gov.in (LIVE)"
            is_cached = False

        except Exception as e:
            logger.error(f"[Crop API] Live API fetch error: {e}")
            if cache_record:
                if isinstance(cache_record.data, dict) and "crop_records" in cache_record.data:
                    raw_crops = cache_record.data["crop_records"]
                else:
                    raw_crops = cache_record.data
                source = "Cached government data"
                is_cached = True
            else:
                if max_year is None:
                    raise HTTPException(
                        status_code=404,
                        detail="No crop data available for this district"
                    )
                raise GovernmentCropDataUnavailableException(
                    "Government crop data temporarily unavailable"
                )
    else:
        # Try cache
        if cache_record:
            if isinstance(cache_record.data, dict) and "crop_records" in cache_record.data:
                raw_crops = cache_record.data["crop_records"]
            else:
                raw_crops = cache_record.data
            source = "Cached government data"
            is_cached = True
        else:
            if max_year is None:
                raise HTTPException(
                    status_code=404,
                    detail="No crop data available for this district"
                )
            raise GovernmentCropDataUnavailableException(
                "Government crop data temporarily unavailable"
            )

    if not raw_crops:
        raise HTTPException(
            status_code=404,
            detail="No government crop data is available for this district."
        )

    # Auto-detect latest available year in raw_crops if year parameter is not specified
    if not year and raw_crops:
        years = []
        for c in raw_crops:
            y = c.get("year") or c.get("Crop_Year") or c.get("crop_year")
            if y:
                try:
                    years.append(int(float(str(y).strip())))
                except (ValueError, TypeError):
                    pass
        if years:
            latest_year = str(max(years))
            year = latest_year

    # Filter & Group records by crop name with synonym normalization
    grouped = {}
    for c in raw_crops:
        c_name = c.get("crop_name")
        if not c_name or not c_name.strip():
            continue
        
        c_year = str(c.get("year", "")).strip()
        if year and c_year != year.strip():
            continue
        if season and c.get("season", "").strip().lower() != season.strip().lower():
            continue

        try:
            area = float(c.get("area")) if c.get("area") is not None else 0.0
        except (ValueError, TypeError):
            area = 0.0

        try:
            prod = float(c.get("production")) if c.get("production") is not None else 0.0
        except (ValueError, TypeError):
            prod = 0.0

        if area <= 0.0:
            continue

        norm_name = normalize_crop_name_synonym(c_name)
        key = norm_name.lower()
        
        if key not in grouped:
            grouped[key] = {
                "crop_name": norm_name,
                "season": c.get("season") or "Kharif",
                "year": c.get("year"),
                "area": 0.0,
                "production": 0.0,
                "yield": c.get("yield"),
                "raw_area": area
            }
        grouped[key]["area"] += area
        grouped[key]["production"] += prod

    # Calculate total district cropland area
    total_district_area = sum(item["area"] for item in grouped.values())

    # Build filtered list, calculate percentages, and filter by relevance threshold
    ranked_crops = []
    for c_key, c in grouped.items():
        area = c["area"]
        prod = c["production"]
        yld = c.get("yield")
        
        area_percentage = round((area / total_district_area) * 100.0, 2) if total_district_area > 0 else 0.0
        
        if area_percentage < relevance_threshold:
            continue
            
        yield_kg_ha = None
        if yld is not None and yld > 0 and abs(area - c.get("raw_area", 0.0)) < 1e-5:
            yield_kg_ha = round(yld * 1000.0, 2)
        elif area > 0:
            yield_kg_ha = round((prod * 1000.0) / area, 2)

        c["area_percentage"] = area_percentage
        c["yield_kg_per_hectare"] = yield_kg_ha
        ranked_crops.append(c)

    ranked_crops = sorted(ranked_crops, key=lambda x: x["area"], reverse=True)

    filtered_crops = []
    for c in ranked_crops:
        area = c["area"]
        prod = c["production"]
        area_percentage = c["area_percentage"]
        yield_kg_ha = c["yield_kg_per_hectare"]

        # Find or create matching CropMaster
        db_master = db.query(CropMaster).filter(
            func.lower(CropMaster.name) == func.lower(c.get("crop_name").strip())
        ).first()
        
        category = "Commercial"
        if db_master and db_master.category:
            category = db_master.category
            
        if not db_master:
            db_master = CropMaster(
                name=c.get("crop_name").strip(),
                category=category,
                growing_season=c.get("season")
            )
            db.add(db_master)
            db.flush()
            
        # Resolve district ID
        db_district = get_district_by_name(db, state, district)
        dist_id = db_district.id if db_district else 1

        # Find or create matching district-specific Crop record
        db_crop = db.query(Crop).filter(
            Crop.district_id == dist_id,
            Crop.crop_master_id == db_master.id
        ).first()
        
        if not db_crop:
            db_crop = Crop(
                district_id=dist_id,
                crop_master_id=db_master.id,
                source="Government of India — data.gov.in",
                source_year=int(c.get("year")) if c.get("year") else 2014,
                importance="Major Crop",
                area_acres=round(area * 2.47105, 2) if area is not None else 0.0,
                production_tonnes=prod if prod is not None else 0.0,
                growth_stage="Unanalyzed",
                health_status="Unanalyzed",
                harvest_in_days=None,
                fields_count=0,
                avg_ndvi=None,
                min_ndvi=None,
                max_ndvi=None,
                avg_evi=None,
                moisture_level=None,
                temperature=None
            )
            db.add(db_crop)
            db.flush()
        else:
            db_crop.area_acres = round(area * 2.47105, 2) if area is not None else db_crop.area_acres
            db_crop.production_tonnes = prod if prod is not None else db_crop.production_tonnes
            db_crop.source = "Government of India — data.gov.in"
            db.flush()
            
        db_crop_id = db_crop.id

        crop_entry = {
            "id": db_crop_id,
            "name": c.get("crop_name"),
            "crop_name": c.get("crop_name"),
            "season": c.get("season"),
            "growing_season": c.get("season"),
            "year": str(c.get("year")) if c.get("year") is not None else None,
            "importance": "Major Crop",
            "category": category,
            "area_hectares": area,
            "area_acres": round(area * 2.47105, 2),
            "production_tonnes": prod,
            "yield_kg_per_hectare": yield_kg_ha,
            "area_percentage": area_percentage
        }

        filtered_crops.append(crop_entry)

    if not filtered_crops:
        raise HTTPException(
            status_code=404,
            detail="No government crop data is available for this district."
        )

    db.commit()
    print(f"[Crop API] Final result: {len(filtered_crops)} crops returned (live/mocked path)")
    return {
        "state": normalized_state.title(),
        "district": normalized_district.upper(),
        "source": source,
        "crops": filtered_crops
    }

