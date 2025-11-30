import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings that vary by environment"""

    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")  # development, staging, production

    # Security
    SECRET_KEY = os.getenv("SECRET_KEY")
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")

    # Database
    DB_URL = os.getenv("DB_URL")

    # Twilio
    TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

    # Feature Flags
    SEED_DATABASE = os.getenv("SEED_DATABASE", "false").lower() == "true"
    ENABLE_SMS = os.getenv("ENABLE_SMS", "true").lower() == "true"

    # Auth bypass (ONLY for local development with fake data)
    DISABLE_AUTH = os.getenv("DISABLE_AUTH", "false").lower() == "true"

    @classmethod
    def is_production(cls) -> bool:
        return cls.ENVIRONMENT == "production"

    @classmethod
    def is_development(cls) -> bool:
        return cls.ENVIRONMENT == "development"

    @classmethod
    def validate(cls):
        """Validate critical settings before app starts"""
        errors = []

        if not cls.SECRET_KEY:
            errors.append("SECRET_KEY is required")

        if not cls.DB_URL:
            errors.append("DB_URL is required")

        # In production, certain things MUST be set
        if cls.is_production():
            if cls.DISABLE_AUTH:
                errors.append("DISABLE_AUTH cannot be true in production!")

            if cls.SEED_DATABASE:
                errors.append("SEED_DATABASE cannot be true in production!")

            if not cls.STRIPE_SECRET_KEY:
                errors.append("STRIPE_SECRET_KEY is required in production")

            if not cls.TWILIO_ACCOUNT_SID or not cls.TWILIO_AUTH_TOKEN:
                errors.append("Twilio credentials are required in production")

        if errors:
            raise ValueError(f"Configuration errors:\n" + "\n".join(f"  - {e}" for e in errors))

        return True


# Validate on import
settings = Settings()