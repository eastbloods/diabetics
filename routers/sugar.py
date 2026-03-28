from fastapi import Depends, APIRouter, Request
from sqlalchemy.orm import Session
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
