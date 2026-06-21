from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Dataset, DatasetData
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

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




@router.get("/{dataset_id}/correlation")
def get_correlation(dataset_id: int, db: Session = Depends(get_db)):
    df = get_dataframe(dataset_id, db)
    numeric_df = df.select_dtypes(include="number")
 
    if numeric_df.shape[1] < 2:
        return {
            "dataset_id": dataset_id,
            "message": "Недостаточно числовых колонок для корреляции (нужно минимум 2)",
            "columns": list(numeric_df.columns),
            "matrix": [],
        }
 
    corr = numeric_df.corr().round(3)
    columns = list(corr.columns)
 
    # Формат, удобный для heatmap в Recharts: плоский список ячеек {x, y, value}
    cells = []
    for row_col in columns:
        for col_col in columns:
            val = corr.loc[row_col, col_col]
            cells.append({
                "x": col_col,
                "y": row_col,
                "value": None if pd.isna(val) else float(val),
            })
 
    return {
        "dataset_id": dataset_id,
        "columns": columns,
        "cells": cells,
    }
 
 
@router.get("/{dataset_id}/anomalies")
def get_anomalies(dataset_id: int, contamination: float = 0.05, db: Session = Depends(get_db)):
    df = get_dataframe(dataset_id, db)
    numeric_df = df.select_dtypes(include="number").dropna(axis=1, how="all")
 
    if numeric_df.shape[1] == 0:
        return {
            "dataset_id": dataset_id,
            "message": "Числовых колонок нет, anomaly detection невозможен",
            "anomalies": [],
        }
 
    # IsolationForest не переносит NaN — заполняем медианой по колонке
    clean_df = numeric_df.fillna(numeric_df.median(numeric_only=True))
 
    if len(clean_df) < 10:
        return {
            "dataset_id": dataset_id,
            "message": "Слишком мало строк для anomaly detection (нужно минимум 10)",
            "anomalies": [],
        }
 
    contamination = max(0.01, min(contamination, 0.5))  # защита от мусорных значений параметра
 
    model = IsolationForest(contamination=contamination, random_state=42)
    predictions = model.fit_predict(clean_df)  # -1 = аномалия, 1 = норма
    scores = model.decision_function(clean_df)  # чем ниже, тем более аномально
 
    anomaly_indices = np.where(predictions == -1)[0]
 
    anomalies = []
    for idx in anomaly_indices:
        row = df.iloc[int(idx)].to_dict()
        # JSON-safety: NaN/inf -> None
        row = {k: (None if isinstance(v, float) and (pd.isna(v) or np.isinf(v)) else v) for k, v in row.items()}
        anomalies.append({
            "row_index": int(idx),
            "anomaly_score": round(float(scores[idx]), 4),
            "row_data": row,
        })
 
    anomalies.sort(key=lambda a: a["anomaly_score"])  # самые аномальные первыми
 
    return {
        "dataset_id": dataset_id,
        "total_rows": len(df),
        "anomaly_count": len(anomalies),
        "contamination": contamination,
        "anomalies": anomalies,
    }
 
 
@router.get("/{dataset_id}/trend")
def get_trend(dataset_id: int, db: Session = Depends(get_db)):
    df = get_dataframe(dataset_id, db)
 
    date_col = next((c for c in df.columns if "date" in c.lower()), None)
    if date_col is None:
        return {
            "dataset_id": dataset_id,
            "message": "Дата-колонка не найдена (ищем колонку с 'date' в названии)",
            "trend": [],
        }
 
    parsed_dates = pd.to_datetime(df[date_col], errors="coerce")
    valid_mask = parsed_dates.notna()
 
    if valid_mask.sum() < 2:
        return {
            "dataset_id": dataset_id,
            "message": f"Колонка '{date_col}' найдена, но не удалось распарсить достаточно дат",
            "date_column": date_col,
            "trend": [],
        }
 
    numeric_cols = df.select_dtypes(include="number").columns.tolist()
    if not numeric_cols:
        return {
            "dataset_id": dataset_id,
            "message": "Числовых колонок для построения тренда нет",
            "date_column": date_col,
            "trend": [],
        }
 
    trend_df = df.loc[valid_mask, numeric_cols].copy()
    trend_df["__date"] = parsed_dates[valid_mask].dt.date.astype(str)
 
    # Группируем по дате (на случай нескольких строк в один день) и берём среднее
    grouped = trend_df.groupby("__date")[numeric_cols].mean().reset_index()
    grouped = grouped.sort_values("__date")
 
    trend_points = []
    for _, row in grouped.iterrows():
        point = {"date": row["__date"]}
        for col in numeric_cols:
            val = row[col]
            point[col] = None if pd.isna(val) else round(float(val), 2)
        trend_points.append(point)
 
    return {
        "dataset_id": dataset_id,
        "date_column": date_col,
        "metrics": numeric_cols,
        "trend": trend_points,
    }
 
 
@router.get("/compare")
def compare_datasets(dataset_id_a: int, dataset_id_b: int, db: Session = Depends(get_db)):
    if dataset_id_a == dataset_id_b:
        raise HTTPException(status_code=400, detail="Нужны два разных датасета")
 
    df_a = get_dataframe(dataset_id_a, db)
    df_b = get_dataframe(dataset_id_b, db)
    ds_a = db.query(Dataset).filter(Dataset.id == dataset_id_a).first()
    ds_b = db.query(Dataset).filter(Dataset.id == dataset_id_b).first()
 
    numeric_a = set(df_a.select_dtypes(include="number").columns)
    numeric_b = set(df_b.select_dtypes(include="number").columns)
    common_cols = sorted(numeric_a & numeric_b)
 
    if not common_cols:
        return {
            "dataset_a": {"id": dataset_id_a, "name": ds_a.name},
            "dataset_b": {"id": dataset_id_b, "name": ds_b.name},
            "message": "Нет общих числовых колонок для сравнения",
            "comparison": {},
        }
 
    comparison = {}
    for col in common_cols:
        mean_a = float(df_a[col].mean())
        mean_b = float(df_b[col].mean())
        diff_pct = None
        if mean_a != 0:
            diff_pct = round((mean_b - mean_a) / abs(mean_a) * 100, 2)
 
        comparison[col] = {
            "dataset_a": {
                "mean": round(mean_a, 2),
                "min": round(float(df_a[col].min()), 2),
                "max": round(float(df_a[col].max()), 2),
            },
            "dataset_b": {
                "mean": round(mean_b, 2),
                "min": round(float(df_b[col].min()), 2),
                "max": round(float(df_b[col].max()), 2),
            },
            "diff_percent": diff_pct,
        }
 
    return {
        "dataset_a": {"id": dataset_id_a, "name": ds_a.name, "row_count": len(df_a)},
        "dataset_b": {"id": dataset_id_b, "name": ds_b.name, "row_count": len(df_b)},
        "common_columns": common_cols,
        "comparison": comparison,
    }