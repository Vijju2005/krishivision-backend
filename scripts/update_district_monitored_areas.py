import os
import sys

# Ensure backend path is in sys.path
backend_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.append(backend_dir)
os.environ["JWT_SECRET_KEY"] = "dev_secret_key_123"

from sqlalchemy import create_engine, func
from sqlalchemy.orm import sessionmaker
from app.models.orm_models import District, State, APYCropStatistic
from app.routers.dashboard_map import get_district_monitored_area_acres

def update_all_district_monitored_areas():
    db_urls = []
    env_db = os.getenv("DATABASE_URL")
    if env_db:
        db_urls.append(env_db)
    
    root_db = os.path.abspath(os.path.join(backend_dir, "..", "krishivision.db"))
    backend_db = os.path.join(backend_dir, "krishivision.db")
    
    for path in [root_db, backend_db]:
        if os.path.exists(path):
            db_urls.append(f"sqlite:///{path}")
            
    # Remove duplicate DB URLs preserving order
    unique_urls = list(dict.fromkeys(db_urls))
    
    for url in unique_urls:
        print(f"\n--- Updating database at: {url} ---")
        try:
            connect_args = {"check_same_thread": False} if url.startswith("sqlite") else {}
            engine = create_engine(url, connect_args=connect_args)
            SessionLocal = sessionmaker(bind=engine)
            db = SessionLocal()

            districts = db.query(District).all()
            updated_count = 0

            print(f"Total districts in DB: {len(districts)}")

            for d in districts:
                state_name = d.state.name if d.state else ""
                if not state_name:
                    continue

                calculated_acres = get_district_monitored_area_acres(db, state_name, d.name)
                if calculated_acres and calculated_acres > 0:
                    if abs((d.monitored_area_acres or 0.0) - calculated_acres) > 0.01:
                        d.monitored_area_acres = calculated_acres
                        updated_count += 1
                        if d.name.lower() == "morena":
                            print(f"MORENA UPDATED: {calculated_acres} acres")

            db.commit()
            print(f"Successfully updated {updated_count} district monitored_area_acres records in DB: {url}")
            db.close()
        except Exception as e:
            print(f"Error updating DB at {url}: {e}")

if __name__ == "__main__":
    update_all_district_monitored_areas()
