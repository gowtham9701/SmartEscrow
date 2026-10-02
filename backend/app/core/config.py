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

    # Stripe Connect Sandbox (USD fiat escrow rails — NOT crypto)
    STRIPE_API_KEY: str = "sk_test_placeholder"
    STRIPE_WEBHOOK_SECRET: str = "whsec_placeholder"

    # Plaid Sandbox (bank account linking / ACH verification)
    PLAID_CLIENT_ID: str = "plaid_placeholder"
    PLAID_SECRET: str = "plaid_placeholder"
    PLAID_ENV: str = "sandbox"

    # GitHub (AI verification engine + webhook merge-event triggers)
    GITHUB_WEBHOOK_SECRET: str = "change-me"
    GITHUB_APP_TOKEN: str = ""

    # Ollama (local LLM orchestration on Apple Silicon, zero cloud cost)
    OLLAMA_HOST: str = "http://localhost:11434"
    OLLAMA_MODEL: str = "deepseek-coder:6.7b"

    # Fiat-Staking Integrity Model
    INTEGRITY_STAKE_USD_CENTS: int = 2500  # $25.00 refundable stake


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
