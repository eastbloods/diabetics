from fastapi import Depends, APIRouter, Request
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from models import SugarLog
from routers.auth import get_current_user
from schemas import SugarLogResponse, SugarLogCreate
from rate_limit import limiter

router = APIRouter(prefix="/sugar", tags=["sugar_log"])


@router.post("/add", response_model=SugarLogResponse)
@limiter.limit("30/minute")
def add_sugar(request: Request, data: SugarLogCreate, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    sugar_log = SugarLog(
        user_id=current_user.id,
        sugar_rate=data.sugar_rate,
        starvation=data.starvation,
    )

    db.add(sugar_log)
    db.commit()
    db.refresh(sugar_log)
    return sugar_log


@router.get("/history", response_model=List[SugarLogResponse])
@limiter.limit("30/minute")
def get_sugar_history(request: Request, limit: int = 10, current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    logs = (
        db.query(SugarLog)
        .filter(SugarLog.user_id == current_user.id)
        .order_by(SugarLog.measure_at.desc())
        .limit(limit)
        .all()
    )
    return logs
