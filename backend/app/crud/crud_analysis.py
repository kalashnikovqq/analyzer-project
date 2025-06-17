from typing import List, Optional, Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_, desc
from sqlalchemy.orm import selectinload
import logging

from app.crud.base import CRUDBase
from app.models.analysis import AnalysisRequest, AnalysisResult, AnalysisStatus
from app.schemas.analysis import AnalysisRequestCreate, AnalysisRequestResponse


class CRUDAnalysis(CRUDBase[AnalysisRequest, AnalysisRequestCreate, AnalysisRequestResponse]):

    
    async def create_with_user(
        self, db: AsyncSession, *, obj_in: AnalysisRequestCreate, user_id: int
    ) -> AnalysisRequest:

        obj_in_data = obj_in.model_dump()
        db_obj = AnalysisRequest(**obj_in_data, user_id=user_id)
        
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj
    
    async def get_multi_by_user(
        self, db: AsyncSession, *, user_id: int, skip: int = 0, limit: int = 100
    ) -> List[AnalysisRequest]:

        query = (
            select(AnalysisRequest)
            .where(AnalysisRequest.user_id == user_id)
            .options(selectinload(AnalysisRequest.results))
            .order_by(desc(AnalysisRequest.created_at))
            .offset(skip)
            .limit(limit)
        )
        result = await db.execute(query)
        return result.scalars().all()
    
    async def get_with_result(
        self, db: AsyncSession, *, id: int, user_id: Optional[int] = None
    ) -> Optional[AnalysisRequest]:
   
        if user_id:
            query = select(AnalysisRequest).where(
                and_(AnalysisRequest.id == id, AnalysisRequest.user_id == user_id)
            ).options(selectinload(AnalysisRequest.results))
        else:
            query = select(AnalysisRequest).where(AnalysisRequest.id == id).options(selectinload(AnalysisRequest.results))
        
        result = await db.execute(query)
        return result.scalars().first()
    
    async def update_status(
        self, db: AsyncSession, *, db_obj: AnalysisRequest, status: AnalysisStatus, error_message: Optional[str] = None
    ) -> AnalysisRequest:

        update_data = {"status": status}
        if error_message:
            update_data["error_message"] = error_message
        
        return await super().update(db, db_obj=db_obj, obj_in=update_data)
    
    async def update_progress(
        self, 
        db: AsyncSession, 
        *, 
        db_obj: AnalysisRequest, 
        progress_percentage: float,
        current_stage: str,
        processed_reviews: int = 0,
        total_reviews: int = 0
    ) -> AnalysisRequest:

        update_data = {
            "progress_percentage": progress_percentage,
            "current_stage": current_stage,
            "processed_reviews": processed_reviews,
            "total_reviews": total_reviews
        }
        
        return await super().update(db, db_obj=db_obj, obj_in=update_data)
    
    async def save_result(
        self, 
        db: AsyncSession, 
        *, 
        request_id: int,
        positive_aspects: List[Dict[str, Any]],
        negative_aspects: List[Dict[str, Any]],
        aspect_categories: Dict[str, Any],
        reviews_count: int,
        sentiment_summary: Dict[str, Any],
        product_info: Optional[Dict[str, Any]] = None
    ) -> AnalysisResult:


        query = select(AnalysisResult).where(AnalysisResult.request_id == request_id)
        existing = await db.execute(query)
        existing_result = existing.scalars().first()
        
        if existing_result:
            existing_result.positive_aspects = positive_aspects
            existing_result.negative_aspects = negative_aspects
            existing_result.aspect_categories = aspect_categories
            existing_result.reviews_count = reviews_count
            existing_result.sentiment_summary = sentiment_summary
            existing_result.product_info = product_info
            db.add(existing_result)
            await db.commit()
            await db.refresh(existing_result)
            return existing_result
        else:
            result = AnalysisResult(
                request_id=request_id,
                positive_aspects=positive_aspects,
                negative_aspects=negative_aspects,
                aspect_categories=aspect_categories,
                reviews_count=reviews_count,
                sentiment_summary=sentiment_summary,
                product_info=product_info
            )
            db.add(result)
            await db.commit()
            await db.refresh(result)
            return result
    
    async def get_result(self, db: AsyncSession, *, request_id: int) -> Optional[AnalysisResult]:

        query = select(AnalysisResult).where(AnalysisResult.request_id == request_id)
        result = await db.execute(query)
        return result.scalars().first()


analysis = CRUDAnalysis(AnalysisRequest) 