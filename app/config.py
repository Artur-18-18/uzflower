"""
Конфигурация приложения UzFlower.
Вынесена для возможности переопределения в тестах.
"""
import os


class Settings:
    """Настройки приложения."""
    
    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "sqlite:///./uzflower.db"
    )
    
    # Security
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY",
        "uzflower-super-secret-key-2026"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 43200  # 30 дней
    
    # Payment
    CLICK_SERVICE_ID: str = os.getenv("CLICK_SERVICE_ID", "YOUR_CLICK_SERVICE_ID")
    CLICK_MERCHANT_ID: str = os.getenv("CLICK_MERCHANT_ID", "YOUR_CLICK_MERCHANT_ID")
    CLICK_SECRET_KEY: str = os.getenv("CLICK_SECRET_KEY", "YOUR_CLICK_SECRET_KEY")
    
    PAYME_MERCHANT_ID: str = os.getenv("PAYME_MERCHANT_ID", "YOUR_PAYME_MERCHANT_ID")
    PAYME_SECRET_KEY: str = os.getenv("PAYME_SECRET_KEY", "YOUR_PAYME_SECRET_KEY")
    
    # Flags
    is_test: bool = DATABASE_URL == "sqlite:///:memory:"


settings = Settings()
