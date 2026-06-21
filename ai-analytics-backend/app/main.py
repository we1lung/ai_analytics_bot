from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
from sqladmin import Admin, ModelView

from app.database import get_db, engine, Base
from app import models
from app.models import User, Dataset, Report
from app.routers import datasets, analytics, chat, reports, auth, admin as router_admin

# 1. Создаем таблицы в БД при запуске
Base.metadata.create_all(bind=engine)

# 2. Инициализируем ЕДИНСТВЕННЫЙ экземпляр FastAPI
app = FastAPI(title="AI Business Analytics")

# 3. Настраиваем визуальную админку SQLAdmin
admin_panel = Admin(app, engine)

class UserAdmin(ModelView, model=User):
    column_list = [User.id, User.email]

class DatasetAdmin(ModelView, model=Dataset):
    column_list = [Dataset.id, Dataset.name, Dataset.user_id, Dataset.row_count]

class ReportAdmin(ModelView, model=Report):
    column_list = [Report.id, Report.dataset_id, Report.title, Report.created_at]

admin_panel.add_view(UserAdmin)
admin_panel.add_view(DatasetAdmin)
admin_panel.add_view(ReportAdmin)

# 4. Настраиваем CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 5. Подключаем роутеры
app.include_router(auth.router)
app.include_router(router_admin.router) # Избегаем конфликта имён с admin_panel
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