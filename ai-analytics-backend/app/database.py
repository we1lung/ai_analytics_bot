from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os

load_dotenv()  # загружает переменные из .env файла

DATABASE_URL = os.getenv("DATABASE_URL")  # читает строку подключения

# engine — это соединение с базой данных
engine = create_engine(DATABASE_URL)

# SessionLocal — фабрика сессий (каждый запрос получает свою сессию)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base — базовый класс для всех моделей
Base = declarative_base()

# get_db — функция-зависимость, открывает и закрывает сессию на каждый запрос
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()