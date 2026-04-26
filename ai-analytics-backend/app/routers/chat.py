from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import Dataset, DatasetData, ChatHistory
from app.services import (
    should_use_sql, answer_with_sql, answer_with_ai, 
    answer_with_sql_raw, answer_with_ai_explain  # NEW imports!
)
from sqlalchemy import text
import json

router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    dataset_id: int
    question: str

@router.post("/")
def chat_with_data(request: ChatRequest, db: Session = Depends(get_db)):
    # 1. Check dataset exists
    dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found")

    # 2. Load chat history
    history_rows = (
        db.query(ChatHistory)
        .filter(ChatHistory.dataset_id == request.dataset_id)
        .order_by(ChatHistory.created_at)
        .all()
    )
    chat_history = [{"role": r.role, "content": r.content} for r in history_rows]

    # 3. SQL vs AI decision - CORRECT INDENTATION!
    if should_use_sql(request.question):
        # 🚀 HYBRID: SQL data + AI explanation
        sql_data = answer_with_sql_raw(question=request.question, db=db, dataset_id=request.dataset_id)
        
        if sql_data:
            sql_explanation = answer_with_ai_explain(
                question=request.question, 
                sql_data=sql_data, 
                dataset_summary=get_sql_summary(db, request.dataset_id, dataset),
                chat_history=chat_history
            )
            answer = sql_explanation
            answer_type = "sql+ai"
        else:
            answer = "❓ Не понял SQL вопрос. Попробуй: 'сколько строк?', 'пропуски?', 'среднее?'"
            answer_type = "sql_error"
    else:
        # Pure AI path
        dataset_summary = get_sql_summary(db, request.dataset_id, dataset)
        try:
            answer = answer_with_ai(request.question, dataset_summary, chat_history)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI error: {str(e)}")
        answer_type = "ai"

    # 4. Save to history
    db.add(ChatHistory(
        dataset_id=request.dataset_id,
        role="user",
        content=request.question,
        answer_type=None,
    ))
    db.add(ChatHistory(
        dataset_id=request.dataset_id,
        role="assistant",
        content=str(answer),
        answer_type=answer_type,
    ))
    db.commit()

    return {
        "dataset_id": request.dataset_id,
        "question": request.question,
        "answer": answer,
        "answered_by": answer_type,
    }

# ... rest of your routes unchanged (history, clear_history) ...

def get_sql_summary(db: Session, dataset_id: int, dataset: Dataset) -> dict:
    """Get dataset stats using ONLY SQL. No pandas."""
    summary = {
        "name": dataset.name,
        "row_count": dataset.row_count or 0,
        "column_count": len(dataset.columns) if dataset.columns else 0,
        "columns": dataset.columns or [],
        "averages": {},
        "top_categories": {},
    }
    
    columns = [c for c in (dataset.columns or []) if isinstance(c, str)]
    
    for col in columns[:3]:
        try:
            # Try numeric stats
            stats = db.execute(text("""
                SELECT 
                    COALESCE(AVG((row_data->>:col)::numeric), 0) as avg_val,
                    COALESCE(MIN((row_data->>:col)::numeric), 0) as min_val,
                    COALESCE(MAX((row_data->>:col)::numeric), 0) as max_val
                FROM dataset_data 
                WHERE dataset_id = :id 
                AND row_data->>:col IS NOT NULL 
                AND row_data->>:col ~ '^-?[0-9]+(\.[0-9]+)?$'
                LIMIT 1
            """), {"col": col, "id": dataset_id}).fetchone()
            
            if stats and float(stats.avg_val) != 0:
                summary["averages"][col] = {
                    "mean": round(float(stats.avg_val), 2),
                    "min": round(float(stats.min_val), 2),
                    "max": round(float(stats.max_val), 2),
                }
                continue
                
        except Exception:
            pass
        
        # Text categories
        try:
            top = db.execute(text("""
                SELECT row_data->>:col, COUNT(*) as cnt
                FROM dataset_data 
                WHERE dataset_id = :id AND row_data->>:col IS NOT NULL
                GROUP BY row_data->>:col 
                ORDER BY cnt DESC 
                LIMIT 3
            """), {"col": col, "id": dataset_id}).fetchall()
            
            if top:
                summary["top_categories"][col] = [
                    {"value": str(r[0]), "count": int(r.cnt)} for r in top
                ]
        except:
            pass
    
    return summary

# Keep your other routes (get_chat_history, clear_chat_history) exactly as they are

@router.get("/{dataset_id}/history")
def get_chat_history(dataset_id: int, db: Session = Depends(get_db)):
    rows = (
        db.query(ChatHistory)
        .filter(ChatHistory.dataset_id == dataset_id)
        .order_by(ChatHistory.created_at)
        .all()
    )
    return [{"role": r.role, "content": r.content, "answered_by": r.answer_type} for r in rows]


@router.delete("/{dataset_id}/history")
def clear_chat_history(dataset_id: int, db: Session = Depends(get_db)):
    db.query(ChatHistory).filter(ChatHistory.dataset_id == dataset_id).delete()
    db.commit()
    return {"message": "История очищена"}