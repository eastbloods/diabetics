from fastapi import Depends, APIRouter, Request
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import InsulinLog
from routers.auth import get_current_user
from schemas import InsulinLogResponse, InsulinLogCreate
from rate_limit import limiter

router = APIRouter(prefix="/insulin", tags=["insulin_log"])


@router.post("/add", response_model=InsulinLogResponse)
@limiter.limit('30/minute')
def add_insulin(request: Request, data: InsulinLogCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    insulin_log = InsulinLog(
        user_id=current_user.id,
        insulin_type=data.insulin_type,
        total_unit=data.total_unit,
        single_dose=data.single_dose
    )

    db.add(insulin_log)
    db.commit()
    db.refresh(insulin_log)
    return insulin_log


@router.get("/history", response_model=List[InsulinLogResponse])
@limiter.limit("30/minute")
def get_insulin_history(request: Request, limit: int = 10, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    logs = (
        db.query(InsulinLog)
        .filter(InsulinLog.user_id == current_user.id)
        .order_by(InsulinLog.injected_at.desc())
        .limit(limit)
        .all()
    )
    return logs
