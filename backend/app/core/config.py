"""Configuração da aplicação via variáveis de ambiente."""
from typing import List, Optional

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Settings carregadas de env e .env."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ─── Aplicação ────────────────────────────────────────────────────────────
    PROJECT_NAME: str = "IBMI - Agenda Igrejas"
    VERSION: str = "0.1.0"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # ─── Banco de Dados ───────────────────────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://ibmi:ibmi@db:5432/ibmi"

    # Override para uso local fora do Docker (host=localhost).
    # Quando definida, tem prioridade sobre DATABASE_URL.
    ALEMBIC_DATABASE_URL: Optional[str] = None

    # Preenchida automaticamente pelo validator — use esta no engine.
    EFFECTIVE_DATABASE_URL: str = ""

    # ─── Segurança ────────────────────────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ─── CORS ─────────────────────────────────────────────────────────────────
    ALLOWED_ORIGINS: List[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    @model_validator(mode="after")
    def resolve_database_url(self) -> "Settings":
        """
        Resolve a URL efetiva do banco após todos os campos serem carregados.

        Prioridade:
          1. ALEMBIC_DATABASE_URL — uso local fora do Docker
          2. DATABASE_URL — padrão (host=db, dentro do Docker)
        """
        self.EFFECTIVE_DATABASE_URL = self.ALEMBIC_DATABASE_URL or self.DATABASE_URL
        return self


def get_settings() -> Settings:
    return Settings()