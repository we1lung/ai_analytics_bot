from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Header
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Dataset, DatasetData, User
from app.routers.auth import verify_token
import pandas as pd
import tempfile
from pathlib import Path

router = APIRouter(prefix="/datasets", tags=["Datasets"])


def get_current_user(authorization: str = Header(None), db: Session = Depends(get_db)) -> User:
    """Получает текущего пользователя из стандартного заголовка Authorization"""
    if not authorization:
        raise HTTPException(status_code=401, detail="No token provided")
    
    try:
        token_type, token = authorization.split(" ")
        if token_type.lower() != "bearer":
            raise HTTPException(status_code=401, detail="Invalid token type")
        
        user_id = verify_token(token)
    except:
        raise HTTPException(status_code=401, detail="Invalid token")
        
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.post("/upload")
def upload_csv(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Загружает CSV файл"""
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        content = file.file.read()
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        df = pd.read_csv(tmp_path)
        rows = df.to_dict(orient="records")
        columns = list(df.columns)
        
        dataset = Dataset(
            name=file.filename,
            row_count=len(df),
            columns=columns,
            user_id=current_user.id,
        )
        db.add(dataset)
        db.flush()
        
        for idx, row in enumerate(rows):
            dataset_data = DatasetData(
                dataset_id=dataset.id,
                row_index=idx,
                row_data=row,
            )
            db.add(dataset_data)
        
        db.commit()
        db.refresh(dataset)
        
        return {
            "id": dataset.id,
            "name": dataset.name,
            "row_count": len(df),
            "columns": columns,
        }
    finally:
        Path(tmp_path).unlink(missing_ok=True)


@router.get("/")
def get_user_datasets(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Список датасетов текущего пользователя"""
    datasets = db.query(Dataset).filter(Dataset.user_id == current_user.id).all()
    
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


@router.get("/{dataset_id}")
def get_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Информация о датасете (только если твой)"""
    dataset = db.query(Dataset).filter(
        (Dataset.id == dataset_id) & (Dataset.user_id == current_user.id)
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    return {
        "id": dataset.id,
        "name": dataset.name,
        "row_count": dataset.row_count,
        "column_count": len(dataset.columns) if dataset.columns else 0,
        "columns": dataset.columns,
    }


@router.delete("/{dataset_id}")
def delete_dataset(
    dataset_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Удаляет датасет (только свой)"""
    dataset = db.query(Dataset).filter(
        (Dataset.id == dataset_id) & (Dataset.user_id == current_user.id)
    ).first()
    
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")
    
    db.query(DatasetData).filter(DatasetData.dataset_id == dataset_id).delete()
    db.delete(dataset)
    db.commit()
    
    return {"message": "Deleted"}