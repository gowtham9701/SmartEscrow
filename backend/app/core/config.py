"""
Central application configuration.
Loaded entirely from environment variables (.env) — zero hardcoded secrets.
"""
from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_NAME: str = "SmartEscrow"
    ENV: str = "local"
    API_V1_PREFIX: str = "/api/v1"

    # Database (local PostgreSQL, zero-cost, no cloud dependency)
    DATABASE_URL: str = "postgresql+asyncpg://smartescrow:smartescrow@localhost:5432/smartescrow"

    # Auth
    JWT_SECRET_KEY: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    # Razorpay India payment gateway (fiat settlement in INR)
    RAZORPAY_KEY_ID: str = "rzp_test_placeholder"
    RAZORPAY_KEY_SECRET: str = "placeholder_secret"
    RAZORPAY_WEBHOOK_SECRET: str = "whsec_placeholder"
    PAYMENT_CURRENCY: str = "INR"

    # Zero-cost local prototype uses the mock provider by default.
    # Switch to a sandbox provider later if you want simulated external payments.
    PAYMENT_PROVIDER: str = "mock"

    # GitHub (AI verification engine + webhook merge-event triggers)
    GITHUB_WEBHOOK_SECRET: str = "change-me"
    GITHUB_APP_TOKEN: str = ""

    # Ollama (local LLM orchestration on Apple Silicon, zero cloud cost)
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "deepseek-coder:6.7b"

    # Fiat-Staking Integrity Model
    INTEGRITY_STAKE_INR_PAISA: int = 2500  # ₹25.00 refundable stake (2,500 paise)


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
