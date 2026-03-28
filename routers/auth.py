import os
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from database import get_db
from models import User
from schemas import UserCreate, UserResponse, Token, UserLogin
from passlib.context import CryptContext
from jose import jwt
from fastapi.security import OAuth2PasswordBearer
import logging
from rate_limit import limiter


logger = logging.getLogger(__name__)
secret = os.getenv("SECRET_KEY")
router = APIRouter(prefix="/auth", tags=["auth"])
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


@router.post("/register", response_model=UserResponse)
@limiter.limit("3/minute")
def register(request: Request, user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=400, detail="Email zaten kayıtlı!")

    hashed = pwd_context.hash(user.password)

    db_user = User(
        email=user.email,
        password_hash=hashed,
        name=user.name,
        surname=user.surname,
        age=user.age,
        height_cm=user.height_cm,
        weight_kg=user.weight_kg,
        diabetes_type=user.diabetes_type
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login(request: Request, user: UserLogin, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.email == user.email).first()
    dt = datetime.now(timezone.utc) + timedelta(hours=24)
    int_timestamp = int(dt.timestamp())

    if not db_user:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı!")
    if not pwd_context.verify(user.password, db_user.password_hash):
        raise HTTPException(status_code=401, detail="Hatalı Şifre!")

    token = jwt.encode({'user_id': str(db_user.id), 'exp': int_timestamp}, secret, algorithm='HS256')
    return {"access_token": token, "token_type": "bearer"}


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    try:
        decoded = jwt.decode(token, secret, algorithms=['HS256'], options={"verify_exp": True})
        user_id = decoded['user_id']
    except Exception as e:
        logger.error(f"JWT decode hatası: {e}")
        raise HTTPException(status_code=401, detail="Geçersiz token!")

    db_user = db.query(User).filter(User.id == user_id).first()
    if not db_user:
        raise HTTPException(status_code=401, detail="Kullanıcı bulunamadı!")
    return db_user

