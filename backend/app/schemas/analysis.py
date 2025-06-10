from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field, validator

from app.models.analysis import AnalysisStatus, Marketplace


class AnalysisRequestBase(BaseModel):
    url: str = Field(..., description="URL товара или ID товара")
    marketplace: str = Field(..., description="Маркетплейс (wb, ozon)")
    max_reviews: int = Field(30, description="Количество отзывов для парсинга", ge=1, le=1000)


class AnalysisRequestCreate(AnalysisRequestBase):
    product_id: Optional[str] = None  
    
    @validator('max_reviews')
    def validate_max_reviews(cls, v):
        if v is None:
            return 30
        if v > 1000:
            return 1000
        if v < 1:
            return 1
        return v


class AnalysisResultResponse(BaseModel):
    id: int
    request_id: int
    positive_aspects: Optional[List[Dict[str, Any]]] = []
    negative_aspects: Optional[List[Dict[str, Any]]] = []
    aspect_categories: Optional[Dict[str, Any]] = {}
    reviews_count: int = 0
    sentiment_summary: Optional[Dict[str, Any]] = {}
    product_info: Optional[Dict[str, Any]] = {}
    created_at: datetime

    class Config:
        from_attributes = True


class AnalysisRequestResponse(AnalysisRequestBase):
    id: int
    user_id: int
    product_id: str  
    status: str
    error_message: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    results: Optional[AnalysisResultResponse] = None
    product_name: Optional[str] = None  
    reviews_count: Optional[int] = 0  
    class Config:
        from_attributes = True
        populate_by_name = True
        arbitrary_types_allowed = True


class AnalysisRequestWithResults(AnalysisRequestResponse):
    results: Optional[AnalysisResultResponse] = None 