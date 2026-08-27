from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models.orm_models import User, Analysis

router = APIRouter(prefix="/fields", tags=["fields"])


@router.get("/{job_id}/boundary")
def get_field_boundary(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Returns the field polygon (GeoJSON) for the Map screen.
    job_id here reuses the analysis id since each analysis is tied to one field upload.
    Swap this to a real PostGIS ST_AsGeoJSON query once field boundaries are
    detected/stored properly (e.g. via segmentation on the uploaded image).
    """
    analysis = db.query(Analysis).filter(Analysis.id == job_id, Analysis.owner_id == current_user.id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Field not found")

    return {
        "job_id": job_id,
        "crop": analysis.crop,
        "area_acres": analysis.area_acres,
        "health_status": analysis.health_status,
        "boundary": analysis.boundary_geojson,
    }
