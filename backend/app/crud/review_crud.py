from typing import List, Optional, Dict, Any, Union
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func
from sqlalchemy.sql import text
from sqlalchemy.orm import selectinload

from app.models.review import ReviewModel
from app.crud.base import CRUDBase

class CRUDReview(CRUDBase[ReviewModel, Dict[str, Any], Dict[str, Any]]):
    async def get_by_product_id(self, db: AsyncSession, product_id: str) -> List[ReviewModel]:
     
        result = await db.execute(select(self.model).where(self.model.product_id == product_id))
        return result.scalars().all()

    async def get_by_source(self, db: AsyncSession, source: str) -> List[ReviewModel]:

        result = await db.execute(select(self.model).where(self.model.source == source))
        return result.scalars().all()

    async def get_with_pagination(
        self, 
        db: AsyncSession, 
        skip: int = 0, 
        limit: int = 100,
        product_id: Optional[str] = None,
        source: Optional[str] = None
    ) -> tuple[List[ReviewModel], int]:

        query = select(self.model)
        count_query = select(func.count()).select_from(self.model)
        
        if product_id:
            query = query.where(self.model.product_id == product_id)
            count_query = count_query.where(self.model.product_id == product_id)
        
        if source:
            query = query.where(self.model.source == source)
            count_query = count_query.where(self.model.source == source)
        
        query = query.offset(skip).limit(limit)
        
        result = await db.execute(query)
        count_result = await db.execute(count_query)
        
        return result.scalars().all(), count_result.scalar()

    async def create_from_parser(
        self, 
        db: AsyncSession, 
        parsed_reviews: List[Dict[str, Any]]
    ) -> List[ReviewModel]:

        reviews_to_create = []
        
        for review_data in parsed_reviews:
            if review_data.get("external_id"):
                existing = await db.execute(
                    select(self.model).where(
                        self.model.external_id == review_data["external_id"],
                        self.model.source == review_data["source"]
                    )
                )
                if existing.scalar_one_or_none():
                    continue
            
            review = ReviewModel(
                text=review_data["text"],
                rating=review_data.get("rating"),
                product_id=review_data["product_id"],
                product_name=review_data.get("product_name"),
                source=review_data["source"],
                external_id=review_data.get("external_id"),
                date=review_data.get("date"),
                author=review_data.get("author"),
                likes=review_data.get("likes", 0),
                dislikes=review_data.get("dislikes", 0),
                photos=review_data.get("photos", [])
            )
            
            reviews_to_create.append(review)
        
        if reviews_to_create:
            db.add_all(reviews_to_create)
            await db.commit()
            for review in reviews_to_create:
                await db.refresh(review)
        
        return reviews_to_create

    async def update_sentiment(
        self, 
        db: AsyncSession, 
        review_id: int, 
        sentiment_data: Dict[str, Any]
    ) -> Optional[ReviewModel]:

        review = await self.get(db, review_id)
        if not review:
            return None
        
        review.sentiment = sentiment_data
        await db.commit()
        await db.refresh(review)
        return review

reviews = CRUDReview(ReviewModel) 