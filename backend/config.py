"""
Configuration file for the database application.
Supports both development/testing and production environments.
"""

import os
import urllib.parse
from datetime import timedelta
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)


class Config:
    """Base configuration"""

    # Application (can be overridden via environment variables)
    APP_NAME = os.getenv("APP_NAME", "NLF Database")
    APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
    COMPANY_NAME = os.getenv("COMPANY_NAME", "Your Company")
    LOGO_URL = os.getenv("LOGO_URL", "/static/logo.png")
    COPYRIGHT_YEAR = int(os.getenv("COPYRIGHT_YEAR", 2026))

    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES = 60
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    TOKEN_REFRESH_INTERVAL_MINUTES = int(os.getenv("TOKEN_REFRESH_INTERVAL_MINUTES", 55))
    SESSION_TIMEOUT_MINUTES = int(os.getenv("SESSION_TIMEOUT_MINUTES", 60))

    # Database
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = int(os.getenv("DB_PORT", 5432))
    DB_USER = os.getenv("DB_USER", "nlf_user")
    DB_PASSWORD = os.getenv("DB_PASSWORD", "nlf_password")
    DB_NAME = os.getenv("DB_NAME", "nlf_db")
    DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

    # SMTP Configuration
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
    SMTP_USER = os.getenv("SMTP_USER", "your-email@gmail.com")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "your-app-password")
    SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", "noreply@example.com")
    SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "NLF Database")

    # Email Token expiration
    REGISTRATION_TOKEN_EXPIRE_HOURS = int(os.getenv("REGISTRATION_TOKEN_EXPIRE_HOURS", 24))
    EMAIL_TOKEN_EXPIRE_HOURS = 24
    USER_PASSWORD_RESET_TOKEN_EXPIRE_HOURS = int(os.getenv("USER_PASSWORD_RESET_TOKEN_EXPIRE_HOURS", 1))
    PASSWORD_RESET_TOKEN_EXPIRE_HOURS = int(os.getenv("PASSWORD_RESET_TOKEN_EXPIRE_HOURS", 24))
    EMAIL_CHANGE_TOKEN_EXPIRE_HOURS = 1

    # Login Security
    MAX_UNSUCCESSFUL_LOGINS = 5
    GRACE_PERIOD_MINUTES_3_ATTEMPTS = 5
    GRACE_PERIOD_MINUTES_5_ATTEMPTS = 10

    # Password Requirements
    PASSWORD_MIN_LENGTH = 10
    PASSWORD_MAX_LENGTH = 60
    PASSWORD_REQUIRE_UPPERCASE = True
    PASSWORD_REQUIRE_LOWERCASE = True
    PASSWORD_REQUIRE_DIGIT_OR_SPECIAL = True

    # OTP Settings
    OTP_SECRET_LENGTH = 32
    OTP_VALIDITY_MINUTES = 5

    # Frontend
    FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")

    # Languages
    AVAILABLE_LANGUAGES = ["en", "de"]
    DEFAULT_LANGUAGE = os.getenv("DEFAULT_LANGUAGE", "en")

    # CORS
    CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

    # UI
    ITEMS_PER_PAGE_DEFAULT = int(os.getenv("ITEMS_PER_PAGE_DEFAULT", 10))
    ITEMS_PER_PAGE_OPTIONS = [10, 20, 50]

    # Feature Flags (can be enabled/disabled via environment variables)
    FEATURE_OTP_ENABLED = os.getenv("FEATURE_OTP_ENABLED", "true").lower() == "true"
    FEATURE_EMAIL_VERIFICATION_ENABLED = os.getenv("FEATURE_EMAIL_VERIFICATION_ENABLED", "true").lower() == "true"
    FEATURE_CORPORATE_APPROVALS_ENABLED = os.getenv("FEATURE_CORPORATE_APPROVALS_ENABLED", "true").lower() == "true"

    # File Upload Configuration
    _DEFAULT_UPLOAD_DIRECTORY = Path(__file__).parent / "uploads"
    UPLOAD_DIRECTORY = Path(os.getenv("UPLOAD_DIRECTORY", str(_DEFAULT_UPLOAD_DIRECTORY))).resolve()
    MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 50 * 1024 * 1024))  # 50MB default
    ALLOWED_FILE_EXTENSIONS = [".pdf"]
    WATERMARK_IMAGE_PATH = os.getenv("WATERMARK_IMAGE_PATH", "")

    @classmethod
    def get_watermark_image_path(cls) -> Optional[Path]:
        """Return configured watermark image path (or None when disabled)."""
        value = (cls.WATERMARK_IMAGE_PATH or "").strip()
        if not value:
            return None

        image_path = Path(value)
        if not image_path.is_absolute():
            image_path = (Path(__file__).parent / image_path).resolve()
        return image_path
    
    @classmethod
    def ensure_upload_directory(cls):
        """Ensure upload directory exists"""
        cls.UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration"""

    DEBUG = True
    TESTING = False
    DB_NAME = os.getenv("DB_NAME", "nlf_db_dev")
    DATABASE_URL = f"postgresql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}:{Config.DB_PORT}/{DB_NAME}"


class TestingConfig(Config):
    """Testing configuration"""

    DEBUG = True
    TESTING = True
    DB_NAME = os.getenv("DB_NAME", "nlf_db_test")
    DATABASE_URL = f"postgresql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}:{Config.DB_PORT}/{DB_NAME}"
    SQLALCHEMY_ECHO = False


class ProductionConfig(Config):
    """Production configuration"""

    DEBUG = False
    TESTING = False
    DB_NAME = os.getenv("DB_NAME", "nlf_db_prod")
    DATABASE_URL = f"postgresql://{Config.DB_USER}:{Config.DB_PASSWORD}@{Config.DB_HOST}:{Config.DB_PORT}/{DB_NAME}"


def get_config() -> Config:
    """Get the appropriate configuration based on environment"""
    env = os.getenv("ENVIRONMENT", "development")

    if env == "production":
        cfg = ProductionConfig()
    elif env == "testing":
        cfg = TestingConfig()
    else:
        cfg = DevelopmentConfig()

    # Ensure username and password are URL-encoded to handle non-ASCII or
    # special characters (prevents psycopg2/ libpq decode errors).
    user_enc = urllib.parse.quote_plus(cfg.DB_USER)
    pwd_enc = urllib.parse.quote_plus(cfg.DB_PASSWORD)
    cfg.DATABASE_URL = f"postgresql://{user_enc}:{pwd_enc}@{cfg.DB_HOST}:{cfg.DB_PORT}/{cfg.DB_NAME}"

    return cfg


# Create config instance
config = get_config()
