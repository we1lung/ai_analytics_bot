from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.database import get_db, engine, Base
from app import models
from app.routers import datasets, analytics, chat, reports

Base.metadata.create_all(bind=engine)

app = FastAPI(title="AI Business Analytics")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(datasets.router)
app.include_router(analytics.router)
app.include_router(chat.router)
app.include_router(reports.router)


@app.get("/test")
def test_endpoint():
    return {"status": "ok", "message": "FastAPI работает!"}


@app.get("/test-db")
def test_db(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "ok", "message": "PostgreSQL подключён успешно!"}
    except Exception as e:
        return {"status": "error", "message": str(e)}