from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
import os
import bcrypt
from app.database import get_db
from app.models import User

router = APIRouter(prefix="/auth", tags=["Auth"])

SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-env")
ALGORITHM = "HS256"


class RegisterRequest(BaseModel):
    username: str
    email: EmailStr
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# 🚀 ИСПРАВЛЕНО: username теперь может быть Optional[str], чтобы избежать ResponseValidationError
class AuthResponse(BaseModel):
    access_token: str
    token_type: str
    user_id: int
    username: Optional[str] = None
    role: str


def hash_password(password: str) -> str:
    pwd_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(pwd_bytes, salt).decode("utf-8")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        pwd_bytes = plain_password.encode('utf-8')
        hashed_bytes = hashed_password.encode('utf-8')
        return bcrypt.checkpw(pwd_bytes, hashed_bytes)
    except ValueError:
        return False


def create_access_token(user_id: int):
    expire = datetime.now(timezone.utc) + timedelta(days=7)
    to_encode = {"sub": str(user_id), "exp": expire}
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def verify_token(token: str) -> int:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = int(payload.get("sub"))
        return user_id
    except:
        raise HTTPException(status_code=401, detail="Invalid token")


@router.post("/register", response_model=AuthResponse)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(
        (User.email == req.email) | (User.username == req.username)
    ).first()
    
    if existing:
        raise HTTPException(status_code=400, detail="User exists")
    
    user = User(
        username=req.username,
        email=req.email,
        password_hash=hash_password(req.password),
        role="user",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    token = create_access_token(user.id)
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "role": user.role,
    }


@router.post("/login", response_model=AuthResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    
    if not user or not verify_password(req.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    token = create_access_token(user.id)
    
    # 🚀 ИСПРАВЛЕНО: если username в БД равен None, подставляем часть email до собаки
    safe_username = user.username if user.username else user.email.split('@')[0]
    
    return {
        "access_token": token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": safe_username,
        "role": user.role,
    }


@router.get("/me")
def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)):
    if not authorization:
        raise HTTPException(status_code=401, detail="No token provided")
    
    try:
        token_type, token = authorization.split(" ")
        if token_type.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid token type")
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid authorization header format")
        
    user_id = verify_token(token)
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
        
    return {
        "id": user.id,
        "username": user.username if user.username else user.email.split('@')[0],
        "email": user.email,
        "role": user.role,
    }