import os
import json
import time
import logging
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException

from ..models.orm_models import Crop, District, AgroMonitoringPolygon, SatelliteAnalysisCache

logger = logging.getLogger("krishivision")

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

def get_agromonitoring_api_key() -> str:
    key = os.getenv("AGROMONITORING_API_KEY", "")
    return key.strip()

def extract_flat_coordinates(boundary_geojson) -> list:
    if not boundary_geojson:
        return []
    
    geom = None
    if isinstance(boundary_geojson, str):
        try:
            geom = json.loads(boundary_geojson)
        except Exception:
            return []
    elif isinstance(boundary_geojson, dict):
        geom = boundary_geojson
    else:
        return []

    g_type = geom.get("type")
    coords = geom.get("coordinates")
    if not coords or not isinstance(coords, list):
        return []
    
    flat = []
    try:
        if g_type == "Polygon":
            ring = coords[0]
            for pt in ring:
                if isinstance(pt, list) and len(pt) >= 2:
                    flat.append((float(pt[0]), float(pt[1])))
        elif g_type == "MultiPolygon":
            for poly in coords:
                if poly and isinstance(poly, list):
                    ring = poly[0]
                    for pt in ring:
                        if isinstance(pt, list) and len(pt) >= 2:
                            flat.append((float(pt[0]), float(pt[1])))
    except Exception as e:
        logger.error(f"[AgroMonitoring] Error extracting coords: {e}")
    return flat

def calculate_centroid(flat_coords: list) -> tuple:
    if not flat_coords:
        return (75.9200, 14.4650) # Fallback to Karnataka center
    sum_lng = sum(pt[0] for pt in flat_coords)
    sum_lat = sum(pt[1] for pt in flat_coords)
    n = len(flat_coords)
    return (sum_lng / n, sum_lat / n)

def make_agromonitoring_request(url: str, method: str = "GET", data_dict: dict = None) -> dict:
    req_start = time.time()
    headers = {
        "Accept": "application/json",
        "User-Agent": "KrishiVisionBackend/1.0"
    }
    
    api_key = get_agromonitoring_api_key()
    if not api_key or not api_key.strip():
        raise HTTPException(status_code=503, detail="AgroMonitoring API key is not configured")

    # Redact API key from logs/errors
    safe_url = url.replace(api_key, "REDACTED_API_KEY")

    logger.info(f"[AgroMonitoring API Request] Method: {method}, URL: {safe_url}")
    
    data_bytes = None
    if data_dict:
        data_bytes = json.dumps(data_dict).encode("utf-8")
        headers["Content-Type"] = "application/json"

    req = urllib.request.Request(url, headers=headers, method=method, data=data_bytes)
    
    try:
        with urllib.request.urlopen(req, timeout=8.0) as response:
            res_data = response.read().decode("utf-8")
            elapsed = time.time() - req_start
            logger.info(f"[AgroMonitoring Response] Status: {response.getcode()}, Time: {elapsed:.4f}s")
            return json.loads(res_data)
    except urllib.error.HTTPError as he:
        elapsed = time.time() - req_start
        logger.error(f"[AgroMonitoring HTTP Error] Status: {he.code}, Time: {elapsed:.4f}s")
        # Read the error body to identify specific messages (e.g. quota exceeded)
        err_body = ""
        try:
            err_body = he.fp.read().decode("utf-8")
            logger.error(f"[AgroMonitoring HTTP Error Body] {err_body}")
        except Exception:
            pass

        if he.code in [401, 403]:
            raise HTTPException(status_code=503, detail="AgroMonitoring API authentication failed")
        elif he.code == 429:
            raise HTTPException(status_code=429, detail="AgroMonitoring API rate limit reached")
        elif he.code == 404:
            raise HTTPException(status_code=404, detail="Satellite data unavailable")
        elif he.code == 413 or "polygons anymore" in err_body or "PayloadTooLarge" in err_body:
            raise HTTPException(status_code=413, detail="AgroMonitoring API quota exceeded")
        else:
            raise HTTPException(status_code=503, detail="Satellite service temporarily unavailable")
    except Exception as e:
        elapsed = time.time() - req_start
        err_msg = str(e)
        if api_key:
            err_msg = err_msg.replace(api_key, "REDACTED_API_KEY")
        logger.error(f"[AgroMonitoring Connection Error] Time: {elapsed:.4f}s, Error: {err_msg}")
        raise HTTPException(status_code=503, detail="Satellite service temporarily unavailable")

def clean_string(s: str) -> str:
    if not s:
        return ""
    import re
    s = s.lower().strip()
    s = s.replace(" district", "").replace(" islands", "").replace(" island", "")
    return re.sub(r'[^a-z0-9]', '', s)

def get_district_obj(db: Session, state: str, district: str) -> District | None:
    if not district:
        return None
    from sqlalchemy import func
    from ..models.orm_models import State, District
    
    norm_state = normalize_state_name(state)
    norm_district = normalize_district_name(district)
    
    # 1. Direct query by exact or lower name matching
    d_obj = db.query(District).filter(
        func.lower(District.name).in_([district.strip().lower(), norm_district.strip().lower()])
    ).first()
    if d_obj:
        return d_obj
        
    # 2. Match via State filter
    state_obj = db.query(State).filter(
        func.lower(State.name).in_([state.strip().lower(), norm_state.strip().lower()])
    ).first()
    
    if not state_obj:
        states = db.query(State).all()
        clean_st = clean_string(norm_state)
        for s in states:
            if clean_string(s.name) == clean_st:
                state_obj = s
                break
                
    if state_obj:
        districts = db.query(District).filter(District.state_id == state_obj.id).all()
        clean_req = clean_string(district)
        clean_norm = clean_string(norm_district)
        for d in districts:
            cd = clean_string(d.name)
            if cd == clean_req or cd == clean_norm:
                return d
                
        import difflib
        best_d = None
        best_score = 0.0
        for d in districts:
            cd = clean_string(d.name)
            score = max(
                difflib.SequenceMatcher(None, clean_req, cd).ratio(),
                difflib.SequenceMatcher(None, clean_norm, cd).ratio()
            )
            if score > best_score:
                best_score = score
                best_d = d
        if best_score >= 0.7:
            return best_d
            
    return db.query(District).filter(
        func.lower(District.name) == func.lower(district.strip())
    ).first()

def create_or_get_polygon(db: Session, state: str, district: str, crop: str) -> str:
    from sqlalchemy import func
    from ..models.orm_models import CropMaster
    
    district_obj = get_district_obj(db, state, district)
    district_db_name = district_obj.name if district_obj else district.strip().title()
    state_db_name = district_obj.state.name if (district_obj and district_obj.state) else (state.strip().title() if state else "Karnataka")
    
    norm_state = normalize_state_name(state).title()
    norm_district = normalize_district_name(district).title()
    norm_crop = crop.strip().title()
    
    # 1. Look up in local db mapping for the exact crop across possible district name variations
    poly_record = db.query(AgroMonitoringPolygon).filter(
        AgroMonitoringPolygon.state.in_([norm_state, state_db_name]),
        AgroMonitoringPolygon.district.in_([norm_district, district_db_name, district.strip().title()]),
        AgroMonitoringPolygon.crop == norm_crop
    ).first()
    
    if poly_record:
        logger.info(f"[AgroMonitoring Match] Found local polygon ID mapping for {state_db_name} -> {district_db_name} -> {norm_crop}: {poly_record.polygon_id}")
        return poly_record.polygon_id
    
    # 2. Key not configured verification
    api_key = get_agromonitoring_api_key()
    if not api_key:
        raise HTTPException(status_code=503, detail="AgroMonitoring API key is not configured")

    # 3. Query the API for all registered polygons to check for matches by district and crop name
    api_polys = []
    try:
        list_url = f"https://api.agromonitoring.com/agro/1.0/polygons?appid={api_key}"
        api_polys = make_agromonitoring_request(list_url)
    except Exception as e:
        logger.warning(f"[AgroMonitoring API] Failed to fetch registered polygons list: {e}")

    if api_polys and isinstance(api_polys, list):
        district_search_terms = {norm_district.lower(), district_db_name.lower(), district.strip().lower()}
        for poly in api_polys:
            name = poly.get("name", "").lower()
            if any(term in name for term in district_search_terms) and norm_crop.lower() in name:
                polygon_id = poly.get("id")
                if polygon_id:
                    # Cache in local DB
                    existing_poly = db.query(AgroMonitoringPolygon).filter(AgroMonitoringPolygon.polygon_id == polygon_id).first()
                    if not existing_poly:
                        new_poly = AgroMonitoringPolygon(
                            state=state_db_name,
                            district=district_db_name,
                            crop=norm_crop,
                            polygon_id=polygon_id,
                            geojson=poly.get("geo_json") or {}
                        )
                        db.add(new_poly)
                        db.commit()
                        db.refresh(new_poly)
                    return polygon_id

    # 4. Retrieve GeoJSON from Crop database or District boundary fallback
    boundary = None
    analysis_scope = "field"

    if district_obj:
        # Search crop field geometry
        search_crop_names = [norm_crop.lower(), crop.strip().lower()]
        if "arhar" in crop.lower() or "tur" in crop.lower():
            search_crop_names.extend(["arhar / tur", "arhar/tur", "arhar", "tur", "pigeon pea"])
        elif "soy" in crop.lower():
            search_crop_names.extend(["soybean", "soyabean"])
        elif "mustard" in crop.lower() or "rapeseed" in crop.lower():
            search_crop_names.extend(["rapeseed & mustard", "rapeseed &mustard", "mustard"])

        crop_rec = db.query(Crop).filter(
            Crop.district_id == district_obj.id,
            Crop.crop_master.has(func.lower(CropMaster.name).in_(search_crop_names))
        ).first()

        if crop_rec and crop_rec.boundary_geojson:
            boundary = crop_rec.boundary_geojson
            analysis_scope = "field"

    # Fallback to District Boundary Geometry if field geometry is unavailable
    if not boundary and district_obj and district_obj.boundary_geojson:
        boundary = district_obj.boundary_geojson
        analysis_scope = "district"

    if not boundary:
        # Fallback to State boundary geometry if district boundary is also missing
        if district_obj and district_obj.state and district_obj.state.boundary_geojson:
            boundary = district_obj.state.boundary_geojson
            analysis_scope = "district"

    if not boundary:
        raise HTTPException(status_code=404, detail=f"No geometry available for {norm_crop} in {district_db_name}")

    # Create new polygon coordinates if we have a boundary
    try:
        flat_coords = extract_flat_coordinates(boundary)
        if flat_coords:
            centroid_lng, centroid_lat = calculate_centroid(flat_coords)
            # Create a small bounding box representing the field (0.014 degrees)
            d = 0.014
            coords = [
                [centroid_lng - d, centroid_lat - d],
                [centroid_lng + d, centroid_lat - d],
                [centroid_lng + d, centroid_lat + d],
                [centroid_lng - d, centroid_lat + d],
                [centroid_lng - d, centroid_lat - d]
            ]
            geojson = {
                "type": "Feature",
                "properties": {"analysis_scope": analysis_scope},
                "geometry": {
                    "type": "Polygon",
                    "coordinates": [coords]
                }
            }
            
            poly_name = f"{state_db_name}_{district_db_name}_{norm_crop}".replace(" ", "_")
            post_data = {
                "name": poly_name,
                "geo_json": geojson
            }
            
            # Try to create on API
            url = f"https://api.agromonitoring.com/agro/1.0/polygons?appid={api_key}"
            response = make_agromonitoring_request(url, method="POST", data_dict=post_data)
            polygon_id = response.get("id")
            if polygon_id:
                new_poly = AgroMonitoringPolygon(
                    state=state_db_name,
                    district=district_db_name,
                    crop=norm_crop,
                    polygon_id=polygon_id,
                    geojson=geojson
                )
                db.add(new_poly)
                db.commit()
                db.refresh(new_poly)
                logger.info(f"[AgroMonitoring Created] Created new polygon {polygon_id} (scope={analysis_scope}) for {state_db_name} -> {district_db_name} -> {norm_crop}")
                return polygon_id
    except HTTPException as he:
        logger.error(f"[AgroMonitoring Create Failed] HTTP {he.status_code}: {he.detail}")
        raise he
    except Exception as e:
        logger.error(f"[AgroMonitoring Create Error] {e}")
        raise HTTPException(status_code=500, detail="Failed to create field polygon on satellite server")

    raise HTTPException(status_code=404, detail="Crop-specific field geometry unavailable")

def fetch_satellite_indices_and_images(db: Session, state: str, district: str, crop: str) -> dict:
    norm_state = normalize_state_name(state).title()
    norm_district = normalize_district_name(district).title()
    norm_crop = crop.strip().title()

    # 0. Purge any invalid/stale cache records that have null ndvi to ensure temporary errors are never cached
    try:
        db.query(SatelliteAnalysisCache).filter(
            SatelliteAnalysisCache.state == norm_state,
            SatelliteAnalysisCache.district == norm_district,
            SatelliteAnalysisCache.crop == norm_crop,
            SatelliteAnalysisCache.ndvi.is_(None)
        ).delete()
        db.commit()
    except Exception:
        db.rollback()

    # 1. Check local cache (3 days threshold for valid satellite results)
    cache_record = db.query(SatelliteAnalysisCache).filter(
        SatelliteAnalysisCache.state == norm_state,
        SatelliteAnalysisCache.district == norm_district,
        SatelliteAnalysisCache.crop == norm_crop
    ).order_by(SatelliteAnalysisCache.fetched_at.desc()).first()

    if cache_record and cache_record.ndvi is not None:
        freshness_limit = datetime.utcnow() - timedelta(days=3)
        if cache_record.fetched_at > freshness_limit:
            logger.info(f"[AgroMonitoring Cache HIT] Found fresh satellite analysis cache for {norm_state} -> {norm_district} -> {norm_crop}")
            logger.info("Satellite provider: AgroMonitoring")
            logger.info("Authentication: SUCCESS")
            logger.info("Scene search: SUCCESS")
            logger.info("Image retrieval: SUCCESS")
            logger.info("Statistics retrieval: SUCCESS")
            logger.info(f"NDVI: {'AVAILABLE' if cache_record.ndvi is not None else 'UNAVAILABLE'}")
            logger.info(f"EVI: {'AVAILABLE' if cache_record.evi is not None else 'UNAVAILABLE'}")
            logger.info(f"NDWI: {'AVAILABLE' if cache_record.ndwi is not None else 'UNAVAILABLE'}")
            return {
                "state": cache_record.state,
                "district": cache_record.district,
                "crop": cache_record.crop,
                "polygon_id": cache_record.polygon_id,
                "observation_date": cache_record.observation_date,
                "ndvi": cache_record.ndvi,
                "evi": cache_record.evi,
                "evi2": cache_record.evi2,
                "ndwi": cache_record.ndwi,
                "nri": cache_record.nri,
                "dswi": cache_record.dswi,
                "image_urls": cache_record.image_urls,
                "statistics": cache_record.statistics,
                "source": cache_record.source,
                "fetched_at": cache_record.fetched_at.isoformat()
            }

    # 2. Get polygon ID
    polygon_auth_success = "SUCCESS"
    try:
        polygon_id = create_or_get_polygon(db, state, district, crop)
    except HTTPException as he:
        if "authentication" in str(he.detail).lower():
            polygon_auth_success = "FAILED"
        logger.info("Satellite provider: AgroMonitoring")
        logger.info(f"Authentication: {polygon_auth_success}")
        logger.info("Scene search: FAILED")
        logger.info("Image retrieval: FAILED")
        logger.info("Statistics retrieval: FAILED")
        logger.info("NDVI: UNAVAILABLE")
        logger.info("EVI: UNAVAILABLE")
        logger.info("NDWI: UNAVAILABLE")
        raise he
    except Exception as e:
        logger.info("Satellite provider: AgroMonitoring")
        logger.info("Authentication: FAILED")
        logger.info("Scene search: FAILED")
        logger.info("Image retrieval: FAILED")
        logger.info("Statistics retrieval: FAILED")
        logger.info("NDVI: UNAVAILABLE")
        logger.info("EVI: UNAVAILABLE")
        logger.info("NDWI: UNAVAILABLE")
        raise e

    api_key = get_agromonitoring_api_key()

    # 3. Search satellite scenes for the last 30 to 90 days using HTTPS
    now_ts = int(time.time()) - 300
    thirty_days_ago_ts = now_ts - (30 * 24 * 60 * 60)
    
    search_url = f"https://api.agromonitoring.com/agro/1.0/image/search?start={thirty_days_ago_ts}&end={now_ts}&polyid={polygon_id}&appid={api_key}"
    scenes = None
    scene_search_success = "FAILED"
    try:
        scenes = make_agromonitoring_request(search_url)
        if not scenes or not isinstance(scenes, list) or len(scenes) == 0:
            # Fallback to 90 days historical search window
            ninety_days_ago_ts = now_ts - (90 * 24 * 60 * 60)
            search_url_90 = f"https://api.agromonitoring.com/agro/1.0/image/search?start={ninety_days_ago_ts}&end={now_ts}&polyid={polygon_id}&appid={api_key}"
            scenes = make_agromonitoring_request(search_url_90)
            
        scene_search_success = "SUCCESS" if (scenes and isinstance(scenes, list) and len(scenes) > 0) else "FAILED"
    except HTTPException as he:
        if he.status_code in [401, 403] or "authentication" in str(he.detail).lower():
            polygon_auth_success = "FAILED"
        logger.info("Satellite provider: AgroMonitoring")
        logger.info(f"Authentication: {polygon_auth_success}")
        logger.info(f"Scene search: {scene_search_success}")
        logger.info("Image retrieval: FAILED")
        logger.info("Statistics retrieval: FAILED")
        logger.info("NDVI: UNAVAILABLE")
        logger.info("EVI: UNAVAILABLE")
        logger.info("NDWI: UNAVAILABLE")
        raise he
    except Exception as e:
        logger.info("Satellite provider: AgroMonitoring")
        logger.info("Authentication: FAILED")
        logger.info(f"Scene search: {scene_search_success}")
        logger.info("Image retrieval: FAILED")
        logger.info("Statistics retrieval: FAILED")
        logger.info("NDVI: UNAVAILABLE")
        logger.info("EVI: UNAVAILABLE")
        logger.info("NDWI: UNAVAILABLE")
        raise e
    
    if not scenes or not isinstance(scenes, list) or len(scenes) == 0:
        logger.info("Satellite provider: AgroMonitoring")
        logger.info(f"Authentication: {polygon_auth_success}")
        logger.info("Scene search: FAILED")
        logger.info("Image retrieval: FAILED")
        logger.info("Statistics retrieval: FAILED")
        logger.info("NDVI: UNAVAILABLE")
        logger.info("EVI: UNAVAILABLE")
        logger.info("NDWI: UNAVAILABLE")
        raise HTTPException(status_code=404, detail="Satellite data unavailable")

    # Pick latest scene with low cloud cover if available
    low_cloud_scenes = [s for s in scenes if isinstance(s, dict) and s.get("cl", 100) <= 40]
    if low_cloud_scenes:
        latest_scene = low_cloud_scenes[-1]
    else:
        latest_scene = scenes[-1]

    dt = latest_scene.get("dt")
    images = latest_scene.get("image", {})
    truecolor = images.get("truecolor")
    falsecolor = images.get("falsecolor")
    
    image_retrieval_success = "SUCCESS" if truecolor else "FAILED"
    
    # 4. Fetch statistics for indices: ndvi, evi, evi2, ndwi, nri, dswi
    indices = ["ndvi", "evi", "evi2", "ndwi", "nri", "dswi"]
    stats_data = {}
    
    scene_stats = latest_scene.get("stats", {})
    for idx in indices:
        stats_url = scene_stats.get(idx)
        if stats_url:
            try:
                if stats_url.startswith("http://"):
                    stats_url = "https://" + stats_url[7:]
                idx_stats = make_agromonitoring_request(stats_url)
                if idx_stats:
                    stats_data[idx] = idx_stats
            except Exception as e:
                logger.warning(f"[AgroMonitoring] Error fetching stats for index {idx} from {stats_url}: {e}")
                stats_data[idx] = {}
        else:
            stats_data[idx] = {}

    # Extract mean values for indices and save metadata
    stats_data["cloud_cover"] = latest_scene.get("cl")
    stats_data["resolution"] = "10m / Sen2Cor BOA"

    ndvi_val = stats_data.get("ndvi", {}).get("mean")
    evi_val = stats_data.get("evi", {}).get("mean")
    evi2_val = stats_data.get("evi2", {}).get("mean")
    ndwi_val = stats_data.get("ndwi", {}).get("mean")
    nri_val = stats_data.get("nri", {}).get("mean")
    dswi_val = stats_data.get("dswi", {}).get("mean")
    
    stats_retrieval_success = "SUCCESS" if (ndvi_val is not None) or (evi_val is not None) or (ndwi_val is not None) else "FAILED"
    
    ndvi_avail = "AVAILABLE" if ndvi_val is not None else "UNAVAILABLE"
    evi_avail = "AVAILABLE" if evi_val is not None else "UNAVAILABLE"
    ndwi_avail = "AVAILABLE" if ndwi_val is not None else "UNAVAILABLE"

    logger.info("Satellite provider: AgroMonitoring")
    logger.info(f"Authentication: {polygon_auth_success}")
    logger.info(f"Scene search: {scene_search_success}")
    logger.info(f"Image retrieval: {image_retrieval_success}")
    logger.info(f"Statistics retrieval: {stats_retrieval_success}")
    logger.info(f"NDVI: {ndvi_avail}")
    logger.info(f"EVI: {evi_avail}")
    logger.info(f"NDWI: {ndwi_avail}")
    
    obs_date_str = datetime.utcfromtimestamp(dt).strftime("%Y-%m-%d")
    
    image_urls = {
        "truecolor": truecolor,
        "falsecolor": falsecolor
    }

    # 5. Save in local cache
    new_cache = SatelliteAnalysisCache(
        state=norm_state,
        district=norm_district,
        crop=norm_crop,
        polygon_id=polygon_id,
        observation_date=obs_date_str,
        ndvi=ndvi_val,
        evi=evi_val,
        evi2=evi2_val,
        ndwi=ndwi_val,
        nri=nri_val,
        dswi=dswi_val,
        image_urls=image_urls,
        statistics=stats_data
    )
    
    # Delete old cache records for this crop first
    db.query(SatelliteAnalysisCache).filter(
        SatelliteAnalysisCache.state == norm_state,
        SatelliteAnalysisCache.district == norm_district,
        SatelliteAnalysisCache.crop == norm_crop
    ).delete()
    
    db.add(new_cache)
    db.commit()
    db.refresh(new_cache)

    return {
        "state": new_cache.state,
        "district": new_cache.district,
        "crop": new_cache.crop,
        "polygon_id": new_cache.polygon_id,
        "observation_date": new_cache.observation_date,
        "ndvi": new_cache.ndvi,
        "evi": new_cache.evi,
        "evi2": new_cache.evi2,
        "ndwi": new_cache.ndwi,
        "nri": new_cache.nri,
        "dswi": new_cache.dswi,
        "image_urls": new_cache.image_urls,
        "statistics": new_cache.statistics,
        "source": new_cache.source,
        "fetched_at": new_cache.fetched_at.isoformat()
    }

def fetch_ndvi_history(db: Session, state: str, district: str, crop: str) -> list:
    polygon_id = create_or_get_polygon(db, state, district, crop)
    api_key = get_agromonitoring_api_key()

    # Search for history of last 180 days using HTTPS
    now_ts = int(time.time()) - 300
    start_ts = now_ts - (180 * 24 * 60 * 60)

    url = f"https://api.agromonitoring.com/agro/1.0/ndvi/history?polyid={polygon_id}&start={start_ts}&end={now_ts}&appid={api_key}"
    history_records = make_agromonitoring_request(url)

    if not history_records or not isinstance(history_records, list):
        return []

    structured_history = []
    for item in history_records:
        dt = item.get("dt")
        data = item.get("data", {})
        date_str = datetime.utcfromtimestamp(dt).strftime("%Y-%m-%d")
        
        structured_history.append({
            "date": date_str,
            "mean": data.get("mean"),
            "min": data.get("min"),
            "max": data.get("max"),
            "median": data.get("median"),
            "std": data.get("std"),
            "p25": data.get("p25"),
            "p75": data.get("p75")
        })

    return structured_history


def map_to_standard_stage(stage_name: str) -> str:
    """
    Maps crop-specific growth stages to the standard Flutter UI stages.
    """
    if not stage_name:
        return "Vegetative Growth"
    s = stage_name.strip().lower()
    if any(keyword in s for keyword in ["plant", "sow", "transplant", "germination", "seedling"]):
        return "Planting"
    if any(keyword in s for keyword in ["vegetative", "grow", "shoot", "stem", "trunk", "tillering"]):
        return "Vegetative Growth"
    if any(keyword in s for keyword in ["flower", "bloom", "square", "heading", "shoot / flower"]):
        return "Flowering"
    if any(keyword in s for keyword in ["mature", "ripen", "dough", "boll", "pod"]):
        return "Maturity"
    if any(keyword in s for keyword in ["harvest", "cut", "pick"]):
        return "Harvest"
    return "Vegetative Growth"


def classify_crop_health_score(ndvi: float | None, evi: float | None = None, ndwi: float | None = None) -> tuple[str, int | None]:
    """
    Centralized health classification helper.
    Calculates health score (0-100) based on NDVI, EVI, and NDWI,
    and classifies it as Good (>=70), Moderate (40-69), or Poor (<40).
    When NDVI is unavailable, returns ("Satellite data unavailable", None).
    """
    if ndvi is None or ndvi <= 0.0:
        return "Satellite data unavailable", None

    # Calculate EVI approximation if not provided
    if evi is None or evi <= 0.0:
        evi = 0.85 * ndvi + 0.05

    # NDVI Contribution (max 50 points)
    ndvi_contrib = min(50.0, max(0.0, ndvi * 50.0))
    # EVI Contribution (max 30 points)
    evi_contrib = min(30.0, max(0.0, evi * 30.0))
    # NDWI Contribution (max 20 points, maps NDWI range from -0.3 to 0.5 to 0-20)
    if ndwi is not None:
        ndwi_norm = (ndwi + 0.3) / 0.8
        ndwi_contrib = min(20.0, max(0.0, ndwi_norm * 20.0))
    else:
        ndwi_contrib = 10.0 # Baseline default

    health_score = int(round(ndvi_contrib + evi_contrib + ndwi_contrib))
    health_score = max(0, min(100, health_score))

    # Configurable thresholds matching project specification: 70+ Good, 40-69 Moderate, <40 Poor
    threshold_good = 70
    threshold_moderate = 40

    if health_score >= threshold_good:
        status = "Good"
    elif health_score >= threshold_moderate:
        status = "Moderate"
    else:
        status = "Poor"

    return status, health_score


CROP_PHENOLOGY_DEFAULTS = {
    "arhar / tur": {"duration": 180, "stages": ["Planting", "Germination", "Vegetative Growth", "Flowering", "Maturity", "Harvest"], "sow_months": [6, 7]},
    "arhar": {"duration": 180, "stages": ["Planting", "Germination", "Vegetative Growth", "Flowering", "Maturity", "Harvest"], "sow_months": [6, 7]},
    "tur": {"duration": 180, "stages": ["Planting", "Germination", "Vegetative Growth", "Flowering", "Maturity", "Harvest"], "sow_months": [6, 7]},
    "pigeon pea": {"duration": 180, "stages": ["Planting", "Germination", "Vegetative Growth", "Flowering", "Maturity", "Harvest"], "sow_months": [6, 7]},
    "cotton": {"duration": 180, "stages": ["Planting", "Vegetative Growth", "Flowering", "Maturity", "Harvest"], "sow_months": [6, 7]},
    "wheat": {"duration": 120, "stages": ["Planting", "Vegetative Growth", "Tillering", "Maturity", "Harvest"], "sow_months": [10, 11, 12]},
    "soybean": {"duration": 100, "stages": ["Planting", "Vegetative Growth", "Flowering", "Maturity", "Harvest"], "sow_months": [6, 7]},
    "soyabean": {"duration": 100, "stages": ["Planting", "Vegetative Growth", "Flowering", "Maturity", "Harvest"], "sow_months": [6, 7]},
    "maize": {"duration": 110, "stages": ["Planting", "Vegetative Growth", "Flowering", "Maturity", "Harvest"], "sow_months": [6, 7, 10, 11]},
    "paddy": {"duration": 130, "stages": ["Planting", "Vegetative Growth", "Tillering", "Maturity", "Harvest"], "sow_months": [6, 7, 11, 12]},
    "rice": {"duration": 130, "stages": ["Planting", "Vegetative Growth", "Tillering", "Maturity", "Harvest"], "sow_months": [6, 7, 11, 12]},
    "potato": {"duration": 100, "stages": ["Planting", "Germination", "Vegetative Growth", "Tuber Initiation", "Maturity", "Harvest"], "sow_months": [10, 11]},
    "mustard": {"duration": 110, "stages": ["Planting", "Vegetative Growth", "Flowering", "Maturity", "Harvest"], "sow_months": [10, 11]},
    "rapeseed & mustard": {"duration": 110, "stages": ["Planting", "Vegetative Growth", "Flowering", "Maturity", "Harvest"], "sow_months": [10, 11]},
    "coffee": {"duration": 270, "stages": ["Planting", "Vegetative Growth", "Flowering", "Maturity", "Harvest"], "sow_months": [5, 6]},
    "black pepper": {"duration": 240, "stages": ["Planting", "Vegetative Growth", "Flowering", "Maturity", "Harvest"], "sow_months": [5, 6]},
    "khesari": {"duration": 120, "stages": ["Planting", "Vegetative Growth", "Flowering", "Maturity", "Harvest"], "sow_months": [10, 11]},
}


def estimate_crop_growth_stage(crop_name: str, observation_date_str: str, latest_ndvi: float | None, ndvi_trend: str, growing_season: str) -> tuple[str, int, str, int]:
    """
    Estimates crop-specific growth stage and progress based on phenology defaults,
    observation date, NDVI value, and NDVI trend.
    Returns: (current_stage, progress_percent, next_stage, days_to_next)
    """
    from datetime import datetime
    
    # Parse observation date
    try:
        obs_date = datetime.strptime(observation_date_str, "%Y-%m-%d")
    except Exception:
        obs_date = datetime.utcnow()
        
    crop_lower = crop_name.lower()
    
    # Match crop config
    crop_conf = None
    for k, conf in CROP_PHENOLOGY_DEFAULTS.items():
        if k in crop_lower:
            crop_conf = conf
            break
            
    if not crop_conf:
        # Fallback default phenology
        crop_conf = {
            "duration": 120,
            "stages": ["Planting", "Vegetative Growth", "Maturity", "Harvest"],
            "sow_months": [6, 7] if growing_season == "Kharif" else ([10, 11] if growing_season == "Rabi" else [3, 4])
        }
        
    duration = crop_conf["duration"]
    stages = crop_conf["stages"]
    sow_months = crop_conf["sow_months"]
    
    # Find estimated sowing date (closest sow month in the past relative to observation date)
    obs_year = obs_date.year
    obs_month = obs_date.month
    
    sow_month = sow_months[0]
    for m in sow_months:
        if m <= obs_month:
            sow_month = m
        else:
            break
            
    sow_year = obs_year
    if sow_month > obs_month:
        sow_year = obs_year - 1 # Sown last year
        
    sow_date = datetime(sow_year, sow_month, 1)
    days_since_sow = (obs_date - sow_date).days
    if days_since_sow < 0:
        days_since_sow = 0
        
    # Sowing progress fraction
    progress_frac = min(1.0, max(0.0, days_since_sow / duration))
    
    # Initial stage classification by time progress
    num_stages = len(stages)
    stage_idx = int(progress_frac * num_stages)
    if stage_idx >= num_stages:
        stage_idx = num_stages - 1
        
    current_stage = stages[stage_idx]
    
    # Refine stage classification using NDVI Zonal statistics and Trend
    if latest_ndvi is not None:
        if latest_ndvi > 0.65:
            # High NDVI means high biomass (Vegetative Growth, Flowering, or Maturity)
            # Ensure it is not in Planting or Harvest
            if current_stage in [stages[0], stages[-1]]:
                current_stage = stages[min(2, num_stages - 2)] # Typically Flowering or Maturity
        elif latest_ndvi < 0.20:
            # Low NDVI means bare soil or initial growth (Planting, early vegetative or post-harvest)
            if ndvi_trend == "declining" or progress_frac > 0.8:
                current_stage = stages[-1] # Harvested
            else:
                current_stage = stages[0] # Planting
        elif ndvi_trend == "declining" and progress_frac > 0.5:
            # Declining NDVI in later stages means senescence towards harvest
            current_stage = stages[-1] # Harvest
            
    # Recalculate progress index based on selected stage
    stage_idx = stages.index(current_stage)
    progress_percent = int(((stage_idx + 0.5) / num_stages) * 100)
    
    # Determine next stage and estimated days
    if stage_idx < num_stages - 1:
        next_stage = stages[stage_idx + 1]
        days_to_next = int(duration / num_stages)
    else:
        next_stage = stages[-1]
        days_to_next = 0
        
    return current_stage, progress_percent, next_stage, days_to_next


def calculate_crop_satellite_analysis(db: Session, crop) -> dict:
    from datetime import datetime, timedelta
    from sqlalchemy import func
    from ..models.orm_models import CropMasterIndia, SatelliteAnalysisCache
    import time
    
    crop_name = crop.crop_master.name if crop.crop_master else "Unknown Crop"
    district_name = crop.district.name if crop.district else ""
    state_name = crop.district.state.name if (crop.district and crop.district.state) else "Karnataka"
    
    # Crop Master properties
    crop_master_india = db.query(CropMasterIndia).filter(
        func.lower(CropMasterIndia.crop_name) == func.lower(crop_name)
    ).first()
    
    growing_season = crop_master_india.season if crop_master_india else (crop.crop_master.growing_season if crop.crop_master else "Kharif")
    
    # Try to retrieve AgroMonitoring data
    sat_data = None
    satellite_ndvi = None
    satellite_evi = None
    satellite_observation_date = None
    satellite_history = []
    cloud_cover = None
    resolution = None
    
    # Internal flag to know if we have real/baseline data
    has_real_satellite = False
    
    # Default user visible status
    satellite_status = "SATELLITE DATA UNAVAILABLE"
    satellite_error_detail = "Satellite data unavailable"
    
    api_key = get_agromonitoring_api_key()
    if api_key:
        try:
            sat_data = fetch_satellite_indices_and_images(db, state_name, district_name, crop_name)
            if sat_data:
                satellite_ndvi = sat_data.get("ndvi")
                satellite_evi = sat_data.get("evi")
                satellite_observation_date = sat_data.get("observation_date")
                
                stats = sat_data.get("statistics")
                if stats and isinstance(stats, dict):
                    cloud_cover = stats.get("cloud_cover")
                    resolution = stats.get("resolution", "10m / Sen2Cor BOA")
                
                if satellite_ndvi is not None or satellite_evi is not None:
                    satellite_status = "SATELLITE ACTIVE"
                    has_real_satellite = True
                else:
                    satellite_status = "SATELLITE DATA UNAVAILABLE"
                
                try:
                    satellite_history = fetch_ndvi_history(db, state_name, district_name, crop_name)
                except Exception:
                    pass
            else:
                satellite_status = "SATELLITE DATA UNAVAILABLE"
        except HTTPException as he:
            logger.error(f"[AgroMonitoring] HTTP error in analysis helper: {he.detail}")
            satellite_status = "SATELLITE DATA UNAVAILABLE"
            satellite_error_detail = he.detail
        except Exception as e:
            logger.error(f"[AgroMonitoring] Error fetching in analysis helper: {e}")
            satellite_status = "SATELLITE DATA UNAVAILABLE"
            satellite_error_detail = "Satellite service temporarily unavailable"
    else:
        satellite_status = "SATELLITE DATA UNAVAILABLE"
        satellite_error_detail = "Satellite data unavailable"

    # Default values based on satellite availability
    if has_real_satellite:
        latest_ndvi = satellite_ndvi
        mean_ndvi = satellite_ndvi
        latest_evi = satellite_evi
        observation_date = satellite_observation_date
        observation_count = len(satellite_history) if satellite_history else 1

        if satellite_history:
            valid_means = [h["mean"] for h in satellite_history if h.get("mean") is not None]
            if valid_means:
                mean_ndvi = sum(valid_means) / len(valid_means)
            
            if len(valid_means) >= 2:
                if valid_means[-1] > valid_means[-2] + 0.01:
                    ndvi_trend = "improving"
                elif valid_means[-1] < valid_means[-2] - 0.01:
                    ndvi_trend = "declining"
                else:
                    ndvi_trend = "stable"
            else:
                ndvi_trend = "stable"
        else:
            ndvi_trend = "stable"

        health_status, health_index = classify_crop_health_score(
            latest_ndvi if latest_ndvi is not None else latest_evi, 
            latest_evi, 
            crop.moisture_level / 100.0 if crop.moisture_level is not None else None
        )
        
        current_stage, progress_percent, next_stage, estimated_days_to_next_stage = estimate_crop_growth_stage(
            crop_name,
            observation_date or datetime.utcnow().strftime("%Y-%m-%d"),
            latest_ndvi,
            ndvi_trend,
            growing_season
        )
        
        est_days = estimated_days_to_next_stage
        if est_days <= 0:
            est_days = 5
        estimated_harvest_date = (datetime.utcnow() + timedelta(days=est_days)).strftime("%Y-%m-%d")
        
        if satellite_history and len(satellite_history) >= 3:
            confidence = 90.0
        else:
            confidence = 80.0
            
        data_source = "Sentinel-2 / AgroMonitoring"
    else:
        latest_ndvi = None
        mean_ndvi = None
        latest_evi = None
        observation_date = None
        observation_count = 0
        ndvi_trend = "stable"
        
        health_status = "Satellite data unavailable"
        health_index = None
        current_stage = "Growth stage unavailable"
        progress_percent = 0
        next_stage = "Growth stage unavailable"
        estimated_days_to_next_stage = None
        estimated_harvest_date = None
        confidence = 0.0
        data_source = "Satellite data unavailable"

    health_obj = {
        "status": health_status,
        "latest_ndvi": latest_ndvi,
        "mean_ndvi": mean_ndvi,
        "trend": ndvi_trend,
        "observation_date": observation_date,
        "observation_count": observation_count
    }
    
    growth_obj = {
        "current_stage": current_stage,
        "progress_percent": progress_percent,
        "next_stage": next_stage,
        "estimated_days_to_next_stage": estimated_days_to_next_stage,
        "estimated_harvest_date": estimated_harvest_date,
        "confidence": confidence
    }
    
    moisture_val = (crop.moisture_level if crop.moisture_level and crop.moisture_level > 0.0 else None)
    if not moisture_val and latest_ndvi is not None and sat_data:
        ndwi_val = sat_data.get("ndwi")
        if ndwi_val is not None:
            moisture_val = round(ndwi_val * 100.0, 2)
            
    temp_val = crop.temperature if crop.temperature and crop.temperature > 0.0 else None
    if temp_val is None and crop.district:
        try:
            flat_c = extract_flat_coordinates(crop.district.boundary_geojson or crop.boundary_geojson)
            if flat_c:
                c_lng, c_lat = calculate_centroid(flat_c)
                from .weather_service import fetch_current_weather
                w_data = fetch_current_weather(c_lat, c_lng)
                if w_data and "temp" in w_data:
                    temp_val = round(w_data["temp"], 1)
        except Exception as we:
            logger.warning(f"[Weather] Could not fetch district weather: {we}")

    return {
        "crop_id": crop.id,
        "crop_name": crop_name,
        "state": state_name,
        "district": district_name,
        "area_acres": crop.area_acres,
        "cultivated_area_acres": crop.area_acres,
        "area_scope": "crop_in_district",
        "satellite_available": has_real_satellite,
        "satellite_status": satellite_status if has_real_satellite else "SATELLITE DATA UNAVAILABLE",
        "satellite_platform": "Sentinel-2" if has_real_satellite else None,
        "observation_date": observation_date,
        "data_status": "REAL_DATA" if has_real_satellite else "NO_DATA",
        "health": health_obj,
        "growth": growth_obj,
        "health_status": health_status,
        "health_index": health_index,
        "growth_stage": current_stage,
        "est_harvest_days": estimated_days_to_next_stage,
        "latest_ndvi": latest_ndvi,
        "mean_ndvi": mean_ndvi,
        "ndvi_trend": ndvi_trend,
        "latest_evi": latest_evi,
        "observation_count": observation_count,
        "current_growth_stage": current_stage,
        "growth_progress_percent": progress_percent,
        "next_growth_stage": next_stage,
        "estimated_days_to_next_stage": estimated_days_to_next_stage,
        "estimated_harvest_date": estimated_harvest_date,
        "confidence": confidence,
        "data_source": data_source,
        "moisture": moisture_val if has_real_satellite else None,
        "temp": temp_val,
        "temperature": temp_val,
        "cloud_cover": cloud_cover if has_real_satellite else None,
        "resolution": resolution if has_real_satellite else None
    }

