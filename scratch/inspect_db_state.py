from app.database import SessionLocal
from app.models.orm_models import District, State, Crop, CropMaster, AgroMonitoringPolygon, SatelliteAnalysisCache
from sqlalchemy import func

db = SessionLocal()

print("States:")
for s in db.query(State).all():
    print(f"  ID: {s.id}, Name: {s.name}")

print("\nDistricts in Karnataka:")
karnataka = db.query(State).filter(func.lower(State.name) == "karnataka").first()
if karnataka:
    for d in db.query(District).filter(District.state_id == karnataka.id).all():
        print(f"  ID: {d.id}, Name: {d.name}")

print("\nCrops for Chikkamagaluru:")
chikka = db.query(District).filter(func.lower(District.name) == "chikkamagaluru").first()
if chikka:
    crops = db.query(Crop).filter(Crop.district_id == chikka.id).all()
    for c in crops:
        print(f"  ID: {c.id}, Name: {c.crop_master.name}, Source: {c.source}, Source Year: {c.source_year}, Area: {c.area_acres}")
else:
    print("  Chikkamagaluru district not found!")

print("\nAgroMonitoring Polygons:")
for p in db.query(AgroMonitoringPolygon).all():
    print(f"  ID: {p.id}, State: {p.state}, District: {p.district}, Crop: {p.crop}, Polygon ID: {p.polygon_id}")

print("\nSatellite Analysis Cache:")
for cache in db.query(SatelliteAnalysisCache).all():
    print(f"  ID: {cache.id}, Crop: {cache.crop}, District: {cache.district}, Date: {cache.observation_date}, NDVI: {cache.ndvi}")

db.close()
