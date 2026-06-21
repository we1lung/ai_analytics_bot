from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User, Dataset
from app.routers.auth import verify_token

router = APIRouter(prefix="/admin", tags=["Admin"])


def get_current_admin(token: str = Header(None), db: Session = Depends(get_db)):
    """Проверяет что юзер админ"""
    if not token:
        raise HTTPException(status_code=401, detail="No token")
    
    user_id = verify_token(token)
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user or user.role != "admin":
        raise HTTPException(status_code=403, detail="Not admin")
    
    return user


@router.get("/users")
def get_users(db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    """Список всех пользователей"""
    users = db.query(User).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "email": u.email,
            "role": u.role,
            "created_at": u.created_at,
            "datasets_count": len(u.datasets),
        }
        for u in users
    ]


@router.get("/users/{user_id}/datasets")
def get_user_datasets(user_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    """Датасеты конкретного пользователя"""
    user = db.query(User).filter(User.id == user_id).first()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    datasets = db.query(Dataset).filter(Dataset.user_id == user_id).all()
    return [
        {
            "id": ds.id,
            "name": ds.name,
            "row_count": ds.row_count,
            "column_count": len(ds.columns) if ds.columns else 0,
            "created_at": ds.created_at,
        }
        for ds in datasets
    ]


@router.delete("/users/{user_id}")
def delete_user(user_id: int, db: Session = Depends(get_db), admin: User = Depends(get_current_admin)):
    """Удаляет пользователя и его датасеты"""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Cannot delete yourself")
    
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    # Удаляем его датасеты
    db.query(Dataset).filter(Dataset.user_id == user_id).delete()
    db.delete(user)
    db.commit()
    
    return {"message": "User deleted"}