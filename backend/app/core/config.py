import os
from typing import Any, Dict, List, Optional, Union
from pydantic import AnyHttpUrl, PostgresDsn, validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "FeedbackLab"
    API_V1_STR: str = "/api/v1"
    
    SECRET_KEY: str = os.getenv("SECRET_KEY", "FeedbackLabSecretKey2024!#$%^&*")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15  
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30 
    
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []

    @validator("BACKEND_CORS_ORIGINS", pre=True)
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)

    POSTGRES_SERVER: str = os.getenv("POSTGRES_SERVER", "db")
    POSTGRES_USER: str = os.getenv("POSTGRES_USER", "postgres")
    POSTGRES_PASSWORD: str = os.getenv("POSTGRES_PASSWORD", "postgres")
    POSTGRES_DB: str = os.getenv("POSTGRES_DB", "analyzer")
    DATABASE_URL: Optional[str] = os.getenv("DATABASE_URL")
    SQLALCHEMY_DATABASE_URI: Optional[PostgresDsn] = None

    @validator("SQLALCHEMY_DATABASE_URI", pre=True)
    def assemble_db_connection(cls, v: Optional[str], values: Dict[str, Any]) -> Any:
        if isinstance(v, str):
            return v
        
        if values.get("DATABASE_URL"):
            return values.get("DATABASE_URL")
            
        return f"postgresql+asyncpg://{values.get('POSTGRES_USER')}:{values.get('POSTGRES_PASSWORD')}@{values.get('POSTGRES_SERVER')}/{values.get('POSTGRES_DB')}"
    
    MODEL_DIR: str = os.getenv("MODEL_DIR", "../saved_model")
    MAX_REVIEWS: int = 1000
    
    PARSER_TIMEOUT: int = 10
    PARSER_RETRIES: int = 3

    CORS_ORIGINS: List[str] = [
        "http://localhost", 
        "http://localhost:80", 
        "http://localhost:3000",
        "http://127.0.0.1:80",
        "http://127.0.0.1:3000",
        "http://frontend", 
        "http://frontend:80",
        "http://localhost:8000",
        "http://backend:8000"
    ]

    class Config:
        case_sensitive = True
        env_file = ".env"

settings = Settings() 