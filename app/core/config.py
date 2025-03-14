"""
Configuration settings for the application.
This module loads config from environment variables.
"""
import os
from typing import List, Any, Dict, Optional, Union
from pathlib import Path
from pydantic import field_validator, AnyHttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """Application settings class that loads from environment variables."""
    
    # App settings
    APP_NAME: str = "Meter Installation Tracking System"
    APP_VERSION: str = "1.0.0"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str
    API_PREFIX: str = "/api"
    TIMEZONE: str = "Asia/Bangkok"
    
    # CORS settings
    ALLOW_ORIGINS: List[str] = ["http://localhost:8080", "http://localhost:3000"]
    ALLOWED_HOSTS: List[str] = ["localhost", "127.0.0.1"]
    
    # Database settings
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "postgres"
    DB_NAME: str = "meterinstall_db"
    
    # JWT settings
    JWT_SECRET_KEY: str
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # PWA API settings
    PWA_AUTH_URL: str = "https://intranet.pwa.co.th/login/webservice_login6.php"
    PWA_AUTH_API_URL: Optional[str] = None  # For backward compatibility
    PWA_AUTH_API_TIMEOUT: int = 15
    PWA_NOTIFY_API_URL: str
    # PWA admin users
    PWA_ADMIN_USERS: List[str] = ["11008", "11009", "11010", "10932"]
    
    # Oracle DB sync settings
    ORACLE_HOST: str
    ORACLE_PORT: int = 1521
    ORACLE_SERVICE: str
    ORACLE_USER: str
    ORACLE_PASSWORD: str
    
    # Line Notify settings
    LINE_NOTIFY_API_URL: str
    LINE_NOTIFY_DEFAULT_TOKEN: str
    
    # Redis settings
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: Optional[str] = None
    
    # Logging settings
    LOG_LEVEL: str = "INFO"
    LOG_DIR: str = "./logs"
    
    @property
    def DATABASE_URL(self) -> str:
        """Get the database URL string."""
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Get the async database URL string."""
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"
    
    @property
    def ORACLE_CONNECTION_STRING(self) -> str:
        """Get the Oracle connection string."""
        return f"{self.ORACLE_USER}/{self.ORACLE_PASSWORD}@{self.ORACLE_HOST}:{self.ORACLE_PORT}/{self.ORACLE_SERVICE}"
    
    @property
    def REDIS_URL(self) -> str:
        """Get the Redis URL string."""
        if self.REDIS_PASSWORD:
            return f"redis://:{self.REDIS_PASSWORD}@{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"
    
    @field_validator("ALLOW_ORIGINS")
    @classmethod
    def validate_allow_origins(cls, v: Union[str, List]) -> List[str]:
        """Validate and convert ALLOW_ORIGINS to list if it's a string."""
        if isinstance(v, str) and v.startswith("[") and v.endswith("]"):
            import json
            return json.loads(v)
        return v
    
    @field_validator("ALLOWED_HOSTS")
    @classmethod
    def validate_allowed_hosts(cls, v: Union[str, List]) -> List[str]:
        """Validate and convert ALLOWED_HOSTS to list if it's a string."""
        if isinstance(v, str) and v.startswith("[") and v.endswith("]"):
            import json
            return json.loads(v)
        return v
    
    @field_validator("PWA_AUTH_API_URL")
    @classmethod
    def validate_pwa_auth_api_url(cls, v: Optional[str]) -> Optional[str]:
        """Process PWA_AUTH_API_URL for backward compatibility."""
        return v  # Just accept it for compatibility but we'll use PWA_AUTH_URL
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True
    )


# Create settings instance
settings = Settings() 