from sqlalchemy.orm import Session
from app.database import SessionLocal, Base, engine
from app.models.orm_models import User, Farm, Analysis, Notification, Settings, State, District, Crop
from app.services.auth import hash_password
from datetime import datetime, timedelta


def seed_database():
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()

    try:
        # Check if users already seeded
        if db.query(User).count() > 0:
            print("Users already seed. Proceeding to map and crop seeding check...")
        else:
            print("Seeding database with production-ready sample data...")

            # 1. Create Users
            admin = User(
                full_name="Krishi Admin",
                email="admin@krishivision.ai",
                phone="+91 9999988888",
                hashed_password=hash_password("admin123"),
                role="admin"
            )
            farmer = User(
                full_name="Ramesh Farmer",
                email="rameshfarmer@gmail.com",
                phone="+91 9876543210",
                hashed_password=hash_password("farmer123"),
                role="user"
            )
            db.add(admin)
            db.add(farmer)
            db.commit()
            db.refresh(admin)
            db.refresh(farmer)

            # 2. Settings
            settings_admin = Settings(user_id=admin.id, preferred_language="en", dark_mode=False)
            settings_farmer = Settings(user_id=farmer.id, preferred_language="en", dark_mode=False)
            db.add(settings_admin)
            db.add(settings_farmer)
            db.commit()

            # 3. Create Farms
            farm1 = Farm(
                owner_id=farmer.id,
                name="Davanagere Main Farm",
                boundary_geojson={
                    "type": "Polygon",
                    "coordinates": [[
                        [75.9200, 14.4650], [75.9235, 14.4660],
                        [75.9230, 14.4620], [75.9190, 14.4615],
                        [75.9200, 14.4650],
                    ]],
                },
                area_acres=2.5
            )
            farm2 = Farm(
                owner_id=farmer.id,
                name="Haveri Plot B",
                boundary_geojson={
                    "type": "Polygon",
                    "coordinates": [[
                        [75.9310, 14.4750], [75.9345, 14.4760],
                        [75.9340, 14.4720], [75.9300, 14.4715],
                        [75.9310, 14.4750],
                    ]],
                },
                area_acres=1.8
            )
            db.add(farm1)
            db.add(farm2)
            db.commit()

            # 4. Create Analysis History
            a1 = Analysis(
                owner_id=farmer.id,
                status="completed",
                crop="Rice",
                district="Davanagere",
                area_acres=2.5,
                growth_stage="Vegetative",
                health_status="Healthy",
                harvest_in_days=35,
                confidence=96.0,
                avg_ndvi=0.62,
                min_ndvi=0.25,
                max_ndvi=0.85,
                boundary_geojson=farm1.boundary_geojson,
                created_at=datetime.utcnow() - timedelta(days=2)
            )
            a2 = Analysis(
                owner_id=farmer.id,
                status="completed",
                crop="Maize",
                district="Haveri",
                area_acres=1.8,
                growth_stage="Flowering",
                health_status="Healthy",
                harvest_in_days=45,
                confidence=94.2,
                avg_ndvi=0.58,
                min_ndvi=0.20,
                max_ndvi=0.78,
                boundary_geojson=farm2.boundary_geojson,
                created_at=datetime.utcnow() - timedelta(days=14)
            )
            a3 = Analysis(
                owner_id=farmer.id,
                status="completed",
                crop="Cotton",
                district="Dharwad",
                area_acres=3.2,
                growth_stage="Boll Formation",
                health_status="At Risk",
                harvest_in_days=20,
                confidence=89.5,
                avg_ndvi=0.38,
                min_ndvi=0.15,
                max_ndvi=0.55,
                boundary_geojson=farm1.boundary_geojson,
                created_at=datetime.utcnow() - timedelta(days=28)
            )
            db.add(a1)
            db.add(a2)
            db.add(a3)
            db.commit()

            # 5. Create Notifications
            n1 = Notification(
                user_id=farmer.id,
                title="Weather Alert: Heavy Rain",
                message="Heavy rain forecast in Davanagere. Consider delaying pesticide applications.",
                type="weather",
                read=False,
                created_at=datetime.utcnow() - timedelta(hours=2)
            )
            n2 = Notification(
                user_id=farmer.id,
                title="Disease Alert: Aphids Spotted",
                message="Local regional warnings for Aphid infestations on groundnut crops.",
                type="disease",
                read=False,
                created_at=datetime.utcnow() - timedelta(hours=5)
            )
            db.add(n1)
            db.add(n2)
            db.commit()

        # Seed map boundaries and crop details if not already present
        if db.query(State).count() == 0:
            print("Seeding Map boundaries (State and Districts)...")
            base_dir = os.path.dirname(os.path.abspath(__file__))
            state_json_path = os.path.join(base_dir, "karnataka_state_boundary.json")
            dist_json_path = os.path.join(base_dir, "karnataka_districts_boundary.json")

            karnataka_geom = None
            districts_geom_map = {}

            if os.path.exists(state_json_path):
                with open(state_json_path, "r", encoding="utf-8") as f:
                    karnataka_geom = json.load(f)
            if os.path.exists(dist_json_path):
                with open(dist_json_path, "r", encoding="utf-8") as f:
                    districts_geom_map = json.load(f)

            if not karnataka_geom:
                try:
                    from scripts.import_india_boundaries import main as import_boundaries
                    import_boundaries()
                except Exception as e:
                    print(f"Error calling import_india_boundaries: {e}")
                return

            # Seed Karnataka State with authentic high-resolution MultiPolygon boundary
            karnataka = State(
                name="Karnataka",
                boundary_geojson=karnataka_geom
            )
            db.add(karnataka)
            db.commit()
            db.refresh(karnataka)

            # Seed Karnataka Districts with authentic polygon boundaries
            districts_data = [
                {
                    "name": "Belagavi",
                    "area": 24560.0,
                    "crops": [
                        {"name": "Sugarcane", "area": 1450.0, "percentage": 35.0, "stage": "Vegetative", "health": "Healthy", "harvest": 68, "fields": 18, "ndvi": 0.72, "evi": 0.58, "moisture": 32.0, "temp": 28.0},
                        {"name": "Paddy", "area": 980.0, "percentage": 24.0, "stage": "Tillering", "health": "Healthy", "harvest": 45, "fields": 12, "ndvi": 0.65, "evi": 0.52, "moisture": 40.0, "temp": 27.0},
                        {"name": "Cotton", "area": 760.0, "percentage": 18.0, "stage": "Flowering", "health": "At Risk", "harvest": 30, "fields": 8, "ndvi": 0.48, "evi": 0.38, "moisture": 25.0, "temp": 30.0},
                        {"name": "Maize", "area": 520.0, "percentage": 13.0, "stage": "Maturity", "health": "Healthy", "harvest": 15, "fields": 6, "ndvi": 0.58, "evi": 0.45, "moisture": 22.0, "temp": 29.0}
                    ]
                },
                {
                    "name": "Dharwad",
                    "area": 18200.0,
                    "crops": [
                        {"name": "Cotton", "area": 1200.0, "percentage": 30.0, "stage": "Boll Formation", "health": "At Risk", "harvest": 20, "fields": 14, "ndvi": 0.42, "evi": 0.35, "moisture": 24.0, "temp": 31.0},
                        {"name": "Paddy", "area": 950.0, "percentage": 23.0, "stage": "Vegetative", "health": "Healthy", "harvest": 50, "fields": 10, "ndvi": 0.68, "evi": 0.55, "moisture": 38.0, "temp": 28.0}
                    ]
                },
                {
                    "name": "Haveri",
                    "area": 16800.0,
                    "crops": [
                        {"name": "Maize", "area": 1500.0, "percentage": 40.0, "stage": "Flowering", "health": "Healthy", "harvest": 45, "fields": 15, "ndvi": 0.58, "evi": 0.45, "moisture": 20.0, "temp": 29.0}
                    ]
                },
                {
                    "name": "Gadag",
                    "area": 14200.0,
                    "crops": [
                        {"name": "Groundnut", "area": 1100.0, "percentage": 35.0, "stage": "Vegetative", "health": "Healthy", "harvest": 55, "fields": 11, "ndvi": 0.62, "evi": 0.49, "moisture": 30.0, "temp": 30.0}
                    ]
                },
                {
                    "name": "Davanagere",
                    "area": 22400.0,
                    "crops": [
                        {"name": "Rice", "area": 1800.0, "percentage": 45.0, "stage": "Vegetative", "health": "Healthy", "harvest": 35, "fields": 22, "ndvi": 0.62, "evi": 0.50, "moisture": 35.0, "temp": 28.0}
                    ]
                },
                {
                    "name": "Vijayapura",
                    "area": 28650.0,
                    "crops": [
                        {"name": "Sugarcane", "area": 2200.0, "percentage": 38.0, "stage": "Vegetative", "health": "Healthy", "harvest": 75, "fields": 20, "ndvi": 0.70, "evi": 0.56, "moisture": 34.0, "temp": 29.0}
                    ]
                }
            ]

            # Seed CropMaster if empty
            from app.models.orm_models import CropMaster
            crop_masters_map = {}
            if db.query(CropMaster).count() == 0:
                crop_masters_data = [
                    {"name": "Coffee", "scientific_name": "Coffea arabica", "category": "Beverage", "icon": "☕", "growing_season": "Year-round", "growth_duration": "9-10 Months", "description": "High-value beverage crop.", "growth_stages": ["Planting", "Vegetative Growth", "Flowering", "Pinhead Stage", "Berry Expansion", "Ripening", "Harvesting"]},
                    {"name": "Black Pepper", "scientific_name": "Piper nigrum", "category": "Spice", "icon": "🌶", "growing_season": "Kharif", "growth_duration": "8-9 Months", "description": "King of Spices.", "growth_stages": ["Perennial Rooting", "Vine Growth", "Spike Emergence", "Flowering", "Berry Formation", "Ripening", "Harvesting"]},
                    {"name": "Cardamom", "scientific_name": "Elettaria cardamomum", "category": "Spice", "icon": "🌿", "growing_season": "Year-round", "growth_duration": "10-12 Months", "description": "Queen of Spices.", "growth_stages": ["Planting", "Vegetative Growth", "Tillering", "Flowering & Fruit Set", "Capsule Maturity", "Harvesting"]},
                    {"name": "Arecanut", "scientific_name": "Areca catechu", "category": "Commercial", "icon": "🌴", "growing_season": "Year-round", "growth_duration": "Multi-year", "description": "Betel nut palm.", "growth_stages": ["Seedling Transplant", "Juvenile Palm", "Crown Expansion", "Inflorescence Emergence", "Nut Setting", "Ripening", "Harvesting"]},
                    {"name": "Rice", "scientific_name": "Oryza sativa", "category": "Cereal", "icon": "🌾", "growing_season": "Kharif/Rabi", "growth_duration": "4 Months", "description": "Staple food grain.", "growth_stages": ["Sowing", "Seedling", "Transplanting", "Tillering", "Panicle Initiation", "Flowering", "Harvesting"]},
                    {"name": "Wheat", "scientific_name": "Triticum aestivum", "category": "Cereal", "icon": "🌾", "growing_season": "Rabi", "growth_duration": "5 Months", "description": "Staple food grain.", "growth_stages": ["Sowing", "Crown Root Initiation", "Tillering", "Jointing", "Flowering", "Milking", "Harvesting"]},
                    {"name": "Maize", "scientific_name": "Zea mays", "category": "Cereal", "icon": "🌽", "growing_season": "Kharif", "growth_duration": "3.5 Months", "description": "Coarse cereal grain.", "growth_stages": ["Sowing", "Germination", "Vegetative Growth", "Tasseling", "Silking", "Dough Stage", "Harvesting"]},
                    {"name": "Sugarcane", "scientific_name": "Saccharum officinarum", "category": "Commercial", "icon": "🎋", "growing_season": "Year-round", "growth_duration": "12-18 Months", "description": "Sugar crop.", "growth_stages": ["Germination", "Tillering", "Grand Growth", "Maturity", "Ripening", "Harvesting"]},
                    {"name": "Cotton", "scientific_name": "Gossypium hirsutum", "category": "Commercial", "icon": "☁️", "growing_season": "Kharif", "growth_duration": "6 Months", "description": "Fibre crop.", "growth_stages": ["Sowing", "Seedling", "Square Formation", "Flowering", "Boll Development", "Boll Bursting", "Harvesting"]},
                    {"name": "Groundnut", "scientific_name": "Arachis hypogaea", "category": "Oilseed", "icon": "🥜", "growing_season": "Kharif/Rabi", "growth_duration": "4 Months", "description": "Oilseed crop.", "growth_stages": ["Sowing", "Germination", "Vegetative Growth", "Flowering", "Pegging Stage", "Pod Development", "Harvesting"]}
                ]
                for cm in crop_masters_data:
                    m = CropMaster(**cm)
                    db.add(m)
                    db.commit()
                    db.refresh(m)
                    crop_masters_map[m.name] = m.id
            else:
                for cm in db.query(CropMaster).all():
                    crop_masters_map[cm.name] = cm.id

            for d_info in districts_data:
                d_boundary = districts_geom_map.get(d_info["name"], {}).get("boundary")
                district = District(
                    state_id=karnataka.id,
                    name=d_info["name"],
                    monitored_area_acres=d_info["area"],
                    boundary_geojson=d_boundary
                )
                db.add(district)
                db.commit()
                db.refresh(district)

                for c_info in d_info["crops"]:
                    lat = 15.0
                    lng = 75.0
                    if district.boundary_geojson and "coordinates" in district.boundary_geojson:
                        bg = district.boundary_geojson
                        if bg["type"] == "Polygon" and bg["coordinates"]:
                            lng, lat = bg["coordinates"][0][0][0], bg["coordinates"][0][0][1]
                        elif bg["type"] == "MultiPolygon" and bg["coordinates"]:
                            lng, lat = bg["coordinates"][0][0][0][0], bg["coordinates"][0][0][0][1]

                    field_boundary = {
                        "type": "Polygon",
                        "coordinates": [[
                            [lng, lat], [lng + 0.05, lat],
                            [lng + 0.05, lat + 0.05], [lng, lat + 0.05],
                            [lng, lat]
                        ]]
                    }
                    master_id = crop_masters_map.get(c_info["name"])
                    crop = Crop(
                        district_id=district.id,
                        crop_master_id=master_id,
                        name=c_info["name"],
                        area_acres=c_info["area"],
                        crop_percentage=c_info["percentage"],
                        growth_stage=c_info["stage"],
                        health_status=c_info["health"],
                        harvest_in_days=c_info["harvest"],
                        fields_count=c_info["fields"],
                        boundary_geojson=field_boundary,
                        avg_ndvi=c_info["ndvi"],
                        min_ndvi=c_info["ndvi"] - 0.2,
                        max_ndvi=c_info["ndvi"] + 0.2,
                        avg_evi=c_info["evi"],
                        moisture_level=c_info["moisture"],
                        temperature=c_info["temp"]
                    )
                    db.add(crop)
                db.commit()

            print("Map boundaries and crop data seeded successfully!")

        print("Database seeding verification complete.")
    except Exception as e:
        print(f"Error seeding database: {e}")
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
