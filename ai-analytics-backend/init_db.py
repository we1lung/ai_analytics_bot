from app.database import engine, Base
from app.models import User, Dataset, DatasetData, ChatHistory, Report

# Создаёт все таблицы
Base.metadata.create_all(bind=engine)
print("✅ Таблицы созданы")