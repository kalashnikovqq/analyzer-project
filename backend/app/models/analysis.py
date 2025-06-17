from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Enum, Boolean, Float, BigInteger
from sqlalchemy.orm import relationship
import enum
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, HttpUrl
import os

from app.db.database import Base

class AnalysisStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class Marketplace(str, enum.Enum):
    WILDBERRIES = "wb"
    OZON = "ozon"

class AnalysisRequest(Base):
    __tablename__ = "analysis_requests"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user.id"))
    product_id = Column(String, nullable=False)
    marketplace = Column(String, nullable=False)
    status = Column(String, default=AnalysisStatus.PENDING)
    error_message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    url = Column(String, nullable=False)  
    max_reviews = Column(Integer, default=30)  
    is_processed = Column(Boolean, default=False)  
    error = Column(String, nullable=True)  
    
    progress_percentage = Column(Float, default=0.0)  
    current_stage = Column(String, default="pending")  
    processed_reviews = Column(Integer, default=0)  
    total_reviews = Column(Integer, default=0)  
    
    user = relationship("User", back_populates="analysis_requests")
    results = relationship("AnalysisResult", back_populates="request", uselist=False, cascade="all, delete-orphan")

class AnalysisResult(Base):
    __tablename__ = "analysis_results"
    
    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(Integer, ForeignKey("analysis_requests.id"))
    positive_aspects = Column(JSON, nullable=True)  
    negative_aspects = Column(JSON, nullable=True)  
    aspect_categories = Column(JSON, nullable=True)  
    reviews_count = Column(Integer, default=0)  
    sentiment_summary = Column(JSON, nullable=True)  
    product_info = Column(JSON, nullable=True)  
    created_at = Column(DateTime, default=datetime.utcnow)
    
    request = relationship("AnalysisRequest", back_populates="results")

class SentimentAnalysisResult(BaseModel):
    positive: float = Field(..., description="Оценка позитивности текста")
    negative: float = Field(..., description="Оценка негативности текста")
    neutral: float = Field(..., description="Оценка нейтральности текста")
    overall: str = Field(..., description="Общая тональность (positive, negative, neutral)")
    
# Модель для описания тематики отзыва
class Topic(BaseModel):
    name: str = Field(..., description="Название тематики")
    keywords: List[str] = Field([], description="Ключевые слова, относящиеся к тематике")
    count: int = Field(0, description="Количество отзывов по данной тематике")
    percentage: float = Field(0.0, description="Процент отзывов по данной тематике")
    sentiment: Optional[str] = Field(None, description="Тональность отзывов по тематике (positive, negative, neutral)")
    
# Модель для описания распределения рейтингов
class RatingDistribution(BaseModel):
    average: float = Field(..., description="Средний рейтинг")
    count: int = Field(..., description="Общее количество рейтингов")
    distribution: Dict[str, int] = Field(..., description="Распределение рейтингов по шкале (1-5)")
    
# Модель для описания информации о товаре
class ProductInfo(BaseModel):
    name: str = Field("", description="Название товара")
    brand: str = Field("", description="Бренд товара")
    price: float = Field(0.0, description="Цена товара")
    rating: float = Field(0.0, description="Рейтинг товара")
    image_url: Optional[str] = Field(None, description="URL изображения товара")
    url: Optional[str] = Field(None, description="URL товара")
    
# Модель для запроса на анализ отзывов
class AnalysisRequestSchema(BaseModel):
    url: str = Field(..., description="URL товара или ID товара")
    marketplace: str = Field(..., description="Маркетплейс (ozon, wildberries)")
    max_reviews: int = Field(30, description="Количество отзывов для парсинга")
    
# Модель для ответа с результатами анализа
class AnalysisResponse(BaseModel):
    product_id: str
    product_info: Dict[str, Any]
    reviews_count: int
    sentiment_analysis: Dict[str, Any]
    aspect_statistics: Optional[Dict[str, Any]] = None
    topic_analysis: List[Dict[str, Any]] = []
    rating_stats: Dict[str, Any]
    marketplace: str
    topics: Optional[List[str]] = Field([], description="Список тематик, к которым относится отзыв")

    class Config:
        orm_mode = True

# Модель для одного отзыва
class Review(BaseModel):
    id: str = Field(..., description="ID отзыва")
    text: str = Field(..., description="Текст отзыва")
    rating: Optional[int] = Field(None, description="Рейтинг (от 1 до 5)")
    date: Optional[str] = Field(None, description="Дата отзыва")
    product_id: str = Field(..., description="ID товара")
    product_name: Optional[str] = Field(None, description="Название товара")
    author: Optional[str] = Field(None, description="Имя автора отзыва")
    likes: Optional[int] = Field(0, description="Количество лайков на отзыве")
    dislikes: Optional[int] = Field(0, description="Количество дизлайков на отзыве")
    photos: Optional[List[str]] = Field([], description="Список URL фотографий в отзыве")
    source: str = Field(..., description="Источник отзыва (маркетплейс)")
    sentiment: Optional[Dict[str, Any]] = Field(None, description="Анализ тональности для этого отзыва")
    topics: Optional[List[str]] = Field([], description="Список тематик, к которым относится отзыв") 

