"""
Configuration & Settings
========================
Pydantic-Settings model loaded from environment variables / .env file.
"""
from __future__ import annotations

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Mock / Demo ──────────────────────────────────────────────────────────
    mock_mode: bool = Field(default=True, description="Run pipeline with synthetic data, no external keys needed.")

    # ── Gemini AI ────────────────────────────────────────────────────────────
    gemini_api_key: str = Field(default="", description="Google Gemini API key from AI Studio.")
    gemini_model: str = Field(default="gemini-3.8-flash", description="Gemini model identifier.")

    # ── Concurrency & Rate Limiting ───────────────────────────────────────────
    concurrency_limit: int = Field(default=5, ge=1, le=50)
    rate_limit_rps: float = Field(default=2.0, gt=0)
    request_timeout: int = Field(default=15, ge=5, le=120)

    # ── Dispatchers ──────────────────────────────────────────────────────────
    crm_webhook_url: str = Field(default="", description="GoHighLevel / HubSpot / Zapier webhook endpoint.")
    slack_webhook_url: str = Field(default="", description="Slack Incoming Webhook URL.")
    discord_webhook_url: str = Field(default="", description="Discord Webhook URL.")

    # ── Export ────────────────────────────────────────────────────────────────
    output_dir: str = Field(default="./output")
    log_level: str = Field(default="INFO")

    @property
    def ai_enabled(self) -> bool:
        """True when a real Gemini API key is configured."""
        return bool(self.gemini_api_key) and not self.mock_mode

    @field_validator("log_level")
    @classmethod
    def uppercase_log_level(cls, v: str) -> str:
        return v.upper()


# Singleton instance – import this across the codebase
settings = Settings()
