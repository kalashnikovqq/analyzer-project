from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models.schemas_review import ReviewCreate, ReviewResponse, ReviewListResponse
from app.crud.review_crud import reviews

router = APIRouter()

@router.post("/", response_model=ReviewResponse, status_code=201)
def create_review(
    review_data: ReviewCreate,
    db: Session = Depends(get_db)
):

    return reviews.create(db=db, obj_in=review_data)

@router.get("/", response_model=ReviewListResponse)
def read_reviews(
    product_id: Optional[str] = None,
    source: Optional[str] = None,
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(20, ge=1, le=500, description="Максимальное количество записей для получения"),
    db: Session = Depends(get_db)
):

    filters = {}
    if product_id:
        filters["product_id"] = product_id
    if source:
        filters["source"] = source
    
    items = reviews.get_multi(db=db, skip=skip, limit=limit, filters=filters)
    total = reviews.count(db=db, filters=filters)
    
    return {
        "total": total,
        "items": items,
        "page": (skip // limit) + 1,
        "size": limit,
        "pages": (total + limit - 1) // limit
    }

@router.get("/{review_id}", response_model=ReviewResponse)
def read_review(
    review_id: int,
    db: Session = Depends(get_db)
):

    review = reviews.get(db=db, id=review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    return review

@router.delete("/{review_id}", status_code=204)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db)
):

    review = reviews.get(db=db, id=review_id)
    if not review:
        raise HTTPException(status_code=404, detail="Отзыв не найден")
    reviews.remove(db=db, id=review_id)
    return None

@router.get("/product/{product_id}", response_model=ReviewListResponse)
def read_product_reviews(
    product_id: str,
    source: Optional[str] = None,
    skip: int = Query(0, ge=0, description="Количество записей для пропуска"),
    limit: int = Query(20, ge=1, le=100, description="Максимальное количество записей для получения"),
    db: Session = Depends(get_db)
):

    filters = {"product_id": product_id}
    if source:
        filters["source"] = source
    
    items = reviews.get_multi(db=db, skip=skip, limit=limit, filters=filters)
    total = reviews.count(db=db, filters=filters)
    
    return {
        "total": total,
        "items": items,
        "page": (skip // limit) + 1,
        "size": limit,
        "pages": (total + limit - 1) // limit
    } 