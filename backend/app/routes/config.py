"""
Configuration Routes
"""

from fastapi import APIRouter
from fastapi import Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import User
from config import config

router = APIRouter(prefix="/config", tags=["configuration"])


@router.get("")
async def get_app_config(db: Session = Depends(get_db)):
    """
    Get application configuration.
    
    Returns public application configuration including app metadata,
    feature flags, and UI settings. Safe to expose to frontend.
    """
    user_count = db.query(User).count()
    closed_registration_effective = config.CLOSED_REGISTRATION and user_count > 0

    return {
        "appName": config.APP_NAME,
        "appVersion": config.APP_VERSION,
        "companyName": config.COMPANY_NAME,
        "logoUrl": config.LOGO_URL,
        "copyrightYear": config.COPYRIGHT_YEAR,
        # UI Configuration
        "itemsPerPageDefault": config.ITEMS_PER_PAGE_DEFAULT,
        "itemsPerPageOptions": config.ITEMS_PER_PAGE_OPTIONS,
        # Security Configuration
        "tokenRefreshIntervalMinutes": config.TOKEN_REFRESH_INTERVAL_MINUTES,
        "sessionTimeoutMinutes": config.SESSION_TIMEOUT_MINUTES,
        # Feature Flags
        "features": {
            "otp": config.FEATURE_OTP_ENABLED,
            "emailVerification": config.FEATURE_EMAIL_VERIFICATION_ENABLED,
            "corporateApprovals": config.FEATURE_CORPORATE_APPROVALS_ENABLED,
            "closedRegistration": closed_registration_effective,
            "closedRegistrationConfigured": config.CLOSED_REGISTRATION,
            "publicUse": config.PUBLIC_USE,
        },
        # Languages
        "languages": {
            "en": "English",
            "de": "Deutsch",
        },
        "defaultLanguage": config.DEFAULT_LANGUAGE,
        "legalContent": {
            "imprintUrl": "/api/v1/config/legal/imprint",
            "dataProtectionUrl": "/api/v1/config/legal/data-protection",
            "termsOfServiceUrl": "/api/v1/config/legal/terms-of-service",
        },
        # Custom: Link for pers_count
        "recordsPersCountLink": config.RECORDS_PERS_COUNT_LINK,
    }
