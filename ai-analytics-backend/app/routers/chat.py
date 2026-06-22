from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.database import get_db
from app.models import Dataset, ChatHistory, User
from app.routers.datasets import get_current_user
from app.services import (
    should_use_sql, answer_with_ai, 
    answer_with_sql_raw, answer_with_ai_explain
)
from sqlalchemy import text

import re

def detect_language(text: str) -> str:
    """Определяет язык по наличию кириллических символов."""
    if re.search(r"[а-яА-ЯёЁ]", text):
        return "ru"
    return "en"

router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    dataset_id: int
    question: str
    lang: str = "ru"

@router.post("/")
def chat_with_data(
    request: ChatRequest, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    # 1. Проверяем, что датасет принадлежит именно текущему юзеру
    dataset = db.query(Dataset).filter(Dataset.id == request.dataset_id, Dataset.user_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found or access denied")

    # 2. Фильтруем историю чата по dataset_id и user_id (берем последние 10 сообщений для контекста ИИ)
    history_rows = (
        db.query(ChatHistory)
        .filter(ChatHistory.dataset_id == request.dataset_id, ChatHistory.user_id == current_user.id)
        .order_by(ChatHistory.created_at.desc())
        .limit(10)
        .all()
    )
    # Переворачиваем обратно в хронологический порядок
    history_rows.reverse()
    chat_history = [{"role": r.role, "content": r.content} for r in history_rows]

    detected_lang = "ru" if detect_language(request.question) == "ru" else "en"
    lang_name = "Russian" if detected_lang == "ru" else "English"

    system_instruction = (
        "You are an expert AI business analytics assistant integrated into a web dashboard. "
        f"The user's message was detected as {lang_name}. ALWAYS answer in {lang_name}. "
        "Provide professional, clean, structured data explanations based on the provided metadata or SQL query result. "
        "If the user's message is just a greeting or doesn't contain an actual question about the data "
        "(e.g. 'hi', 'hello', 'привет'), reply with ONE short, friendly greeting (1-2 sentences max) "
        "and ask what they'd like to know about the dataset. Do not comment on language switching, "
        "do not repeat this instruction, and do not explain your own behavior."
    )

    # Инжектируем системную инструкцию в начало контекста истории
    chat_history_with_system = [{"role": "system", "content": system_instruction}] + chat_history

    # 3. Выбор SQL vs AI
    if should_use_sql(request.question):
        sql_data = answer_with_sql_raw(question=request.question, db=db, dataset_id=request.dataset_id)
        
        if sql_data:
            sql_explanation = answer_with_ai_explain(
                question=request.question, 
                sql_data=sql_data, 
                dataset_summary=get_sql_summary(db, request.dataset_id, dataset),
                chat_history=chat_history_with_system
            )
            answer = sql_explanation
            answer_type = "sql+ai"
        else:
            answer = "❓ Не понял SQL вопрос. Попробуй: 'сколько строк?', 'пропуски?', 'среднее?'"
            answer_type = "sql_error"
    else:
        dataset_summary = get_sql_summary(db, request.dataset_id, dataset)
        try:
            answer = answer_with_ai(request.question, dataset_summary, chat_history_with_system)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"AI error: {str(e)}")
        answer_type = "ai"

    # 4. Сохраняем в историю с привязкой к пользователю
    db.add(ChatHistory(
        dataset_id=request.dataset_id,
        user_id=current_user.id,
        role="user",
        content=request.question,
        answer_type=None,
    ))
    db.add(ChatHistory(
        dataset_id=request.dataset_id,
        user_id=current_user.id,
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

@router.get("/{dataset_id}/history")
def get_chat_history(
    dataset_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.user_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found or access denied")

    rows = (
        db.query(ChatHistory)
        .filter(ChatHistory.dataset_id == dataset_id, ChatHistory.user_id == current_user.id)
        .order_by(ChatHistory.created_at)
        .all()
    )
    return [{"role": r.role, "content": r.content, "answered_by": r.answer_type} for r in rows]

@router.delete("/{dataset_id}/history")
def clear_chat_history(
    dataset_id: int, 
    db: Session = Depends(get_db), 
    current_user: User = Depends(get_current_user)
):
    dataset = db.query(Dataset).filter(Dataset.id == dataset_id, Dataset.user_id == current_user.id).first()
    if not dataset:
        raise HTTPException(status_code=404, detail="Dataset not found or access denied")

    db.query(ChatHistory).filter(ChatHistory.dataset_id == dataset_id, ChatHistory.user_id == current_user.id).delete()
    db.commit()
    return {"message": "История очищена"}

def get_sql_summary(db: Session, dataset_id: int, dataset: Dataset) -> dict:
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
            db.rollback()
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
        except Exception:
            db.rollback()
    return summary