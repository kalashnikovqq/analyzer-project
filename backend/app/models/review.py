from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Text, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.db.base_class import Base

class ReviewModel(Base):
    __tablename__ = "reviews"
    
    id = Column(Integer, primary_key=True, index=True)
    external_id = Column(String, nullable=True, index=True)
    text = Column(Text, nullable=False)
    rating = Column(Integer, nullable=True)
    product_id = Column(String, nullable=False, index=True)
    product_name = Column(String, nullable=True)
    source = Column(String, nullable=False, index=True)
    date = Column(String, nullable=True)
    author = Column(String, nullable=True)
    likes = Column(Integer, nullable=True, default=0)
    dislikes = Column(Integer, nullable=True, default=0)
    photos = Column(JSON, nullable=True, default=list)
    sentiment = Column(JSON, nullable=True)
    topics = Column(JSON, nullable=True, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 