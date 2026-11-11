from pydantic_settings import BaseSettings
from typing import Optional

class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+psycopg2://im45145v@localhost:5432/pewmail"
    
    # Security
    SECRET_KEY: str = "your_secret_key_here_change_in_production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # AI Provider
    AI_PROVIDER_URL: str = "https://api.openai.com/v1"
    AI_API_KEY: str = "your_api_key_here"
    
    # Google OAuth
    GOOGLE_CLIENT_ID: Optional[str] = None
    GOOGLE_CLIENT_SECRET: Optional[str] = None
    
    # Frontend URL
    FRONTEND_URL: str = "http://localhost:5173"
    
    class Config:
        env_file = ".env"

settings = Settings()