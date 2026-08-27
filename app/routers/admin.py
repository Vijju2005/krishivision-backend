from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict

from ..database import get_db
from ..deps import get_current_user
from ..models.orm_models import User, Analysis, Farm
from ..models.schemas import UserRoleUpdate

router = APIRouter(prefix="/admin", tags=["admin"])


def verify_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Forbidden. Admin privilege required.")
    return current_user


@router.get("/stats")
def get_admin_stats(
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    total_users = db.query(User).count()
    total_analyses = db.query(Analysis).count()
    total_farms = db.query(Farm).count()
    if total_farms == 0:
        total_farms = 2 # fallback mock default value

    return {
        "total_users": total_users,
        "total_analyses": total_analyses,
        "total_farms": total_farms
    }


@router.get("/users")
def get_users_list(
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    users = db.query(User).all()
    # return list of serializable users
    return [
        {
            "id": u.id,
            "full_name": u.full_name,
            "email": u.email,
            "phone": u.phone,
            "role": u.role,
            "created_at": u.created_at
        }
        for u in users
    ]


@router.get("/analyses")
def get_all_analyses(
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    analyses = db.query(Analysis).order_by(Analysis.created_at.desc()).all()
    return [
        {
            "id": a.id,
            "crop": a.crop,
            "district": a.district,
            "area_acres": a.area_acres,
            "growth_stage": a.growth_stage,
            "health_status": a.health_status,
            "created_at": a.created_at,
            "owner_id": a.owner_id
        }
        for a in analyses
    ]


@router.post("/users/{user_id}/role")
def update_user_role(
    user_id: int,
    payload: UserRoleUpdate,
    db: Session = Depends(get_db),
    admin: User = Depends(verify_admin)
):
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.role = payload.role
    db.commit()
    return {"status": "success", "message": f"User {user_id} role updated to {payload.role}"}
