from fastapi import APIRouter, HTTPException, Depends, status, Body, UploadFile, File, Request
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.schemas.user import UserCreate, User, UserUpdate
from app.schemas.token import Token
from app.models.user import User as UserModel
from app.crud.crud_user import CRUDUser
from app.core.security import create_access_token, verify_password, get_password_hash, decode_jwt_token, create_refresh_token
from app.core.config import settings
from app.api.deps import get_current_user
from fastapi.security import OAuth2PasswordBearer
import os
import shutil
from uuid import uuid4
from pathlib import Path
import logging
import jwt as pyjwt

logger = logging.getLogger(__name__)

crud_user = CRUDUser(UserModel)
router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/login")

AVATAR_DIR = "app/static/avatars"
os.makedirs(AVATAR_DIR, exist_ok=True)

@router.post('/register')
async def register(user_in: UserCreate, db: AsyncSession = Depends(get_db)):
    try:
        existing_user = await crud_user.get_by_email(db, email=user_in.email)
        if existing_user:
            raise HTTPException(status_code=400, detail='Пользователь с таким email уже существует')
        
        user = await crud_user.create(db, obj_in=user_in)
        access_token = create_access_token(subject=user.id)
        refresh_token = create_refresh_token(subject=user.id)
        
        user_data = {
            "id": user.id,
            "email": user.email,
            "is_active": user.is_active,
            "is_superuser": user.is_superuser,
            "full_name": user.full_name,
            "created_at": user.created_at
        }
        
        return {
            'user': user_data,
            'access_token': access_token,
            'refresh_token': refresh_token
        }
    except Exception as e:
        logger.error(f"Ошибка при регистрации пользователя: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Внутренняя ошибка сервера: {str(e)}")

@router.post('/login')
async def login(data: dict, db: AsyncSession = Depends(get_db)):
    email = data.get('email')
    password = data.get('password')
    if not email or not password:
        raise HTTPException(status_code=400, detail='Email и пароль обязательны')
    user = await crud_user.get_by_email(db, email=email)
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(status_code=401, detail='Неверный email или пароль')
    access_token = create_access_token(subject=user.id)
    refresh_token = create_refresh_token(subject=user.id)
    
    user_data = {
        "id": user.id,
        "email": user.email,
        "is_active": user.is_active,
        "is_superuser": user.is_superuser,
        "full_name": user.full_name,
        "created_at": user.created_at
    }
    
    return {
        'user': user_data,
        'access_token': access_token,
        'refresh_token': refresh_token
    }

@router.put('/profile', response_model=User)
async def update_profile(
    user_update: UserUpdate,
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    current_user = await get_current_user(db, token)
    updated_user = await crud_user.update(db, db_obj=current_user, obj_in=user_update)
    return updated_user

@router.post('/change-password')
async def change_password(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    current_user = await get_current_user(db, token)
    current_password = data.get('currentPassword')
    new_password = data.get('newPassword')
    if not current_password or not new_password:
        raise HTTPException(status_code=400, detail='Текущий и новый пароль обязательны')
    
    if not verify_password(current_password, current_user.hashed_password):
        raise HTTPException(status_code=401, detail='Неверный текущий пароль')
        
    hashed_password = get_password_hash(new_password)
    await crud_user.update(db, db_obj=current_user, obj_in={"hashed_password": hashed_password})
    return {"status": "success", "message": "Пароль успешно изменен"}

@router.post('/avatar', response_model=dict)
async def upload_avatar(
    avatar: UploadFile = File(...),
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    try:
        if not avatar.filename:
            raise HTTPException(
                status_code=422,
                detail="Файл не выбран или имеет пустое имя"
            )
        
        if not avatar.content_type or not avatar.content_type.startswith('image/'):
            raise HTTPException(
                status_code=422,
                detail="Загружаемый файл должен быть изображением"
            )
        
        contents = await avatar.read()
        if len(contents) > 10 * 1024 * 1024:  # 10MB
            raise HTTPException(
                status_code=422,
                detail="Размер файла не должен превышать 10MB"
            )
        
        await avatar.seek(0)
        
        import uuid
        file_extension = os.path.splitext(avatar.filename)[1]
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        file_path = os.path.join(AVATAR_DIR, unique_filename)
        
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(avatar.file, buffer)
        
        avatar_url = f"/static/avatars/{unique_filename}"
        
        user_from_db = await crud_user.get(db, id=current_user.id)
        if not user_from_db:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        await crud_user.update(db, db_obj=user_from_db, obj_in={"avatar": avatar_url})
        
        return {
            "message": "Аватар успешно обновлен",
            "avatarUrl": avatar_url
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при загрузке файла: {str(e)}"
        )

@router.get('/me', response_model=User)
async def get_current_user_info(
    db: AsyncSession = Depends(get_db),
    token: str = Depends(oauth2_scheme)
):
    current_user = await get_current_user(db, token)
    return current_user 

@router.post('/refresh', response_model=dict)
async def refresh_token(
    data: dict = Body(...),
    db: AsyncSession = Depends(get_db)
):

    refresh_token_str = data.get('refresh_token')
    
    if not refresh_token_str:
        raise HTTPException(
            status_code=400,
            detail="Отсутствует refresh_token"
        )
    
    try:
        payload = decode_jwt_token(refresh_token_str)
        
        user_id = payload.get('sub')
        token_type = payload.get('type')
        
        if not user_id:
            raise HTTPException(
                status_code=401,
                detail="Невалидный refresh_token - отсутствует user_id"
            )
            
        if token_type != "refresh":
            raise HTTPException(
                status_code=401,
                detail="Невалидный refresh_token - неверный тип токена"
            )
        
        try:
            user_id_int = int(user_id)
        except ValueError:
            raise HTTPException(
                status_code=401,
                detail="Невалидный refresh_token - неверный формат user_id"
            )
        
        user = await crud_user.get(db, id=user_id_int)
        if not user:
            raise HTTPException(
                status_code=401,
                detail="Пользователь не найден"
            )
        
        access_token = create_access_token(subject=user.id)
        
        return {
            "access_token": access_token
        }
    except pyjwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Истек срок действия refresh_token"
        )
    except pyjwt.PyJWTError as e:
        logger.error(f"Ошибка JWT при декодировании refresh_token: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Невалидный refresh_token - ошибка декодирования"
        )
    except Exception as e:
        logger.error(f"Ошибка при обновлении токена: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=401,
            detail="Невозможно обновить токен"
        ) 