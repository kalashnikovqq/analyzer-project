from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False
    full_name: Optional[str] = None
    avatar: Optional[str] = None


class UserCreate(UserBase):
    email: EmailStr
    password: str
    username: str = None


class UserUpdate(UserBase):
    password: Optional[str] = None


class UserInDB(UserBase):
    id: Optional[int] = None
    hashed_password: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class User(UserBase):
    id: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True 