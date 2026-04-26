from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Dataset, DatasetData
import pandas as pd

router = APIRouter(prefix="/analytics", tags=["Analytics"])


def get_dataframe(dataset_id: int, db: Session) -> pd.DataFrame:
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Датасет не найден")
    rows = db.query(DatasetData).filter(DatasetData.dataset_id == dataset_id).all()
    if not rows:
        raise HTTPException(status_code=404, detail="Данные пустые")
    df = pd.DataFrame([r.row_data for r in rows])
    return df


@router.get("/{dataset_id}/summary")
def get_summary(dataset_id: int, db: Session = Depends(get_db)):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Датасет не найден")
    return {
        "dataset_id": dataset_id,
        "name": dataset.name,
        "row_count": dataset.row_count,
        "column_count": len(dataset.columns) if dataset.columns else 0,
        "columns": dataset.columns,
    }


@router.get("/{dataset_id}/missing")
def get_missing_values(dataset_id: int, db: Session = Depends(get_db)):
    df = get_dataframe(dataset_id, db)
    missing = df.isnull().sum().to_dict()
    missing_pct = (df.isnull().mean() * 100).round(2).to_dict()
    result = {}
    for col in df.columns:
        result[col] = {
            "missing_count": int(missing[col]),
            "missing_percent": float(missing_pct[col]),
        }
    return {"dataset_id": dataset_id, "total_rows": len(df), "missing_values": result}


@router.get("/{dataset_id}/averages")
def get_averages(dataset_id: int, db: Session = Depends(get_db)):
    df = get_dataframe(dataset_id, db)
    numeric_df = df.select_dtypes(include="number")
    if numeric_df.empty:
        return {"dataset_id": dataset_id, "message": "Числовых колонок нет", "averages": {}}
    result = {}
    for col in numeric_df.columns:
        result[col] = {
            "mean": round(float(numeric_df[col].mean()), 2),
            "min": round(float(numeric_df[col].min()), 2),
            "max": round(float(numeric_df[col].max()), 2),
            "std": round(float(numeric_df[col].std()), 2),
        }
    return {"dataset_id": dataset_id, "averages": result}


@router.get("/{dataset_id}/top-categories")
def get_top_categories(dataset_id: int, top_n: int = 5, db: Session = Depends(get_db)):
    df = get_dataframe(dataset_id, db)
    text_df = df.select_dtypes(include="object")
    text_df = text_df[[
        c for c in text_df.columns
        if 'date' not in c.lower()
        and df[c].nunique() < len(df) * 0.5
    ]]
    if text_df.empty:
        return {"dataset_id": dataset_id, "message": "Текстовых колонок нет", "categories": {}}
    result = {}
    for col in text_df.columns:
        top = df[col].value_counts().head(top_n)
        result[col] = [{"value": str(val), "count": int(cnt)} for val, cnt in top.items()]
    return {"dataset_id": dataset_id, "top_n": top_n, "categories": result}


@router.get("/{dataset_id}/full-report")
def get_full_report(dataset_id: int, db: Session = Depends(get_db)):
    df = get_dataframe(dataset_id, db)
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id).first()

    summary = {
        "name": dataset.name,
        "row_count": len(df),
        "column_count": len(df.columns),
        "columns": list(df.columns),
    }

    missing = {}
    for col in df.columns:
        cnt = int(df[col].isnull().sum())
        missing[col] = {
            "missing_count": cnt,
            "missing_percent": round(cnt / len(df) * 100, 2),
        }

    averages = {}
    for col in df.select_dtypes(include="number").columns:
        averages[col] = {
            "mean": round(float(df[col].mean()), 2),
            "min": round(float(df[col].min()), 2),
            "max": round(float(df[col].max()), 2),
        }

    categories = {}
    for col in df.select_dtypes(include="object").columns:
        if 'date' in col.lower():
            continue
        if df[col].nunique() >= len(df) * 0.5:
            continue
        top = df[col].value_counts().head(5)
        categories[col] = [{"value": str(v), "count": int(c)} for v, c in top.items()]

    return {
        "dataset_id": dataset_id,
        "summary": summary,
        "missing_values": missing,
        "averages": averages,
        "top_categories": categories,
    }