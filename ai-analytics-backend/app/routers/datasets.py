from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Dataset, DatasetData, ChatHistory, Report
import pandas as pd
import io

router = APIRouter(prefix="/datasets", tags=["Datasets"])


@router.post("/upload")
async def upload_csv(file: UploadFile = File(...), db: Session = Depends(get_db)):

    if not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Только CSV файлы разрешены")

    contents = await file.read()

    try:
        df = pd.read_csv(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Ошибка чтения CSV: {str(e)}")

    dataset = Dataset(
        name=file.filename,
        columns=list(df.columns),
        row_count=len(df),
    )
    db.add(dataset)
    db.commit()
    db.refresh(dataset)

    rows = []
    for index, row in df.iterrows():
        rows.append(DatasetData(
            dataset_id=dataset.id,
            row_index=index,
            row_data=row.fillna("").to_dict(),
        ))

    db.bulk_save_objects(rows)
    db.commit()

    return {
        "status": "ok",
        "dataset_id": dataset.id,
        "file_name": dataset.name,
        "columns": dataset.columns,
        "row_count": dataset.row_count,
    }


@router.get("/")
def get_all_datasets(db: Session = Depends(get_db)):
    datasets = db.query(Dataset).all()
    return [
        {
            "id": d.id,
            "name": d.name,
            "columns": d.columns,
            "row_count": d.row_count,
            "created_at": d.created_at,
        }
        for d in datasets
    ]


@router.get("/{dataset_id}")
def get_dataset(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Датасет не найден")

    rows = db.query(DatasetData).filter(DatasetData.dataset_id == dataset_id).all()
    return {
        "id": dataset.id,
        "name": dataset.name,
        "columns": dataset.columns,
        "row_count": dataset.row_count,
        "created_at": dataset.created_at,
        "data": [r.row_data for r in rows],
    }


@router.delete("/{dataset_id}")
async def delete_dataset(dataset_id: int, db: Session = Depends(get_db)):
    db_dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not db_dataset:
        raise HTTPException(status_code=404, detail="Датасет не найден")
    try:
        db.query(DatasetData).filter(DatasetData.dataset_id == dataset_id).delete()
        db.query(ChatHistory).filter(ChatHistory.dataset_id == dataset_id).delete()
        db.query(Report).filter(Report.dataset_id == dataset_id).delete()
        db.delete(db_dataset)
        db.commit()
        return {"status": "ok"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))