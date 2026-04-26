from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Dataset(Base):
    __tablename__ = "datasets"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    columns = Column(JSON, nullable=True)
    row_count = Column(Integer, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Сюда добавили cascade удаление для всех связанных данных
    data = relationship("DatasetData", back_populates="dataset", cascade="all, delete")
    history = relationship("ChatHistory", cascade="all, delete")
    reports = relationship("Report", cascade="all, delete")


class DatasetData(Base):
    __tablename__ = "dataset_data"
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    row_index = Column(Integer, nullable=False)
    row_data = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    dataset = relationship("Dataset", back_populates="data")


class ChatHistory(Base):
    __tablename__ = "chat_history"
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    role = Column(String, nullable=False)
    content = Column(Text, nullable=False)
    answer_type = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Report(Base):
    __tablename__ = "reports"
    id = Column(Integer, primary_key=True, index=True)
    dataset_id = Column(Integer, ForeignKey("datasets.id"), nullable=False)
    title = Column(String, nullable=False)
    summary = Column(Text, nullable=True)          # краткий вывод
    findings = Column(JSON, nullable=True)         # список находок
    recommendations = Column(JSON, nullable=True)  # рекомендации
    risks = Column(JSON, nullable=True)            # риски
    raw_text = Column(Text, nullable=True)         # полный текст от AI
    created_at = Column(DateTime, default=datetime.utcnow)