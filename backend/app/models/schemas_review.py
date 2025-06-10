from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime

# Базовая модель для схем
class ReviewBase(BaseModel):
    text: str = Field(..., description="Текст отзыва")
    rating: Optional[int] = Field(None, description="Рейтинг (от 1 до 5)")
    product_id: str = Field(..., description="ID товара")
    product_name: Optional[str] = Field(None, description="Название товара")
    source: str = Field(..., description="Маркетплейс (источник отзыва)")

# Модель для создания отзыва
class ReviewCreate(ReviewBase):
    external_id: Optional[str] = Field(None, description="Внешний ID отзыва (ID в системе маркетплейса)")
    date: Optional[str] = Field(None, description="Дата публикации отзыва")
    author: Optional[str] = Field(None, description="Имя автора отзыва")
    likes: Optional[int] = Field(0, description="Количество лайков")
    dislikes: Optional[int] = Field(0, description="Количество дизлайков")
    photos: Optional[List[str]] = Field([], description="URL фотографий в отзыве")

# Модель для ответа с полной информацией об отзыве
class ReviewResponse(ReviewBase):
    id: int = Field(..., description="Внутренний ID отзыва в нашей системе")
    external_id: Optional[str] = Field(None, description="Внешний ID отзыва (ID в системе маркетплейса)")
    date: Optional[str] = Field(None, description="Дата публикации отзыва")
    author: Optional[str] = Field(None, description="Имя автора отзыва")
    likes: Optional[int] = Field(0, description="Количество лайков")
    dislikes: Optional[int] = Field(0, description="Количество дизлайков")
    photos: Optional[List[str]] = Field([], description="URL фотографий в отзыве")
    sentiment: Optional[Dict[str, Any]] = Field(None, description="Результаты анализа тональности")
    topics: Optional[List[str]] = Field([], description="Список тематик отзыва")
    created_at: datetime = Field(..., description="Дата создания записи")
    updated_at: Optional[datetime] = Field(None, description="Дата обновления записи")
    
    class Config:
        orm_mode = True

# Модель для списка отзывов 
class ReviewListResponse(BaseModel):
    total: int = Field(..., description="Общее количество отзывов")
    items: List[ReviewResponse] = Field(..., description="Список отзывов")
    page: int = Field(1, description="Текущая страница")
    size: int = Field(20, description="Размер страницы")
    pages: int = Field(..., description="Общее количество страниц")

# Модель для результатов анализа тональности отзыва
class SentimentResult(BaseModel):
    review_id: int = Field(..., description="ID отзыва")
    positive: float = Field(..., description="Позитивная оценка")
    negative: float = Field(..., description="Негативная оценка")
    neutral: float = Field(..., description="Нейтральная оценка")
    overall: str = Field(..., description="Итоговая оценка (positive, negative, neutral)")
    
    class Config:
        orm_mode = True

# Модель для результатов анализа тематик отзыва
class TopicResult(BaseModel):
    review_id: int = Field(..., description="ID отзыва")
    topics: List[str] = Field(..., description="Список тематик отзыва")
    
    class Config:
        orm_mode = True 