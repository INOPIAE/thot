"""
Configuration file for the database application.
Supports both development/testing and production environments.
"""

import os
import urllib.parse
import shutil
import re
from datetime import timedelta
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)



class Config:
    """Base configuration"""
    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "production")
    # Show citation link in PDF watermark
    PDF_WATERMARK_SHOW_CITATION_LINK = os.getenv("PDF_WATERMARK_SHOW_CITATION_LINK", "true").lower() in ("1", "true", "yes")
    # PDF watermark overlay alpha (opacity)
    PDF_WATERMARK_IMAGE_ALPHA = float(os.getenv("PDF_WATERMARK_IMAGE_ALPHA", 0.15))
    # Cookie security (set True in production with HTTPS)
    COOKIE_SECURE = os.getenv("COOKIE_SECURE", "0") in ("1", "true", "True")

    # Application (can be overridden via environment variables)
    APP_NAME = os.getenv("APP_NAME", "NLF Database")
    APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
    COMPANY_NAME = os.getenv("COMPANY_NAME", "Your Company")
    LOGO_URL = os.getenv("LOGO_URL", "/static/logo.png")
    COPYRIGHT_YEAR = int(os.getenv("COPYRIGHT_YEAR", 2026))

    # Security
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))
    REFRESH_TOKEN_EXPIRE_DAYS = 7
    TOKEN_REFRESH_INTERVAL_MINUTES = int(
        os.getenv(
            "TOKEN_REFRESH_INTERVAL_MINUTES",
            max(1, ACCESS_TOKEN_EXPIRE_MINUTES - 5),
        )
    )
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
    USER_OTP_RESET_TOKEN_EXPIRE_HOURS = int(os.getenv("USER_OTP_RESET_TOKEN_EXPIRE_HOURS", 1))
    SUPPORT_OTP_RESET_TOKEN_EXPIRE_HOURS = int(os.getenv("SUPPORT_OTP_RESET_TOKEN_EXPIRE_HOURS", 24))
    EMAIL_CHANGE_TOKEN_EXPIRE_HOURS = int(os.getenv("EMAIL_CHANGE_TOKEN_EXPIRE_HOURS", 1))
    SUPPORT_EMAIL_CHANGE_TOKEN_EXPIRE_HOURS = int(os.getenv("SUPPORT_EMAIL_CHANGE_TOKEN_EXPIRE_HOURS", 24))

    # Login Security
    MAX_UNSUCCESSFUL_LOGINS = int(os.getenv("MAX_UNSUCCESSFUL_LOGINS", 5))
    GRACE_PERIOD_MINUTES_3_ATTEMPTS = int(
        os.getenv("GRACE_PERIOD_MINUTES_3_ATTEMPTS", 5)
    )
    GRACE_PERIOD_MINUTES_5_ATTEMPTS = int(
        os.getenv("GRACE_PERIOD_MINUTES_5_ATTEMPTS", 10)
    )

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
    # Extract hostname for allowed hosts (remove protocol and trailing slash)
    _frontend_host = re.sub(r"^https?://", "", FRONTEND_URL).split("/")[0]
    FRONTEND_HOST = os.getenv("FRONTEND_HOST", _frontend_host)
    API_TERMS_OF_SERVICE_URL = os.getenv(
        "API_TERMS_OF_SERVICE_URL",
        f"{FRONTEND_URL.rstrip('/')}/terms-of-service",
    )

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

    # Pages API default limit (for /pages endpoint)
    PAGES_LIST_DEFAULT_LIMIT = int(os.getenv("PAGES_LIST_DEFAULT_LIMIT", 100))

    # Feature Flags (can be enabled/disabled via environment variables)
    FEATURE_OTP_ENABLED = os.getenv("FEATURE_OTP_ENABLED", "true").lower() == "true"
    FEATURE_EMAIL_VERIFICATION_ENABLED = os.getenv("FEATURE_EMAIL_VERIFICATION_ENABLED", "true").lower() == "true"
    FEATURE_CORPORATE_APPROVALS_ENABLED = os.getenv("FEATURE_CORPORATE_APPROVALS_ENABLED", "true").lower() == "true"
    CLOSED_REGISTRATION = os.getenv("CLOSED_REGISTRATION", "false").lower() == "true"
    PUBLIC_USE = os.getenv("PUBLIC_USE", "false").lower() == "true"

    # File Upload Configuration
    _DEFAULT_UPLOAD_DIRECTORY = Path(__file__).parent / "uploads"
    UPLOAD_DIRECTORY = Path(os.getenv("UPLOAD_DIRECTORY", str(_DEFAULT_UPLOAD_DIRECTORY))).resolve()
    MAX_UPLOAD_SIZE = int(os.getenv("MAX_UPLOAD_SIZE", 50 * 1024 * 1024))  # 50MB default
    ALLOWED_FILE_EXTENSIONS = [".pdf"]
    WATERMARK_IMAGE_PATH = os.getenv("WATERMARK_IMAGE_PATH", "")
    WATERMARK_COPYRIGHT = os.getenv("WATERMARK_COPYRIGHT", "")

    # QR Code logo (optional, embedded centred at 72�72 px)
    QR_CODE_LOGO_PATH = os.getenv("QR_CODE_LOGO_PATH", "")

    # OCR pipeline configuration
    OCR_PIPELINE_ENABLED = os.getenv("OCR_PIPELINE_ENABLED", "true").lower() == "true"
    OCR_PIPELINE_REQUIRED = os.getenv("OCR_PIPELINE_REQUIRED", "false").lower() == "true"
    OCR_PIPELINE_ASYNC = os.getenv("OCR_PIPELINE_ASYNC", "true").lower() == "true"
    OCR_PIPELINE_MAX_WORKERS = int(os.getenv("OCR_PIPELINE_MAX_WORKERS", 1))
    OCR_LANGUAGES = os.getenv("OCR_LANGUAGES", "deu+deu_latf+eng")
    OCR_DPI = int(os.getenv("OCR_DPI", 300))
    OCR_OPTIMIZE = int(os.getenv("OCR_OPTIMIZE", 0))
    GS_BIN = os.getenv("GS_BIN", "gswin64c" if os.name == "nt" else "gs")
    TESSERACT_BIN = os.getenv("TESSERACT_BIN", "tesseract")
    OCRMY_PDF_BIN = os.getenv("OCRMY_PDF_BIN", "ocrmypdf")
    UNPAPER_BIN = os.getenv("UNPAPER_BIN", "unpaper")
    KRAKEN_BIN = os.getenv("KRAKEN_BIN", "kraken")
    KRAKEN_ENABLED = os.getenv("KRAKEN_ENABLED", "true").lower() == "true"
    KRAKEN_MIN_HANDWRITING_PAGES = int(os.getenv("KRAKEN_MIN_HANDWRITING_PAGES", 1))
    KRAKEN_MIN_HANDWRITING_RATIO = float(os.getenv("KRAKEN_MIN_HANDWRITING_RATIO", 0.5))
    OCR_PAGE_NUMBER_PRIORITY = os.getenv("OCR_PAGE_NUMBER_PRIORITY", "book,stamp")

    # Legal Content (HTML files are language-specific and loaded from filesystem)
    _DEFAULT_LEGAL_CONTENT_DIRECTORY = Path(__file__).parent / "legal_content"
    LEGAL_CONTENT_DIRECTORY = Path(
        os.getenv("LEGAL_CONTENT_DIRECTORY", str(_DEFAULT_LEGAL_CONTENT_DIRECTORY))
    ).resolve()
    LEGAL_IMPRINT_FILENAME_TEMPLATE = os.getenv(
        "LEGAL_IMPRINT_FILENAME_TEMPLATE",
        "imprint.{lang}.html",
    )
    LEGAL_DATA_PROTECTION_FILENAME_TEMPLATE = os.getenv(
        "LEGAL_DATA_PROTECTION_FILENAME_TEMPLATE",
        "data-protection.{lang}.html",
    )
    LEGAL_TERMS_OF_SERVICE_FILENAME_TEMPLATE = os.getenv(
        "LEGAL_TERMS_OF_SERVICE_FILENAME_TEMPLATE",
        "terms-of-service.{lang}.html",
    )

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
    def get_qr_code_logo_path(cls) -> Optional[Path]:
        """Return configured QR code logo path (or None when not set)."""
        value = (cls.QR_CODE_LOGO_PATH or "").strip()
        if not value:
            return None

        image_path = Path(value)
        if not image_path.is_absolute():
            image_path = (Path(__file__).parent / image_path).resolve()
        return image_path

    @classmethod
    def get_ocrmypdf_binary(cls) -> Optional[str]:
        """Return OCRmyPDF binary path if available."""
        value = (cls.OCRMY_PDF_BIN or "ocrmypdf").strip()
        return shutil.which(value) or (value if Path(value).exists() else None)

    @classmethod
    def get_tesseract_binary(cls) -> Optional[str]:
        """Return tesseract binary path if available."""
        value = (cls.TESSERACT_BIN or "tesseract").strip()
        return shutil.which(value) or (value if Path(value).exists() else None)

    @classmethod
    def get_ghostscript_binary(cls) -> Optional[str]:
        """Return Ghostscript binary path if available."""
        configured = (cls.GS_BIN or ("gswin64c" if os.name == "nt" else "gs")).strip()
        candidates = [configured]

        if os.name == "nt":
            for fallback in ["gswin64c", "gswin32c", "gs"]:
                if fallback not in candidates:
                    candidates.append(fallback)

        for value in candidates:
            resolved = shutil.which(value)
            if resolved:
                return resolved
            if Path(value).exists():
                return value

        return None

    @classmethod
    def get_unpaper_binary(cls) -> Optional[str]:
        """Return unpaper binary path if available."""
        value = (cls.UNPAPER_BIN or "unpaper").strip()
        return shutil.which(value) or (value if Path(value).exists() else None)

    @classmethod
    def get_kraken_binary(cls) -> Optional[str]:
        """Return Kraken binary path if available."""
        value = (cls.KRAKEN_BIN or "kraken").strip()
        return shutil.which(value) or (value if Path(value).exists() else None)
    
    @classmethod
    def ensure_upload_directory(cls):
        """Ensure upload directory exists"""
        cls.UPLOAD_DIRECTORY.mkdir(parents=True, exist_ok=True)

    @classmethod
    def get_grace_period_minutes_for_attempts(cls, unsuccessful_logins: int) -> int:
        """Return configured grace period based on fixed thresholds of 3 and 5 failed logins."""
        if unsuccessful_logins >= 5:
            return cls.GRACE_PERIOD_MINUTES_5_ATTEMPTS
        if unsuccessful_logins >= 3:
            return cls.GRACE_PERIOD_MINUTES_3_ATTEMPTS
        return 0

    @classmethod
    def get_legal_file_path(cls, document_type: str, language: str) -> Path:
        """Build absolute path for a language-specific legal HTML file."""
        normalized_lang = (
            language if language in cls.AVAILABLE_LANGUAGES else cls.DEFAULT_LANGUAGE
        )
        templates = {
            "imprint": cls.LEGAL_IMPRINT_FILENAME_TEMPLATE,
            "data-protection": cls.LEGAL_DATA_PROTECTION_FILENAME_TEMPLATE,
            "terms-of-service": cls.LEGAL_TERMS_OF_SERVICE_FILENAME_TEMPLATE,
        }
        if document_type not in templates:
            raise ValueError(f"Unsupported legal document type: {document_type}")

        filename = templates[document_type].format(lang=normalized_lang)
        return (cls.LEGAL_CONTENT_DIRECTORY / filename).resolve()

    @classmethod
    def resolve_legal_file_path(cls, document_type: str, language: str) -> Path:
        """Resolve legal file path with fallbacks.

        Fallback order:
        1) requested language
        2) default language
        3) language-agnostic filename (e.g., data-protection.html)
        """
        normalized_lang = (
            language if language in cls.AVAILABLE_LANGUAGES else cls.DEFAULT_LANGUAGE
        )

        templates = {
            "imprint": cls.LEGAL_IMPRINT_FILENAME_TEMPLATE,
            "data-protection": cls.LEGAL_DATA_PROTECTION_FILENAME_TEMPLATE,
            "terms-of-service": cls.LEGAL_TERMS_OF_SERVICE_FILENAME_TEMPLATE,
        }
        if document_type not in templates:
            raise ValueError(f"Unsupported legal document type: {document_type}")

        template = templates[document_type]
        candidate_filenames = [template.format(lang=normalized_lang)]

        default_lang = cls.DEFAULT_LANGUAGE
        if default_lang != normalized_lang:
            candidate_filenames.append(template.format(lang=default_lang))

        if "{lang}" in template:
            language_agnostic = (
                template.replace(".{lang}", "")
                .replace("{lang}.", "")
                .replace("{lang}", "")
            )
            candidate_filenames.append(language_agnostic)

        # Keep order, remove duplicates.
        unique_candidates = list(dict.fromkeys(candidate_filenames))

        for filename in unique_candidates:
            candidate_path = (cls.LEGAL_CONTENT_DIRECTORY / filename).resolve()
            if candidate_path.exists() and candidate_path.is_file():
                return candidate_path

        # Return primary candidate for consistent error messaging by caller.
        return (cls.LEGAL_CONTENT_DIRECTORY / unique_candidates[0]).resolve()


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
