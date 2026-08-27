import os
import time
from datetime import datetime
import uuid
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models.orm_models import User, Analysis, Notification
from ..models.schemas import AnalysisStatusResponse, AnalysisResultResponse, AnalysisHistoryItem
from ..services.analysis_service import run_analysis
from ..services.pdf_service import generate_pdf_report

router = APIRouter(prefix="/analysis", tags=["analysis"])

UPLOAD_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "uploads"))
os.makedirs(UPLOAD_DIR, exist_ok=True)

PROCESSING_SECONDS = 5


@router.post("/upload", response_model=AnalysisStatusResponse)
async def upload_image(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    ext = os.path.splitext(file.filename or "")[1] or ".jpg"
    saved_name = f"{uuid.uuid4().hex}{ext}"
    saved_path = os.path.join(UPLOAD_DIR, saved_name)

    with open(saved_path, "wb") as f:
        f.write(await file.read())

    # Run OpenCV Analysis pipeline
    result = run_analysis(saved_path)
    analysis = Analysis(
        owner_id=current_user.id,
        status="processing",
        image_path=saved_path,
        ndvi_image_path=result["ndvi_image_path"],
        crop=result["crop"],
        crop_name=result["crop_name"],
        district=result["district"],
        area_acres=result["area_acres"],
        growth_stage=result["growth_stage"],
        health_status=result["health_status"],
        harvest_in_days=result["harvest_in_days"],
        confidence=result["confidence"],
        crop_confidence=result["crop_confidence"],
        stage_confidence=result["stage_confidence"],
        disease=result["disease"],
        avg_ndvi=result["avg_ndvi"],
        min_ndvi=result["min_ndvi"],
        max_ndvi=result["max_ndvi"],
        boundary_geojson=result["boundary_geojson"],
    )
    db.add(analysis)
    db.commit()
    db.refresh(analysis)

    # Automatically generate user notifications based on analysis health
    notify = Notification(
        user_id=current_user.id,
        title=f"New {result['crop']} Analysis",
        message=f"Crop health is analyzed as '{result['health_status']}' with mean NDVI {result['avg_ndvi']}.",
        type="harvest" if result["health_status"] == "Healthy" else "disease",
    )
    db.add(notify)
    db.commit()

    return AnalysisStatusResponse(job_id=analysis.id, status="processing", progress=0)


@router.get("/{job_id}/status", response_model=AnalysisStatusResponse)
def get_status(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    analysis = db.query(Analysis).filter(Analysis.id == job_id, Analysis.owner_id == current_user.id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    elapsed = (time.time() - analysis.created_at.timestamp())
    progress = min(100, int((elapsed / PROCESSING_SECONDS) * 100))
    status = "completed" if progress >= 100 else "processing"

    if status == "completed" and analysis.status != "completed":
        analysis.status = "completed"
        db.commit()

    return AnalysisStatusResponse(job_id=job_id, status=status, progress=progress)


@router.get("/{job_id}/results", response_model=AnalysisResultResponse)
def get_results(job_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    analysis = db.query(Analysis).filter(Analysis.id == job_id, Analysis.owner_id == current_user.id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")
    return analysis


@router.get("/history", response_model=list[AnalysisHistoryItem])
def get_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    return (
        db.query(Analysis)
        .filter(Analysis.owner_id == current_user.id)
        .order_by(Analysis.created_at.desc())
        .all()
    )


@router.get("/{job_id}/report")
def download_pdf(job_id: int, lang: str = "en", db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    analysis = db.query(Analysis).filter(Analysis.id == job_id, Analysis.owner_id == current_user.id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    pdf_filename = f"report_{job_id}_{lang}.pdf"
    pdf_path = os.path.join(UPLOAD_DIR, pdf_filename)

    from ..models.orm_models import District, State
    parts = analysis.district.split(",") if analysis.district else []
    dist_name = parts[0].strip() if len(parts) > 0 else ""
    state_pref = parts[1].strip() if len(parts) > 1 else ""
    
    district_obj = None
    if dist_name:
        query = db.query(District).join(State).filter(District.name == dist_name)
        if state_pref:
            query = query.filter(State.name == state_pref)
        district_obj = query.first()
        
    district_boundary = district_obj.boundary_geojson if district_obj else None
    state_name = district_obj.state.name if (district_obj and district_obj.state) else (state_pref or "Karnataka")

    generate_pdf_report(
        file_path=pdf_path,
        farmer_name=current_user.full_name,
        crop=analysis.crop or "Unknown",
        district=analysis.district or "Unknown",
        area=analysis.area_acres or 0.0,
        health=analysis.health_status or "Healthy",
        stage=analysis.growth_stage or "Vegetative",
        confidence=analysis.confidence or 90.0,
        harvest_in_days=analysis.harvest_in_days or 45,
        avg_ndvi=analysis.avg_ndvi or 0.60,
        original_img_path=analysis.image_path,
        lang=lang,
        state=state_name,
        district_boundary=district_boundary,
        crop_boundary=analysis.boundary_geojson,
        data_classification="Satellite/ML Classification",
        db_session=db
    )

    lang_names = {
        "en": "English",
        "kn": "Kannada",
        "hi": "Hindi"
    }
    lang_name = lang_names.get(lang.lower(), "English")
    dist_val = (analysis.district or "Unknown").replace(' ', '_')
    crop_val = (analysis.crop or "Unknown").replace(' ', '_')
    download_name = f"KrishiVision_AI_Crop_Report_{dist_val}_{crop_val}_{datetime.now().strftime('%Y%m%d')}.pdf"

    return FileResponse(
        pdf_path,
        media_type="application/pdf",
        filename=download_name
    )


@router.delete("/{job_id}")
def delete_analysis(
    job_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    analysis = db.query(Analysis).filter(Analysis.id == job_id, Analysis.owner_id == current_user.id).first()
    if not analysis:
        raise HTTPException(status_code=404, detail="Analysis not found")

    # Clean up associated files if they exist
    if analysis.image_path and os.path.exists(analysis.image_path):
        try:
            os.remove(analysis.image_path)
        except OSError:
            pass
    if analysis.ndvi_image_path and os.path.exists(analysis.ndvi_image_path):
        try:
            os.remove(analysis.ndvi_image_path)
        except OSError:
            pass

    db.delete(analysis)
    db.commit()
    return {"status": "success", "message": "Analysis deleted successfully"}

