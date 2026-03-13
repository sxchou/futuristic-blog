from pydantic_settings import BaseSettings
from typing import Optional, List
import os
from zoneinfo import ZoneInfo


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./futuristic_blog.db"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "your-super-secret-key-change-in-production-please"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "admin123"
    ADMIN_EMAIL: str = "admin@futuristic-blog.com"
    
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:3000"]
    
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "Futuristic Blog"
    
    FRONTEND_URL: str = "http://localhost:3000"
    TIMEZONE: str = "Asia/Shanghai"
    
    @property
    def tz(self) -> ZoneInfo:
        return ZoneInfo(self.TIMEZONE)
    
    @property
    def get_database_url(self) -> str:
        url = os.getenv("DATABASE_URL", self.DATABASE_URL)
        if url and url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        if url and url.startswith("mysql://"):
            url = url.replace("mysql://", "mysql+pymysql://", 1)
        if url and "planetscale.com" in url:
            if "?" in url:
                url = url + "&ssl_verify_cert=true"
            else:
                url = url + "?ssl_verify_cert=true"
        return url
    
    @property
    def is_email_configured(self) -> bool:
        return bool(self.SMTP_HOST and self.SMTP_USER and self.SMTP_PASSWORD)
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
